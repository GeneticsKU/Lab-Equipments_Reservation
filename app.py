import streamlit as st
import pandas as pd
import datetime
import plotly.express as px
import json
from dataclasses import asdict
from io import StringIO
import os, time
import subprocess
from functools import lru_cache

from bridge.bootstrap import (
    build_auth_store,
    clear_bridge_session_state,
    ensure_bridge_schema_once,
    hydrate_bridge_session_state,
    load_app_settings,
    should_retry_cookie_restore,
)
from bridge.github_backup import build_push_refspec, build_repo_url, resolve_github_backup_settings
from bridge.session_cookie import clear_session_cookie, get_session_cookie, set_session_cookie
from bridge.reservation_store import (
    BridgeReservationStore,
    PCR_FILE_PATH as BRIDGE_PCR_FILE_PATH,
    NON_PCR_FILE_PATH as BRIDGE_NON_PCR_FILE_PATH,
    reservation_type_for_file_path,
)
from bridge.ui_access_requests import (
    get_approval_request_id,
    render_applicant_pending_access,
    render_sponsor_request_history,
)
from bridge.ui_auth import render_bridge_login, render_deployment_banner

st.set_page_config(layout="wide")

# Set the timezone
os.environ['TZ'] = 'Asia/Bangkok'
time.tzset()

# Constants
PCR_FILE_PATH = BRIDGE_PCR_FILE_PATH
NON_PCR_FILE_PATH = BRIDGE_NON_PCR_FILE_PATH
ANNOUNCEMENT_FILE_PATH = 'announcement.txt'
AUTOCLAVES_PATH = 'autoclaves_count.csv'
LOG_FILE_PATH = "change_log.csv"
EQUIPMENT_DETAILS_FILE_PATH = 'equipment_details.json'

def use_bridge_reservation_store(file_path: str) -> bool:
    if reservation_type_for_file_path(file_path) is None:
        return False
    return reservation_storage_mode() in {"postgres", "db", "database", "neon"} and load_app_settings() is not None


def reservation_storage_mode() -> str:
    try:
        configured_mode = st.secrets.get("RESERVATION_STORAGE_MODE")
    except Exception:
        configured_mode = None
    return str(configured_mode or os.getenv("RESERVATION_STORAGE_MODE", "csv")).strip().lower()


def build_bridge_reservation_store() -> BridgeReservationStore:
    settings = load_app_settings()
    if settings is None:
        raise RuntimeError("Bridge settings are required for DB-backed reservations.")
    return _build_bridge_reservation_store_cached(settings.database_url)


@lru_cache(maxsize=8)
def _build_bridge_reservation_store_cached(database_url: str) -> BridgeReservationStore:
    settings = load_app_settings()
    if settings is None:
        raise RuntimeError("Bridge settings are required for DB-backed reservations.")
    ensure_bridge_schema_once(settings)
    return BridgeReservationStore(settings)

# Initialize files if they don't exist
def init_file(file_path, columns=None):
    if use_bridge_reservation_store(file_path):
        return
    if not os.path.exists(file_path):
        df = pd.DataFrame(columns=columns) if columns else pd.DataFrame()
        df.to_csv(file_path, index=False)

def init_announcement_file():
    if not os.path.exists(ANNOUNCEMENT_FILE_PATH):
        with open(ANNOUNCEMENT_FILE_PATH, 'w') as f:
            f.write('')

# Call initialization functions
init_file(PCR_FILE_PATH, ['Name', 'Room', 'Equipments', 'Start_Time', 'End_Time'])
init_file(NON_PCR_FILE_PATH, ['Name', 'Room', 'Equipments', 'Start_Time', 'End_Time'])
init_file(AUTOCLAVES_PATH, ['Counts'])
init_announcement_file()

# Read the announcement from the text file
def read_announcement():
    if os.path.exists(ANNOUNCEMENT_FILE_PATH):
        with open(ANNOUNCEMENT_FILE_PATH, 'r') as f:
            announcement = f.read().strip()
        return announcement
    return ''

# Update the announcement in the text file
def update_announcement(text, file_path=ANNOUNCEMENT_FILE_PATH):
    try:
        with open(file_path, 'w') as file:
            file.write(text)
        backup_to_github(file_path, commit_message="Update announcements")
    except Exception as e:
        st.error(f"Error saving announcement: {e}")

# Load data from CSV
def load_data(file_path):
    try:
        reservation_type = reservation_type_for_file_path(file_path)
        if reservation_type and use_bridge_reservation_store(file_path):
            return build_bridge_reservation_store().load_dataframe(reservation_type)
        if os.path.exists(file_path):
            return pd.read_csv(file_path)
        return pd.DataFrame(columns=['Equipments', 'Start_Time', 'End_Time', 'Name'])
    except Exception as e:
        st.error(f"Error reading data from file {file_path}: {e}")
        return pd.DataFrame()


# Save data to CSV
def save_data(df, file_path):
    try:
        reservation_type = reservation_type_for_file_path(file_path)
        if reservation_type and use_bridge_reservation_store(file_path):
            build_bridge_reservation_store().save_dataframe(reservation_type, df)
            return
        df.to_csv(file_path, index=False)
        backup_to_github(file_path, commit_message=f"Update {os.path.basename(file_path)}")
    except Exception as e:
        st.error(f"Error saving data: {e}")

def fetch_data(file_path):
    df = load_data(file_path).copy()
    for column in ("Start_Time", "End_Time"):
        if column not in df.columns:
            df[column] = pd.NaT
    df['Start_Time'] = pd.to_datetime(df['Start_Time'], format='%Y/%m/%d %H:%M:%S', errors='coerce')
    df['End_Time'] = pd.to_datetime(df['End_Time'], format='%Y/%m/%d %H:%M:%S', errors='coerce')
    return df

# Configure Git
def configure_git():
    try:
        settings = load_github_backup_settings()
        subprocess.run(["git", "config", "--global", "user.name", settings.username], check=True)
        subprocess.run(["git", "config", "--global", "user.email", settings.email], check=True)
    except subprocess.CalledProcessError as e:
        st.error(f"An error occurred while configuring Git: {e}")


def current_git_branch() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError:
        return None

    branch = result.stdout.strip()
    return None if branch in {"", "HEAD"} else branch


def load_github_backup_settings():
    try:
        github_secrets = st.secrets["github"]
        return resolve_github_backup_settings(github_secrets, current_branch=current_git_branch())
    except KeyError as exc:
        missing_key = exc.args[0]
        raise KeyError(
            "Missing GitHub backup setting. Provide st.secrets['github'] with "
            f"'username', 'email', 'token', and a branch or checked-out branch. Missing: {missing_key}"
        ) from exc


# Backup to GitHub
def backup_to_github(file_path, commit_message="Update data"):
    try:
        configure_git()
        settings = load_github_backup_settings()
        repo_url = build_repo_url(settings)

        # Set the remote URL
        subprocess.run(["git", "remote", "set-url", "origin", repo_url], check=True)

        # Stage the file
        subprocess.run(["git", "add", file_path], check=True)

        staged_diff = subprocess.run(
            ["git", "diff", "--cached", "--quiet", "--", file_path],
            check=False,
        )
        if staged_diff.returncode == 0:
            return

        # Commit the changes
        subprocess.run(["git", "commit", "-m", commit_message], check=True)

        # Push the changes to the configured backup branch explicitly.
        subprocess.run(["git", "push", "origin", build_push_refspec(settings)], check=True)

        # st.success(f"Changes to {file_path} have been backed up to GitHub.")
    except KeyError as e:
        st.error(str(e))
    except subprocess.CalledProcessError as e:
        st.error(f"An error occurred while backing up to GitHub: {e}")

# Load equipment details from JSON
def load_json(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

# Save equipment details to JSON
def save_equipment_details(details, json_file_path=EQUIPMENT_DETAILS_FILE_PATH):
    try:
        with open(json_file_path, 'w') as file:
            json.dump(details, file, indent=4)
        backup_to_github(json_file_path, commit_message="Update equipment details")
    except Exception as e:
        st.error(f"Error saving equipment details: {e}")

# Check if image exists
def image_exists(image_path):
    return os.path.exists(image_path)

# Safely display image
def safe_display_image(image_path, width=100, offset=0):
    if image_exists(image_path):
        cols = st.columns([offset, 1])
        with cols[1]:
            st.image(image_path, width=width)
    else:
        st.error("Image not available.")

# Convert DataFrame to CSV string
def convert_df_to_csv(df):
    output = StringIO()
    df.to_csv(output, index=False)
    return output.getvalue().encode('utf-8')


# Download non-PCR data
def download_non_pcr():
    return convert_df_to_csv(fetch_data(NON_PCR_FILE_PATH))

# Download PCR data
def download_pcr():
    return convert_df_to_csv(fetch_data(PCR_FILE_PATH))

# Generate time slots
def generate_time_slots():
    slots = [{
        "label": f"Slot {i + 1}: {datetime.time(hour=h).strftime('%H:%M')}-{datetime.time(hour=h + 3).strftime('%H:%M')}",
        "start": datetime.time(hour=h), "end": datetime.time(hour=h + 3)}
        for i, h in enumerate(range(8, 20, 3))]
    return slots

slots = generate_time_slots()

# Load equipment details once
def load_equipment_details():
    if 'equipment_details' not in st.session_state:
        st.session_state.equipment_details = load_json(EQUIPMENT_DETAILS_FILE_PATH)

load_equipment_details()

# Log actions
def log_action(action, user, details):
    log_entry = {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "action": action,
        "user": user,
        "details": details
    }

    try:
        if os.path.exists(LOG_FILE_PATH):
            log_df = pd.read_csv(LOG_FILE_PATH)
        else:
            log_df = pd.DataFrame(columns=["timestamp", "action", "user", "details"])

        log_df = pd.concat([log_df, pd.DataFrame([log_entry])], ignore_index=True)
        log_df.to_csv(LOG_FILE_PATH, index=False)
    except Exception as e:
        st.error(f"Error logging action: {e}")

def apply_mobile_style():
    # Mobile style
    st.markdown(
        """
        <style>
        .watermark {
            font-size: 15px;
            text-align: left;
            color: gray;
            margin-top: 3px;
        }
        </style>
        """, unsafe_allow_html=True
    )

    st.markdown(
        '<p class="watermark">Designed by Yanawat Pattharapistthorn and TE Group (2024).</p>',
        unsafe_allow_html=True
    )

    css = '''
        <style>
            /* Style adjustments for tabs */
            .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
                font-size: 2rem;
                margin-right: 25px;
            }
            [data-testid="stMarkdownContainer"] {
                font-size: 25px;
                margin-left: 0px;
            }
            /* Welcome message styles */
            .welcome-message {
                font-size: 28px;
                font-family: Arial;
            }
            /* Light and Dark mode adaptations */
            @media (prefers-color-scheme: dark) {
                .welcome-message {
                    color: #DDD; /* Lighter color for dark mode */
                }
                [data-testid="stMarkdownContainer"] {
                    color: #DDD; /* Adjusting text color for dark mode */
                }
            }
            @media (prefers-color-scheme: light) {
                .welcome-message {
                    color: #333; /* Darker color for light mode */
                }
                [data-testid="stMarkdownContainer"] {
                    color: #333; /* Adjusting text color for light mode */
                }
            }
        </style>
    '''
    st.markdown(css, unsafe_allow_html=True)


def apply_web_style():
    # Web style
    st.markdown(
        """
        <style>
        .watermark {
            font-size: 15px;
            text-align: center;
            color: gray;
            margin-top: 3px;
        }
        </style>
        """, unsafe_allow_html=True
    )

    st.markdown(
        '<p class="watermark">Designed by Yanawat Pattharapistthorn and TE Group (2024).</p>',
        unsafe_allow_html=True
    )

    css = '''
    <style>
        /* Style adjustments for tabs */
        .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
            font-size: 2rem;
            margin-right: 25px;
        }
        [data-testid="stMarkdownContainer"] {
            font-size: 25px;
            margin-left: 0px;
        }
        /* Welcome message styles */
        .welcome-message {
            font-size: 28px;
            font-family: Arial;
        }
        /* Light and Dark mode adaptations */
        @media (prefers-color-scheme: dark) {
            .welcome-message {
                color: #DDD; /* Lighter color for dark mode */
            }
            [data-testid="stMarkdownContainer"] {
                color: #DDD; /* Adjusting text color for dark mode */
            }
        }
        @media (prefers-color-scheme: light) {
            .welcome-message {
                color: #333; /* Darker color for light mode */
            }
            [data-testid="stMarkdownContainer"] {
                color: #333; /* Adjusting text color for light mode */
            }
        }
    </style>
    '''
    st.markdown(css, unsafe_allow_html=True)

# Function to authenticate users
def bridge_role():
    return st.session_state.get("bridge_role", "User")


def init_bridge_state():
    if 'authentication_status' not in st.session_state:
        st.session_state['authentication_status'] = False
    if 'username' not in st.session_state:
        st.session_state['username'] = None
    if 'name' not in st.session_state:
        st.session_state['name'] = None
    if 'bridge_user' not in st.session_state:
        st.session_state['bridge_user'] = None
    if 'bridge_role' not in st.session_state:
        st.session_state['bridge_role'] = None
    if 'bridge_raw_session_token' not in st.session_state:
        st.session_state['bridge_raw_session_token'] = None
    if 'bridge_pending_email' not in st.session_state:
        st.session_state['bridge_pending_email'] = ''


def get_bridge_runtime():
    settings = load_app_settings()
    if settings is None:
        return None, None, "Missing bridge configuration. Set DATABASE_URL, SMTP_USERNAME, SMTP_PASSWORD, SMTP_FROM_EMAIL, and APP_BASE_URL."

    try:
        ensure_bridge_schema_once(settings)
        auth_store = build_auth_store(settings)
        return settings, auth_store, None
    except Exception as exc:
        return None, None, f"Bridge initialization failed: {exc}"


def available_view_dates(days_ahead: int = 60) -> list[str]:
    return [(datetime.date.today() + datetime.timedelta(days=i)).strftime('%Y-%m-%d') for i in range(days_ahead)]


def enabled_equipment_map(room_name: str) -> dict:
    return {
        eq: info
        for eq, info in st.session_state.equipment_details[room_name].items()
        if info.get('enabled', False)
    }


def render_reservation_tables_section(prefix: str, *, title_font_size: int, axis_title_size: int, tick_font_size: int, chart_width: int, margin_top: int) -> None:
    rooms = list(st.session_state.equipment_details.keys())
    dates = available_view_dates()
    room_state_key = f"{prefix}_table_room"
    date_state_key = f"{prefix}_table_date"

    if st.session_state.get(room_state_key) not in rooms:
        st.session_state[room_state_key] = rooms[0]
    if st.session_state.get(date_state_key) not in dates:
        st.session_state[date_state_key] = dates[0]

    room_selection = st.selectbox("### Select a Room", rooms, key=room_state_key)
    selected_date_text = st.selectbox("### View reservations for", dates, key=date_state_key)
    selected_date = datetime.datetime.strptime(selected_date_text, '%Y-%m-%d').date()

    full_day_start = datetime.datetime.combine(selected_date, datetime.time(0, 0))
    full_day_end = datetime.datetime.combine(selected_date, datetime.time(23, 59))
    pcr_start = datetime.datetime.combine(selected_date, datetime.time(8, 0))
    pcr_end = datetime.datetime.combine(selected_date, datetime.time(20, 0))

    df_non_pcr = fetch_data(NON_PCR_FILE_PATH)
    df_non_pcr.dropna(inplace=True)
    df_pcr = fetch_data(PCR_FILE_PATH)
    df_pcr.dropna(inplace=True)

    df_pcr_filtered = df_pcr[(df_pcr['Room'] == room_selection) & (df_pcr['Start_Time'].dt.date == selected_date)]
    df_non_pcr_filtered = df_non_pcr[
        (df_non_pcr['Room'] == room_selection) & (df_non_pcr['Start_Time'].dt.date == selected_date)
    ]

    gantt_df_list_pcr = []
    gantt_df_list_non_pcr = []

    for equipment, details in st.session_state.equipment_details[room_selection].items():
        if details['enabled']:
            is_pcr_equipment = "PCR" in equipment
            equipment_reservations = df_pcr_filtered if is_pcr_equipment else df_non_pcr_filtered
            operational_start = pcr_start if is_pcr_equipment else full_day_start
            operational_end = pcr_end if is_pcr_equipment else full_day_end

            filtered_reservations = equipment_reservations[equipment_reservations['Equipments'] == equipment]
            target_list = gantt_df_list_pcr if is_pcr_equipment else gantt_df_list_non_pcr
            if filtered_reservations.empty:
                target_list.append({
                    'Task': equipment,
                    'Start': operational_end,
                    'Finish': operational_end,
                    'User': 'Available'
                })
            else:
                for _, reservation in filtered_reservations.iterrows():
                    start = max(reservation['Start_Time'], operational_start)
                    end = min(reservation['End_Time'], operational_end)
                    target_list.append({
                        'Task': reservation['Equipments'],
                        'Start': start,
                        'Finish': end,
                        'User': reservation['Name']
                    })

    def render_chart(data_rows: list[dict], *, title: str, x_start: datetime.datetime, x_end: datetime.datetime) -> None:
        if not data_rows:
            return

        gantt_df = pd.DataFrame(data_rows)
        fig = px.timeline(gantt_df, x_start="Start", x_end="Finish", y="Task", color="User", title=title)
        fig.update_xaxes(range=[x_start, x_end], tickformat="%H:%M\n%Y-%m-%d", showgrid=True, gridcolor='LightGrey')
        fig.update_yaxes(showgrid=True, gridcolor='LightGrey')
        fig.update_layout(
            title=dict(
                text=f"Equipments Reservations for {room_selection}",
                font=dict(size=title_font_size),
                x=0,
                y=0.95,
            ),
            xaxis=dict(
                title="Time",
                title_font=dict(size=axis_title_size),
                tickfont=dict(size=tick_font_size),
                showgrid=True,
                gridcolor="LightGrey",
                side="top",
                dtick=7200000,
                tickformat="%H:%M\n%Y-%m-%d"
            ),
            yaxis=dict(
                title="Equipments",
                title_font=dict(size=axis_title_size),
                tickfont=dict(size=tick_font_size),
                showgrid=True,
                gridcolor="LightGrey"
            ),
            margin=dict(t=margin_top),
            height=600,
            width=chart_width
        )
        for trace in fig.data:
            if trace.name == "Available":
                trace.showlegend = False
        st.plotly_chart(fig)

    render_chart(
        gantt_df_list_pcr,
        title=f"PCR Equipments Reservations for {room_selection}",
        x_start=pcr_start,
        x_end=pcr_end,
    )
    render_chart(
        gantt_df_list_non_pcr,
        title=f"Non-PCR Equipments Reservations for {room_selection}",
        x_start=full_day_start,
        x_end=full_day_end,
    )


def render_reservation_form_section(prefix: str, role: str, *, image_width: int) -> None:
    rooms = list(st.session_state.equipment_details.keys())
    equipment_state_key = f"{prefix}_selected_equipment"
    selected_room = st.selectbox("### Select a Room", rooms, key=f"{prefix}_selected_room")
    enabled_equipments = enabled_equipment_map(selected_room)
    if st.session_state.get(equipment_state_key) not in enabled_equipments:
        st.session_state[equipment_state_key] = next(iter(enabled_equipments))
    selected_equipment = st.selectbox("### Select Equipments", list(enabled_equipments.keys()), key=equipment_state_key)

    equipment_info = enabled_equipments[selected_equipment]
    safe_display_image(equipment_info['image'], width=image_width, offset=0.5)
    st.write(f"#### Details : {equipment_info['details']}")

    if "PCR" in selected_equipment:
        st.subheader("Book Your PCR Slot")
        today = datetime.date.today()
        tomorrow = today + datetime.timedelta(days=1)
        current_datetime = datetime.datetime.now()

        with st.form(f"{prefix}_pcr_reservation_form"):
            reservation_date = st.date_input("## Reservation Date", min_value=today, max_value=tomorrow)
            slots = generate_time_slots()
            if reservation_date == today:
                slots = [slot for slot in slots if datetime.datetime.combine(today, slot['end']) > current_datetime]

            selected_slot = None
            if slots:
                available_slots = [slot['label'] for slot in slots]
                selected_slot_label = st.selectbox("## Select a Time Slot", available_slots)
                selected_slot = next((slot for slot in slots if slot['label'] == selected_slot_label), None)
            else:
                st.error("No available slots for the selected day.")

            submit_pcr = st.form_submit_button('### Submit PCR Reservation')

        if submit_pcr:
            if selected_slot is None:
                st.error("No available slot was selected.")
                return

            df_pcr = fetch_data(PCR_FILE_PATH)
            df_pcr.dropna(inplace=True)

            start_datetime = datetime.datetime.combine(reservation_date, selected_slot['start'])
            end_datetime = datetime.datetime.combine(reservation_date, selected_slot['end'])

            df_pcr['Start_Time'] = pd.to_datetime(df_pcr['Start_Time'])
            df_pcr['End_Time'] = pd.to_datetime(df_pcr['End_Time'])

            user_reservations = df_pcr[
                (df_pcr['Name'] == st.session_state["name"]) &
                (df_pcr['Room'] == selected_room) &
                (df_pcr['Equipments'] == selected_equipment) &
                (df_pcr['Start_Time'].dt.date == reservation_date)
            ]

            continuous_slot_booked = any(
                res['End_Time'] == start_datetime or res['Start_Time'] == end_datetime
                for _, res in user_reservations.iterrows()
            )

            overlapping_reservations = df_pcr[
                (df_pcr['Room'] == selected_room) &
                (df_pcr['Equipments'] == selected_equipment) &
                ((df_pcr['Start_Time'] < end_datetime) & (df_pcr['End_Time'] > start_datetime))
            ]

            if not overlapping_reservations.empty:
                st.error("This slot is already booked. Please choose another slot.")
            elif continuous_slot_booked:
                st.error("Cannot book continuous slots. Please select a non-continuous slot.")
            else:
                new_reservation = pd.DataFrame([{
                    'Name': st.session_state["name"],
                    'Room': selected_room,
                    'Equipments': selected_equipment,
                    'Start_Time': start_datetime,
                    'End_Time': end_datetime
                }])
                df_pcr_buffer = pd.concat([df_pcr, new_reservation], ignore_index=True)
                df_pcr_buffer.reset_index(drop=True, inplace=True)
                df_pcr_buffer['Start_Time'] = df_pcr_buffer['Start_Time'].dt.strftime('%Y/%m/%d %H:%M:%S')
                df_pcr_buffer['End_Time'] = df_pcr_buffer['End_Time'].dt.strftime('%Y/%m/%d %H:%M:%S')
                save_data(df_pcr_buffer, PCR_FILE_PATH)
                log_action("Add Reservation", st.session_state["name"], new_reservation)
                st.success(
                    f"Reservation successful for {selected_equipment} from {start_datetime.strftime('%Y/%m/%d %H:%M:%S')} to {end_datetime.strftime('%Y/%m/%d %H:%M:%S')}"
                )
    else:
        st.subheader(f"Reserve {selected_equipment}")
        max_days_advance = 60 if role in ["Admins", "Lecturer"] else 30
        if "Autoclave" in selected_equipment:
            max_days_advance = min(max_days_advance, 1)

        max_date = datetime.date.today() + datetime.timedelta(days=max_days_advance)
        current_time = datetime.datetime.now()

        with st.form(f"{prefix}_non_pcr_reservation_form"):
            start_date = st.date_input("## Start Date", min_value=datetime.date.today(), max_value=max_date)
            start_time = st.time_input("## Start Time", value=None)
            end_time = st.time_input("## End Time", value=None)
            submit_non_pcr = st.form_submit_button("### Submit Reservation")

        if submit_non_pcr:
            if not start_time or not end_time:
                st.error("Please select both a start time and an end time.")
                return

            start_datetime = datetime.datetime.combine(start_date, start_time)
            end_datetime = datetime.datetime.combine(start_date, end_time)
            df_non_pcr = fetch_data(NON_PCR_FILE_PATH)
            df_non_pcr.dropna(inplace=True)

            if start_datetime < current_time:
                st.error("Cannot book a reservation in the past. Please select a future time.")
            elif start_datetime >= end_datetime:
                st.error("The start time must be before the end time. Please adjust your selection.")
            else:
                overlapping_reservations = df_non_pcr[
                    (df_non_pcr['Room'] == selected_room) &
                    (df_non_pcr['Equipments'] == selected_equipment) &
                    ((df_non_pcr['Start_Time'] < end_datetime) & (df_non_pcr['End_Time'] > start_datetime))
                ]

                if not overlapping_reservations.empty:
                    st.error("This time slot is already reserved. Please choose another time.")
                else:
                    new_reservation = {
                        'Name': st.session_state["name"],
                        'Room': selected_room,
                        'Equipments': selected_equipment,
                        'Start_Time': start_datetime,
                        'End_Time': end_datetime
                    }
                    new_reservation_df = pd.DataFrame([new_reservation])
                    df_non_pcr_buffer = pd.concat([df_non_pcr, new_reservation_df], ignore_index=True)
                    df_non_pcr_buffer.reset_index(drop=True, inplace=True)
                    df_non_pcr_buffer['Start_Time'] = df_non_pcr_buffer['Start_Time'].dt.strftime('%Y/%m/%d %H:%M:%S')
                    df_non_pcr_buffer['End_Time'] = df_non_pcr_buffer['End_Time'].dt.strftime('%Y/%m/%d %H:%M:%S')
                    save_data(df_non_pcr_buffer, NON_PCR_FILE_PATH)
                    log_action("Add Reservation", st.session_state["name"], new_reservation)
                    st.success(
                        f"Reservation successful for {selected_equipment} in {selected_room} from {start_datetime.strftime('%Y/%m/%d %H:%M:%S')} to {end_datetime.strftime('%Y/%m/%d %H:%M:%S')}"
                    )


def render_reservation_cancellation_section(prefix: str) -> None:
    df_non_pcr = fetch_data(NON_PCR_FILE_PATH)
    df_non_pcr.dropna(inplace=True)
    df_pcr = fetch_data(PCR_FILE_PATH)
    df_pcr.dropna(inplace=True)

    user_reservations_pcr = df_pcr[df_pcr['Name'] == st.session_state["name"]]
    user_reservations_non_pcr = df_non_pcr[df_non_pcr['Name'] == st.session_state["name"]]
    user_reservations = pd.concat([user_reservations_pcr, user_reservations_non_pcr])

    current_datetime = datetime.datetime.now()
    today = datetime.date.today()
    max_date_60 = today + datetime.timedelta(days=60)

    user_reservations = user_reservations[
        ((user_reservations['Start_Time'].dt.date == today) |
         ((user_reservations['Start_Time'].dt.date > today) &
          (user_reservations['Start_Time'] > current_datetime)))
        & (user_reservations['Start_Time'].dt.date <= max_date_60)
    ]

    if user_reservations.empty:
        st.write("## You have no reservations.")
        return

    with st.form(f"{prefix}_cancel_reservation_form"):
        selected_reservation_index = st.selectbox(
            "## Your Reservations:",
            options=range(len(user_reservations)),
            format_func=lambda x: f"{user_reservations.iloc[x]['Equipments']} on " +
                                  (user_reservations.iloc[x]['Start_Time'].strftime('%Y/%m/%d %H:%M:%S') +
                                   ' To ' +
                                   user_reservations.iloc[x]['End_Time'].strftime('%Y/%m/%d %H:%M:%S')
                                   if pd.notnull(user_reservations.iloc[x]['Start_Time']) else "Date not available"),
        )
        cancel_reservation = st.form_submit_button("### Cancel Reservation")

    if cancel_reservation:
        reservation_to_cancel = user_reservations.iloc[selected_reservation_index]
        if "PCR" in reservation_to_cancel['Equipments']:
            df_pcr.drop(index=reservation_to_cancel.name, inplace=True)
            df_pcr['Start_Time'] = df_pcr['Start_Time'].dt.strftime('%Y/%m/%d %H:%M:%S')
            df_pcr['End_Time'] = df_pcr['End_Time'].dt.strftime('%Y/%m/%d %H:%M:%S')
            log_action("Delete Reservation", st.session_state["name"], f"Details: {user_reservations.iloc[selected_reservation_index]}")
            save_data(df_pcr, PCR_FILE_PATH)
        else:
            df_non_pcr.drop(index=reservation_to_cancel.name, inplace=True)
            df_non_pcr['Start_Time'] = df_non_pcr['Start_Time'].dt.strftime('%Y/%m/%d %H:%M:%S')
            df_non_pcr['End_Time'] = df_non_pcr['End_Time'].dt.strftime('%Y/%m/%d %H:%M:%S')
            log_action("Delete Reservation", st.session_state["name"], f"Details: {user_reservations.iloc[selected_reservation_index]}")
            save_data(df_non_pcr, NON_PCR_FILE_PATH)

        st.success("Reservation canceled successfully.")


def bridge_json_default(value):
    if isinstance(value, (datetime.datetime, datetime.date)):
        return value.isoformat()
    return str(value)


def render_bridge_status_panel(auth_store, bridge_user) -> None:
    if not bridge_user.is_admin:
        st.info("Bridge status is available to admins only.")
        return

    st.subheader("Bridge Status")
    st.caption("Pilot monitoring for login, approval, and current reservation storage.")
    st.info("Reservation storage mode: CSV files. Neon is used only for identity, sessions, and approval state.")

    try:
        users = auth_store.list_users()
        access_requests = auth_store.list_all_access_requests()
    except Exception as exc:
        st.error(f"Unable to load bridge status: {exc}")
        return

    pending_requests = [request for request in access_requests if request["status"] == "Pending"]
    approved_users = [user for user in users if user.approval_state == "approved"]
    pending_users = [user for user in users if user.approval_state == "pending"]
    sponsors = [user for user in users if user.is_sponsor or user.is_admin]

    metric_cols = st.columns(4)
    metric_cols[0].metric("Pending requests", len(pending_requests))
    metric_cols[1].metric("Approved users", len(approved_users))
    metric_cols[2].metric("Pending users", len(pending_users))
    metric_cols[3].metric("Sponsors/admins", len(sponsors))

    if pending_requests:
        st.write("### Pending approval queue")
        pending_rows = []
        for request in pending_requests:
            applicant = auth_store.repository.get_user_by_id(request["applicant_user_id"])
            sponsor = auth_store.repository.get_user_by_id(request["chosen_sponsor_user_id"])
            pending_rows.append(
                {
                    "Applicant": applicant.full_name or applicant.email if applicant else "Unknown",
                    "Email": applicant.email if applicant else "",
                    "Sponsor/Admin reviewer": sponsor.full_name or sponsor.email if sponsor else "Unknown",
                    "Suggested category": request["suggested_user_category"],
                    "Affiliation": request["affiliation"],
                    "Requested at": request["created_at"],
                }
            )
        st.dataframe(pd.DataFrame(pending_rows), use_container_width=True)
    else:
        st.success("No pending access requests.")

    with st.expander("Approved bridge users"):
        user_rows = [
            {
                "Name": user.full_name or "",
                "Email": user.email,
                "Category": user.user_category or "",
                "Affiliation": user.affiliation or "",
                "Sponsor": user.is_sponsor,
                "Admin": user.is_admin,
                "Email verified": user.is_email_verified,
            }
            for user in approved_users
        ]
        st.dataframe(pd.DataFrame(user_rows), use_container_width=True)

    snapshot = {
        "generated_at": datetime.datetime.now(datetime.timezone.utc),
        "reservation_storage_mode": reservation_storage_mode(),
        "users": [asdict(user) for user in users],
        "access_requests": access_requests,
    }
    st.download_button(
        "Download identity and approval snapshot",
        data=json.dumps(snapshot, default=bridge_json_default, indent=2).encode("utf-8"),
        file_name=f"bridge_identity_approval_snapshot_{datetime.date.today().isoformat()}.json",
        mime="application/json",
    )


def hydrate_bridge_user(settings, auth_store):
    current_user = st.session_state.get("bridge_user")
    if current_user is not None:
        return current_user, None

    raw_session_token = st.session_state.get("bridge_raw_session_token") or get_session_cookie(settings.session_cookie_name)
    if raw_session_token is None:
        return None, None

    return hydrate_bridge_session_state(st.session_state, auth_store, raw_session_token), raw_session_token


def logout_bridge_user(settings, auth_store):
    raw_session_token = get_session_cookie(settings.session_cookie_name)
    auth_store.revoke_session(raw_session_token)
    clear_session_cookie(settings.session_cookie_name)
    clear_bridge_session_state(st.session_state)


def require_bridge_user():
    init_bridge_state()
    settings, auth_store, error_message = get_bridge_runtime()
    if error_message:
        st.error(error_message)
        st.stop()

    st.session_state["bridge_settings"] = settings

    user, raw_session_token = hydrate_bridge_user(settings, auth_store)
    if user is None:
        if should_retry_cookie_restore(st.session_state, raw_session_token=raw_session_token):
            st.rerun()
        user = render_bridge_login(settings, auth_store, st.session_state)
        if user is None:
            st.stop()

    return settings, auth_store, user


# Device type selection in sidebar
mobile = st.toggle('Mobile Version')
announcement_text = read_announcement()
settings, auth_store, bridge_user = require_bridge_user()
render_deployment_banner(settings)

if bridge_user.approval_state != "approved" or not bridge_user.is_email_verified:
    render_applicant_pending_access(
        settings,
        auth_store,
        bridge_user,
        logout_callback=lambda: logout_bridge_user(settings, auth_store),
    )
    st.stop()

# Apply the appropriate style based on the toggle
if mobile:
    apply_mobile_style()
    role = bridge_role()
    if st.button("Logout"):
        logout_bridge_user(settings, auth_store)
        st.rerun()  # Rerun the app to refresh the state

    # Always check if there's an announcement to display
    if announcement_text:
        # Using st.markdown to insert HTML for a moving text effect
        st.markdown(
            f"<marquee style='width: 40%; color: red; font-size: 20px;'>{announcement_text}</marquee>",
            unsafe_allow_html=True
        )

    # Usual app interface
    message = f"### Welcome <span class='welcome-message'>{st.session_state['name']}</span>"
    st.markdown(message, unsafe_allow_html=True)
    can_review_approvals = bridge_user.is_admin or bridge_user.is_sponsor

    if role == "Admins":
        mobile_sections = ["Reservation Tables", "Reservation Forms", "Reservation Cancellation", "Approval Requests", "Bridge Status", "Announcement"]
    elif can_review_approvals:
        mobile_sections = ["Reservation Tables", "Reservation Forms", "Reservation Cancellation", "Approval Requests", "Announcement"]
    else:
        mobile_sections = ["Reservation Tables", "Reservation Forms", "Reservation Cancellation"]

    if get_approval_request_id() and can_review_approvals:
        st.session_state["mobile_selected_section"] = "Approval Requests"
    if st.session_state.get("mobile_selected_section") not in mobile_sections:
        st.session_state["mobile_selected_section"] = mobile_sections[0]
    selected_tab = st.selectbox("### Select Actions", mobile_sections, key="mobile_selected_section")

    if selected_tab == "Reservation Tables":
        render_reservation_tables_section(
            "mobile",
            title_font_size=22,
            axis_title_size=14,
            tick_font_size=12,
            chart_width=530,
            margin_top=165,
        )
    elif selected_tab == "Reservation Forms":
        render_reservation_form_section("mobile", role, image_width=300)
    elif selected_tab == "Reservation Cancellation":
        render_reservation_cancellation_section("mobile")
    elif selected_tab == "Approval Requests":
        render_sponsor_request_history(auth_store, bridge_user, show_toggle=False)
    elif selected_tab == "Bridge Status":
        render_bridge_status_panel(auth_store, bridge_user)
    elif selected_tab == "Announcement":
        announcement_text = read_announcement()
        st.write("Admin and Lecturer Controls")
        with st.form("mobile_announcement_form"):
            new_announcement_text = st.text_area("Enter announcement:", value=announcement_text)
            update_announcement_button = st.form_submit_button("Update Announcement")

        if update_announcement_button:
            update_announcement(new_announcement_text, ANNOUNCEMENT_FILE_PATH)
            st.session_state['announcement'] = new_announcement_text

else:
    apply_web_style()
    role = bridge_role()
    # Check if the user is authorized (either an admin or a lecturer) and allow them to post an announcement
    if role in ["Admins", "Lecturer"]:
        with st.sidebar:
            st.write("Admin and Lecturer Controls")
            new_announcement_text = st.text_area("### Enter announcement:", value=announcement_text)
            if st.button("Update Announcement"):
                update_announcement(new_announcement_text,ANNOUNCEMENT_FILE_PATH)
                st.session_state['announcement'] = new_announcement_text

    # Always check if there's an announcement to display
    if announcement_text:
        # Using st.markdown to insert HTML for a moving text effect
        st.markdown(
            f"<marquee style='width: 100%; color: red; font-size: 24px;'>{announcement_text}</marquee>",
            unsafe_allow_html=True
        )

    message = f"### Welcome <span class='welcome-message'>{st.session_state['name']}</span>"
    st.markdown(message, unsafe_allow_html=True)
    if st.sidebar.button("Logout"):
        logout_bridge_user(settings, auth_store)
        st.rerun()  # Rerun the app to refresh the state

    can_review_approvals = bridge_user.is_admin or bridge_user.is_sponsor
    if role == "Admins":
        available_sections = ["Reservation Tables", "Reservation Forms", "Reservation Cancellation", "Approval Requests", "Bridge Status", "Admins Interface"]
    elif can_review_approvals:
        available_sections = ["Reservation Tables", "Reservation Forms", "Reservation Cancellation", "Approval Requests", "Contact Us"]
    else:
        available_sections = ["Reservation Tables", "Reservation Forms", "Reservation Cancellation", "Contact Us"]

    if get_approval_request_id() and can_review_approvals:
        st.session_state["desktop_selected_section"] = "Approval Requests"
    if st.session_state.get("desktop_selected_section") not in available_sections:
        st.session_state["desktop_selected_section"] = available_sections[0]

    selected_section = st.radio(
        "### Select Actions",
        available_sections,
        horizontal=True,
        label_visibility="collapsed",
        key="desktop_selected_section",
    )

    st.sidebar.download_button(
        label="Download General Reservations as CSV",
        data=download_non_pcr(),
        file_name='general_reservations.csv',
        mime='text/csv'
    )

    st.sidebar.download_button(
        label="Download PCR Reservations as CSV",
        data=download_pcr(),
        file_name='pcr_reservations.csv',
        mime='text/csv'
    )

    if selected_section == "Reservation Tables":
        render_reservation_tables_section(
            "web",
            title_font_size=26,
            axis_title_size=20,
            tick_font_size=18,
            chart_width=1000,
            margin_top=200,
        )
    elif selected_section == "Reservation Forms":
        render_reservation_form_section("web", role, image_width=450)
    elif selected_section == "Reservation Cancellation":
        render_reservation_cancellation_section("web")
    elif selected_section == "Approval Requests":
        render_sponsor_request_history(auth_store, bridge_user, show_toggle=False)
    elif selected_section == "Bridge Status":
        render_bridge_status_panel(auth_store, bridge_user)
    elif selected_section == "Contact Us":
        st.subheader("Error reports or Inconvenient issues")

        contact_form = """
        <form action="https://formsubmit.co/geneticsku.services@gmail.com" method="POST">
             <input type="hidden" name="_captcha" value="false">
             <input type="text" name="name" placeholder="Your name" required>
             <input type="email" name="email" placeholder="Your email" required>
             <textarea name="message" placeholder="Your message here"></textarea>
             <button type="submit">Send</button>
        </form>
        """

        st.markdown(contact_form, unsafe_allow_html=True)

    if role == "Admins":
        def admin_interface():
            st.write("### PCR Data")
            df_pcr = load_data(PCR_FILE_PATH)
            st.dataframe(df_pcr)

            st.write("### Non-PCR Data")
            df_non_pcr = load_data(NON_PCR_FILE_PATH)
            st.dataframe(df_non_pcr)

            st.write("### Autoclaves Counts")
            autoclaves_count = load_data(AUTOCLAVES_PATH)
            st.dataframe(autoclaves_count)

            st.write("### Logs")
            logs = load_data(LOG_FILE_PATH)
            st.dataframe(logs)

            st.write("### Manage Data")

            st.write("#### Add New Reservation")
            name = st.text_input("Name")

            selected_room = st.selectbox("Room", list(st.session_state.equipment_details.keys()))
            enabled_equipments = {eq: info for eq, info in st.session_state.equipment_details[selected_room].items()
                                  if info.get('enabled', False)}
            selected_equipment = st.selectbox("Equipment", list(enabled_equipments.keys()))

            if "PCR" in selected_equipment:
                st.subheader("Book Your PCR Slot")
                reservation_date = st.date_input("## Reservation Date")
                start_time = st.time_input("## Start Time")
                end_time = st.time_input("## End Time")

                start_datetime = datetime.datetime.combine(reservation_date, start_time)
                end_datetime = datetime.datetime.combine(reservation_date, end_time)

            else:
                st.subheader(f"Reserve {selected_equipment}")
                start_date = st.date_input("## Start Date")
                start_time = st.time_input("## Start Time")
                end_time = st.time_input("## End Time")

                start_datetime = datetime.datetime.combine(start_date, start_time)
                end_datetime = datetime.datetime.combine(start_date, end_time)

            if st.button("Add Reservation"):
                try:
                    new_reservation = pd.DataFrame([{
                        "Name": name,
                        "Room": selected_room,
                        "Equipments": selected_equipment,
                        "Start_Time": start_datetime,
                        "End_Time": end_datetime
                    }])
                    if "PCR" in selected_equipment:
                        df_pcr = pd.concat([df_pcr, new_reservation], ignore_index=True)
                        save_data(df_pcr, PCR_FILE_PATH)
                    else:
                        df_non_pcr = pd.concat([df_non_pcr, new_reservation], ignore_index=True)
                        save_data(df_non_pcr, NON_PCR_FILE_PATH)
                    st.success("Reservation added successfully.")
                    df_pcr = load_data(PCR_FILE_PATH)
                    df_non_pcr = load_data(NON_PCR_FILE_PATH)

                except Exception as e:
                    st.error(f"Error adding reservation: {e}")

            st.write("#### Delete Reservation")
            delete_id = st.text_input("Reservation ID to Delete")
            delete_from_pcr = st.checkbox("Delete from PCR Data", value=True)

            if st.button("Delete Reservation"):
                try:
                    if delete_from_pcr:
                        df_pcr = df_pcr.drop(index=int(delete_id))
                        save_data(df_pcr, PCR_FILE_PATH)
                    else:
                        df_non_pcr = df_non_pcr.drop(index=int(delete_id))
                        save_data(df_non_pcr, NON_PCR_FILE_PATH)
                    st.success("Reservation deleted successfully.")
                    df_pcr = load_data(PCR_FILE_PATH)
                    df_non_pcr = load_data(NON_PCR_FILE_PATH)

                except Exception as e:
                    st.error(f"Error deleting reservation: {e}")

            st.write("#### Update Reservation")
            update_id = st.text_input("Reservation ID to Update")
            update_field = st.selectbox("Field to Update", ["Name", "Room", "Equipments", "Start_Time", "End_Time"])
            new_value = st.text_input("New Value")
            update_in_pcr = st.checkbox("Update in PCR Data", value=True)

            if st.button("Update Reservation"):
                try:
                    if update_in_pcr:
                        if update_field in ["Start_Time", "End_Time"]:
                            df_pcr.at[int(update_id), update_field] = pd.to_datetime(new_value)
                        else:
                            df_pcr.at[int(update_id), update_field] = new_value
                        save_data(df_pcr, PCR_FILE_PATH)
                    else:
                        if update_field in ["Start_Time", "End_Time"]:
                            df_non_pcr.at[int(update_id), update_field] = pd.to_datetime(new_value)
                        else:
                            df_non_pcr.at[int(update_id), update_field] = new_value
                        save_data(df_non_pcr, NON_PCR_FILE_PATH)
                    st.success("Reservation updated successfully.")
                except Exception as e:
                    st.error(f"Error updating reservation: {e}")

            st.write("### Equipment Availability")
            selected_room_admin = st.selectbox("Select a room to manage equipment:", list(st.session_state.equipment_details.keys()))
            equipment_list = list(st.session_state.equipment_details[selected_room_admin].keys())
            selected_equipment_admin = st.selectbox("Select equipment to toggle availability:", equipment_list)

            if st.button("Toggle Availability"):
                current_status = st.session_state.equipment_details[selected_room_admin][selected_equipment_admin]['enabled']
                st.session_state.equipment_details[selected_room_admin][selected_equipment_admin]['enabled'] = not current_status
                st.success(f"{'Disabled' if current_status else 'Enabled'} {selected_equipment_admin}")
                save_equipment_details(st.session_state.equipment_details)

            st.write("#### Upload CSV to Update Data")
            uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
            update_pcr = st.checkbox("Update PCR Data", value=True)

            if uploaded_file is not None and st.button("Update Data"):
                try:
                    uploaded_df = pd.read_csv(uploaded_file)
                    if update_pcr:
                        save_data(uploaded_df, PCR_FILE_PATH)
                        st.success("PCR data updated successfully.")
                    else:
                        save_data(uploaded_df, NON_PCR_FILE_PATH)
                        st.success("Non-PCR data updated successfully.")
                except Exception as e:
                    st.error(f"Error updating data: {e}")

        if selected_section == "Admins Interface":
            st.write("## Admins Interface")
            st.write("You can view and manipulate the data frames here.")
            admin_interface()

    def local_css(file_name):
        with open(file_name) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

    local_css("style.css")
