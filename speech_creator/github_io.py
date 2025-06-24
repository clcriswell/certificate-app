"""Utilities for loading and saving files via GitHub."""
from __future__ import annotations

from typing import List, Optional
import base64
import streamlit as st
from github import Github, GithubException


def _get_repo():
    """Return the GitHub repository object using Streamlit secrets."""
    token = st.secrets.get("GITHUB_TOKEN")
    repo_name = st.secrets.get("GITHUB_REPO", "clcriswell/certificate-app")
    if not token:
        raise RuntimeError("GITHUB_TOKEN secret not configured")
    gh = Github(token)
    return gh.get_repo(repo_name)


def load_file(path: str) -> Optional[str]:
    """Load file content from GitHub or return None if not found."""
    repo = _get_repo()
    try:
        file = repo.get_contents(path)
        return base64.b64decode(file.content).decode("utf-8")
    except GithubException as e:
        if e.status == 404:
            return None
        raise


def save_file(path: str, content: str, message: str) -> None:
    """Create or update a file in the repository."""
    repo = _get_repo()
    try:
        existing = repo.get_contents(path)
        repo.update_file(existing.path, message, content, existing.sha, branch="main")
    except GithubException as e:
        if e.status == 404:
            repo.create_file(path, message, content, branch="main")
        else:
            raise


def list_files(folder: str) -> List[str]:
    """List file names in the given GitHub folder."""
    repo = _get_repo()
    try:
        contents = repo.get_contents(folder)
        return [c.path for c in contents if c.type == "file"]
    except GithubException as e:
        if e.status == 404:
            return []
        raise
