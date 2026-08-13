"""Repository loader: validate a GitHub URL (SSRF-safe), shallow-clone it, and
walk + filter the files. No code is ever executed — files are only read.
"""
from __future__ import annotations

import ipaddress
import os
import shutil
import socket
import tempfile
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import ParseResult, urlparse

from git import Repo
from git.exc import GitCommandError

from app.config import settings
from app.services.ingest.constants import (
    ALLOWED_HOSTS,
    ALLOWED_SCHEMES,
    BYTES_PER_MB,
    ENV_FILE_PREFIX,
    ENV_FILENAME,
    IGNORED_DIRS,
    IGNORED_FILENAMES,
    IGNORED_SUFFIXES,
    MSG_CLONE_FAILED,
    MSG_CREDENTIALS_NOT_ALLOWED,
    MSG_FILE_LIMIT_EXCEEDED,
    MSG_HOST_NOT_ALLOWED,
    MSG_INVALID_SCHEME,
    MSG_NON_PUBLIC_ADDRESS,
    MSG_SIZE_LIMIT_EXCEEDED,
    MSG_UNRESOLVABLE_HOST,
    MSG_URL_REQUIRED,
    SECRET_SUFFIXES,
    SSH_KEY_FILENAMES,
    TMP_DIR_PREFIX,
)


class RepoValidationError(ValueError):
    """The URL is not an acceptable public GitHub repository."""


class RepoCloneError(RuntimeError):
    """git clone failed."""


class RepoLimitError(RuntimeError):
    """The repository exceeds the configured size/file-count limits."""


@dataclass
class FileEntry:
    path: str  # repo-relative POSIX path, e.g. "app/main.py"
    abs_path: Path  # absolute path on disk (inside the temp dir)
    size: int  # bytes


def _normalize_url(raw_url: str) -> str:
    """Trim whitespace; reject an empty URL."""
    url = (raw_url or "").strip()
    if not url:
        raise RepoValidationError(MSG_URL_REQUIRED)
    return url


def _ensure_allowed_scheme(parsed: ParseResult) -> None:
    """Only http(s) — blocks file://, ssh://, git@..."""
    if parsed.scheme not in ALLOWED_SCHEMES:
        raise RepoValidationError(MSG_INVALID_SCHEME)


def _ensure_no_credentials(parsed: ParseResult) -> None:
    """Reject embedded credentials, e.g. https://user:pass@github.com/..."""
    if parsed.username or parsed.password:
        raise RepoValidationError(MSG_CREDENTIALS_NOT_ALLOWED)


def _ensure_allowed_host(parsed: ParseResult) -> str:
    """Only public github.com; returns the lowercased host."""
    host = (parsed.hostname or "").lower()
    if host not in ALLOWED_HOSTS:
        raise RepoValidationError(MSG_HOST_NOT_ALLOWED)
    return host


def _ensure_public_address(host: str) -> None:
    """Resolve the host and reject non-public IPs (guards DNS rebinding / SSRF)."""
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror as exc:
        raise RepoValidationError(MSG_UNRESOLVABLE_HOST.format(host=host)) from exc
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if (
            ip.is_private or ip.is_loopback or ip.is_link_local
            or ip.is_reserved or ip.is_multicast or ip.is_unspecified
        ):
            raise RepoValidationError(MSG_NON_PUBLIC_ADDRESS)


def validate_repo_url(raw_url: str) -> str:
    """Return a normalized URL or raise RepoValidationError.

    SSRF defense: only http(s) to github.com, no credentials, and the host must
    not resolve to a private/loopback/link-local/reserved address.
    """
    url    = _normalize_url(raw_url)
    parsed = urlparse(url)

    _ensure_allowed_scheme(parsed)
    _ensure_no_credentials(parsed)

    host = _ensure_allowed_host(parsed)
    _ensure_public_address(host)

    return url


def _is_ignored_file(name: str) -> bool:
    if name in IGNORED_FILENAMES:
        return True
    if name == ENV_FILENAME or name.startswith(ENV_FILE_PREFIX):
        return True
    if name in SSH_KEY_FILENAMES:
        return True
    suffix = Path(name).suffix.lower()
    return suffix in IGNORED_SUFFIXES or suffix in SECRET_SUFFIXES


def _collect_files(root: Path) -> list[FileEntry]:
    files: list[FileEntry] = []
    total_bytes = 0
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        # Prune ignored + symlinked dirs in place (don't descend / follow out of root).
        dirnames[:] = [
            d for d in dirnames
            if d not in IGNORED_DIRS and not os.path.islink(os.path.join(dirpath, d))
        ]
        for name in filenames:
            abs_path = Path(dirpath) / name
            if abs_path.is_symlink() or _is_ignored_file(name):
                continue
            try:
                size = abs_path.stat().st_size
            except OSError:
                continue
            if size > settings.MAX_FILE_BYTES:
                continue
            files.append(
                FileEntry(path=abs_path.relative_to(root).as_posix(), abs_path=abs_path, size=size)
            )
            total_bytes += size
            if len(files) > settings.MAX_FILES:
                raise RepoLimitError(MSG_FILE_LIMIT_EXCEEDED.format(limit=settings.MAX_FILES))
            if total_bytes > settings.MAX_REPO_MB * BYTES_PER_MB:
                raise RepoLimitError(MSG_SIZE_LIMIT_EXCEEDED.format(limit=settings.MAX_REPO_MB))
    return files


def clone_and_collect(url: str) -> tuple[Path, list[FileEntry]]:
    """Shallow-clone `url` to a temp dir and return (temp_dir, filtered files).

    The caller owns the temp dir and must remove it. Raises RepoCloneError or
    RepoLimitError (temp dir is cleaned up before those propagate).
    """
    tmp_dir = Path(tempfile.mkdtemp(prefix=TMP_DIR_PREFIX))
    try:
        Repo.clone_from(url, str(tmp_dir), depth=1, single_branch=True) # branch='branchName', will decide it later
    except GitCommandError as exc:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        raise RepoCloneError(MSG_CLONE_FAILED.format(detail=exc.stderr or exc)) from exc

    try:
        files = _collect_files(tmp_dir)
    except RepoLimitError:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        raise
    return tmp_dir, files
