from __future__ import annotations

import datetime

import streamlit as st

from bridge.auth_store import InvalidLoginCodeError, normalize_email
from bridge.bootstrap import write_authenticated_user
from bridge.emailer import send_login_code_email
from bridge.session_cookie import set_session_cookie


def render_deployment_banner(settings) -> None:
    if settings.deployment_label:
        st.caption(settings.deployment_label)
    if settings.deployment_notice:
        st.warning(settings.deployment_notice)


def finish_successful_login(settings, session_state, user, raw_session_token: str):
    session_state["bridge_pending_email"] = ""
    session_state.pop("bridge_login_code", None)
    write_authenticated_user(session_state, user, raw_session_token=raw_session_token)
    cookie_expiry = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=settings.session_ttl_hours)
    set_session_cookie(settings.session_cookie_name, raw_session_token, cookie_expiry)
    return user


def render_bridge_login(settings, auth_store, session_state):
    render_deployment_banner(settings)
    st.title("Login")
    flash_message = session_state.pop("bridge_login_notice", None)
    if flash_message:
        st.success(flash_message)

    pending_email = session_state.get("bridge_pending_email", "")
    if not pending_email:
        with st.form("bridge_send_code_form"):
            email_input = st.text_input(
                "KU Email",
                value=session_state.get("bridge_pending_email", ""),
                key="bridge_login_email",
            )
            send_code = st.form_submit_button("Send one-time code")
    else:
        email_input = pending_email
        send_code = False

    if send_code:
        try:
            normalized_email = normalize_email(email_input)
            login_code = auth_store.issue_login_code(normalized_email)
            send_login_code_email(settings, normalized_email, login_code)
            session_state["bridge_pending_email"] = normalized_email
            session_state["bridge_login_notice"] = f"A login code was sent to {normalized_email}."
            session_state.pop("bridge_login_code", None)
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))
        except Exception as exc:
            st.error(f"Unable to send login code: {exc}")

    if pending_email:
        st.caption(f"Verifying code for: {pending_email}")
        login_code = st.text_input("One-time code", key="bridge_login_code")
        verify_code = st.button("Verify code", key="bridge_verify_code_button")

        if verify_code:
            try:
                user = auth_store.verify_login_code(pending_email, login_code)
                raw_session_token = auth_store.create_session(user.id)
                return finish_successful_login(settings, session_state, user, raw_session_token)
            except InvalidLoginCodeError as exc:
                st.error(str(exc))
            except Exception as exc:
                st.error(f"Unable to complete sign-in: {exc}")

        if st.button("Use a different email", key="bridge_reset_login_flow"):
            session_state["bridge_pending_email"] = ""
            session_state.pop("bridge_login_code", None)
            st.rerun()

    return None
