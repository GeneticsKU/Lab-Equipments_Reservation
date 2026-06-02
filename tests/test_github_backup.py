from __future__ import annotations

import pytest

from bridge.github_backup import (
    build_push_refspec,
    build_repo_url,
    resolve_github_backup_settings,
)


def test_resolve_github_backup_settings_uses_current_branch_when_not_overridden() -> None:
    settings = resolve_github_backup_settings(
        {
            "username": "geneticsku",
            "email": "lab@example.com",
            "token": "secret-token",
        },
        current_branch="bridge-pilot",
    )

    assert settings.repo_owner == "geneticsku"
    assert settings.repo_name == "Lab-Equipments_Reservation"
    assert settings.branch == "bridge-pilot"


def test_resolve_github_backup_settings_respects_explicit_repo_and_branch() -> None:
    settings = resolve_github_backup_settings(
        {
            "username": "geneticsku",
            "email": "lab@example.com",
            "token": "secret-token",
            "repo_owner": "GeneticsKU",
            "repo_name": "Lab-Equipments_Reservation_Bridge",
            "branch": "pilot-live",
        },
        current_branch="bridge-pilot",
    )

    assert build_repo_url(settings) == "https://geneticsku:secret-token@github.com/GeneticsKU/Lab-Equipments_Reservation_Bridge.git"
    assert build_push_refspec(settings) == "HEAD:refs/heads/pilot-live"


def test_resolve_github_backup_settings_requires_branch_when_missing_everywhere() -> None:
    with pytest.raises(KeyError):
        resolve_github_backup_settings(
            {
                "username": "geneticsku",
                "email": "lab@example.com",
                "token": "secret-token",
            },
            current_branch=None,
        )
