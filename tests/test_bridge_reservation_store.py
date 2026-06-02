from __future__ import annotations

import pandas as pd

from bridge.reservation_store import (
    RESERVATION_COLUMNS,
    dataframe_to_reservation_rows,
    reservation_rows_to_dataframe,
    reservation_type_for_file_path,
)


def test_reservation_type_for_file_path_maps_known_csvs() -> None:
    assert reservation_type_for_file_path("pcr_data.csv") == "pcr"
    assert reservation_type_for_file_path("non_pcr_data.csv") == "non_pcr"
    assert reservation_type_for_file_path("announcement.txt") is None


def test_dataframe_to_reservation_rows_normalizes_timestamps() -> None:
    df = pd.DataFrame(
        [
            {
                "Name": "BridgeSmoke_4511",
                "Room": "Central Lab, 5th floor",
                "Equipments": "Incubator Shaker 1",
                "Start_Time": "2026/05/29 09:00:00",
                "End_Time": "2026/05/29 12:00:00",
            }
        ]
    )

    rows = dataframe_to_reservation_rows(df, "non_pcr")

    assert len(rows) == 1
    assert rows[0]["reservation_type"] == "non_pcr"
    assert rows[0]["name"] == "BridgeSmoke_4511"
    assert rows[0]["start_time"].tzinfo is not None


def test_reservation_rows_to_dataframe_formats_expected_columns() -> None:
    df = reservation_rows_to_dataframe(
        [
            {
                "name": "BridgeSmoke_4511",
                "room": "Central Lab, 5th floor",
                "equipments": "Incubator Shaker 1",
                "start_time": pd.Timestamp("2026-05-29T09:00:00Z"),
                "end_time": pd.Timestamp("2026-05-29T12:00:00Z"),
            }
        ]
    )

    assert list(df.columns) == RESERVATION_COLUMNS
    assert df.iloc[0]["Start_Time"] == "2026/05/29 09:00:00"
    assert df.iloc[0]["End_Time"] == "2026/05/29 12:00:00"
