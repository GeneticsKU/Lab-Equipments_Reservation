from __future__ import annotations

from datetime import timezone
from typing import Iterable

import pandas as pd

from bridge.db import PostgresBridgeRepository


PCR_FILE_PATH = "pcr_data.csv"
NON_PCR_FILE_PATH = "non_pcr_data.csv"

RESERVATION_FILE_TYPE_MAP = {
    PCR_FILE_PATH: "pcr",
    NON_PCR_FILE_PATH: "non_pcr",
}

RESERVATION_COLUMNS = ["Name", "Room", "Equipments", "Start_Time", "End_Time"]


def reservation_type_for_file_path(file_path: str) -> str | None:
    return RESERVATION_FILE_TYPE_MAP.get(file_path)


def dataframe_to_reservation_rows(df: pd.DataFrame, reservation_type: str) -> list[dict]:
    if df.empty:
        return []

    working = df.copy()
    for column in RESERVATION_COLUMNS:
        if column not in working.columns:
            working[column] = None

    working["Start_Time"] = pd.to_datetime(working["Start_Time"], errors="coerce")
    working["End_Time"] = pd.to_datetime(working["End_Time"], errors="coerce")
    working = working.dropna(subset=["Name", "Room", "Equipments", "Start_Time", "End_Time"])

    rows: list[dict] = []
    for row in working[RESERVATION_COLUMNS].itertuples(index=False):
        start_time = _normalize_timestamp(row.Start_Time)
        end_time = _normalize_timestamp(row.End_Time)
        rows.append(
            {
                "reservation_type": reservation_type,
                "name": str(row.Name),
                "room": str(row.Room),
                "equipments": str(row.Equipments),
                "start_time": start_time,
                "end_time": end_time,
            }
        )
    return rows


def reservation_rows_to_dataframe(rows: Iterable[dict]) -> pd.DataFrame:
    normalized_rows = []
    for row in rows:
        normalized_rows.append(
            {
                "Name": row["name"],
                "Room": row["room"],
                "Equipments": row["equipments"],
                "Start_Time": _format_timestamp(row["start_time"]),
                "End_Time": _format_timestamp(row["end_time"]),
            }
        )
    if not normalized_rows:
        return pd.DataFrame(columns=RESERVATION_COLUMNS)
    return pd.DataFrame(normalized_rows, columns=RESERVATION_COLUMNS)


class BridgeReservationStore:
    def __init__(self, settings) -> None:
        self.repository = PostgresBridgeRepository(settings)

    def load_dataframe(self, reservation_type: str) -> pd.DataFrame:
        return reservation_rows_to_dataframe(self.repository.list_reservations(reservation_type))

    def save_dataframe(self, reservation_type: str, df: pd.DataFrame) -> None:
        self.repository.replace_reservations(reservation_type, dataframe_to_reservation_rows(df, reservation_type))


def _normalize_timestamp(value):
    if hasattr(value, "to_pydatetime"):
        value = value.to_pydatetime()
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _format_timestamp(value) -> str:
    if hasattr(value, "to_pydatetime"):
        value = value.to_pydatetime()
    if value.tzinfo is not None:
        value = value.astimezone(timezone.utc).replace(tzinfo=None)
    return value.strftime("%Y/%m/%d %H:%M:%S")
