from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

import pandas as pd


NAME_COLUMN = "First name and Last name (In English)"
AFFILIATION_COLUMN = "Lab ( Room number)"
ROLE_COLUMN = "Roles"
KU_EMAIL_COLUMN = "Email (KU)"
FORM_EMAIL_COLUMN = "Email Address"
USERNAME_COLUMN = "Username (Special Characters are not allowed *including Space) สำหรับเข้าใช้งานแอปจองเครื่องมือ"


def clean_text(value) -> str:
    if value is None or pd.isna(value):
        return ""
    text = str(value)
    text = text.replace("\u200b", "").replace("\ufeff", "").strip()
    return text


def normalize_email(value) -> str:
    return clean_text(value).lower()


def is_allowed_ku_email(email: str) -> bool:
    return email.endswith("@ku.th")


def canonical_role(raw_role: str) -> str:
    role = clean_text(raw_role)
    return re.sub(r"\s+", " ", role)


def legacy_role_for_bridge(role: str) -> str:
    if role == "Lecturer":
        return "Lecturer"
    if role == "Admin":
        return "Admins"
    return "User"


def choose_login_email(row: pd.Series) -> str:
    candidates = [
        normalize_email(row.get(FORM_EMAIL_COLUMN)),
        normalize_email(row.get(KU_EMAIL_COLUMN)),
    ]
    for email in candidates:
        if is_allowed_ku_email(email):
            return email
    return ""


def normalize_affiliation(value) -> str | None:
    cleaned = clean_text(value)
    return cleaned or None


def build_username_seed(raw_username: str, email: str, row_index: int) -> str:
    candidate = clean_text(raw_username)
    if not candidate:
        candidate = email.split("@", 1)[0] if email else f"user_{row_index + 1}"
    candidate = re.sub(r"\s+", "_", candidate)
    return candidate


def make_unique_username(seed: str, used: set[str]) -> str:
    candidate = seed
    suffix = 2
    while candidate in used:
        candidate = f"{seed}_{suffix}"
        suffix += 1
    used.add(candidate)
    return candidate


def convert_registration_sheet(input_path: Path) -> tuple[list[dict], dict[str, dict], dict]:
    dataframe = pd.read_excel(input_path)
    sponsors: list[dict] = []
    legacy_users: dict[str, dict] = {}
    used_usernames: set[str] = set()
    skipped_rows: list[dict] = []
    role_counts: dict[str, int] = {}

    for row_index, row in dataframe.iterrows():
        role = canonical_role(row.get(ROLE_COLUMN))
        role_counts[role] = role_counts.get(role, 0) + 1

        email = choose_login_email(row)
        if not email:
            skipped_rows.append(
                {
                    "row_number": row_index + 2,
                    "name": clean_text(row.get(NAME_COLUMN)),
                    "role": role,
                    "reason": "No valid @ku.th email found in Email Address or Email (KU).",
                }
            )
            continue

        full_name = clean_text(row.get(NAME_COLUMN)) or email
        affiliation = normalize_affiliation(row.get(AFFILIATION_COLUMN))
        username_seed = build_username_seed(row.get(USERNAME_COLUMN), email, row_index)
        username = make_unique_username(username_seed, used_usernames)
        legacy_role = legacy_role_for_bridge(role)

        legacy_users[username] = {
            "name": full_name,
            "email": email,
            "role": legacy_role,
        }

        if role == "Lecturer":
            sponsors.append(
                {
                    "email": email,
                    "full_name": full_name,
                    "affiliation": affiliation,
                }
            )

    report = {
        "input_file": str(input_path),
        "total_rows": int(len(dataframe)),
        "role_counts": role_counts,
        "sponsor_count": len(sponsors),
        "legacy_user_count": len(legacy_users),
        "skipped_count": len(skipped_rows),
        "skipped_rows": skipped_rows,
    }
    return sponsors, legacy_users, report


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Export sponsor seed data and legacy-user import data from the registration spreadsheet.")
    parser.add_argument("--input", required=True, help="Path to the registration response .xlsx file.")
    parser.add_argument("--sponsors-output", required=True, help="Path to write sponsor seed JSON.")
    parser.add_argument("--legacy-output", required=True, help="Path to write legacy user JSON.")
    parser.add_argument("--report-output", required=True, help="Path to write conversion summary JSON.")
    args = parser.parse_args()

    input_path = Path(args.input)
    sponsors, legacy_users, report = convert_registration_sheet(input_path)
    write_json(Path(args.sponsors_output), sponsors)
    write_json(Path(args.legacy_output), {"usernames": legacy_users})
    write_json(Path(args.report_output), report)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
