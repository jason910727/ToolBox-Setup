#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# utils.py
import os
import re
import subprocess
import sys
from packaging.version import Version, InvalidVersion


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def normalize_version(v: str) -> str:
    if not v:
        return ""
    return str(v).strip().lstrip("v").strip()


def safe_version(v: str):
    try:
        return Version(normalize_version(v))
    except InvalidVersion:
        return None


def compare_versions(v1: str, v2: str) -> int:
    a = safe_version(v1)
    b = safe_version(v2)

    if a is not None and b is not None:
        if a > b:
            return 1
        if a < b:
            return -1
        return 0

    s1 = normalize_version(v1)
    s2 = normalize_version(v2)
    if s1 == s2:
        return 0
    return 1 if s1 > s2 else -1


def open_path(path: str):
    if not os.path.exists(path):
        return
    if sys.platform.startswith("win"):
        os.startfile(path)
    elif sys.platform == "darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])


def open_url(url: str):
    import webbrowser
    if url:
        webbrowser.open(url)


def run_exe(path: str):
    if os.path.exists(path):
        subprocess.Popen(path)


def format_install_subdir(template: str, version: str, name: str) -> str:
    template = template or "{name}_V{version}"
    return (
        template
        .replace("{version}", normalize_version(version) if version else "")
        .replace("{name}", name)
    )


def extract_version_from_folder_name(folder_name: str, tool_name: str) -> str:
    """
    例如：
    v1.2.0KNEX -> 1.2.0
    1.2.0KNEX  -> 1.2.0
    """
    if not folder_name:
        return ""

    pattern = rf"^v?([0-9]+(?:\.[0-9]+)*)\s*{re.escape(tool_name)}$"
    m = re.match(pattern, folder_name, re.IGNORECASE)
    if m:
        return m.group(1)

    pattern2 = r"v?([0-9]+(?:\.[0-9]+)*)"
    m2 = re.search(pattern2, folder_name, re.IGNORECASE)
    if m2:
        return m2.group(1)

    return ""

