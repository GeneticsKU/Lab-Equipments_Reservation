from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class GitHubBackupSettings:
    username: str
    email: str
    token: str
    repo_owner: str
    repo_name: str
    branch: str


def resolve_github_backup_settings(github_secrets: Mapping[str, str], *, current_branch: str | None) -> GitHubBackupSettings:
    username = github_secrets["username"]
    email = github_secrets["email"]
    token = github_secrets["token"]
    repo_owner = github_secrets.get("repo_owner") or username
    repo_name = github_secrets.get("repo_name") or "Lab-Equipments_Reservation"
    branch = github_secrets.get("branch") or current_branch
    if not branch:
        raise KeyError("branch")

    return GitHubBackupSettings(
        username=username,
        email=email,
        token=token,
        repo_owner=repo_owner,
        repo_name=repo_name,
        branch=branch,
    )


def build_repo_url(settings: GitHubBackupSettings) -> str:
    return f"https://{settings.username}:{settings.token}@github.com/{settings.repo_owner}/{settings.repo_name}.git"


def build_push_refspec(settings: GitHubBackupSettings) -> str:
    return f"HEAD:refs/heads/{settings.branch}"
