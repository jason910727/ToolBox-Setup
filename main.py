#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# main.py
import os
import re
import sys
import subprocess

from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QSettings

from config import (
    APP_NAME, APP_VERSION, WINDOW_TITLE, MANIFEST_URL, CACHE_FILE,
    DEFAULT_INSTALL_DIR, WINDOW_WIDTH, WINDOW_HEIGHT
)
from api import fetch_manifest, github_latest_release
from cache import save_cache, load_cache
from models import ToolItem
from ui_main import MainWindow
from utils import (
    compare_versions, format_install_subdir, extract_version_from_folder_name
)


def file_version_windows(path: str) -> str:
    if not os.path.exists(path):
        return ""
    try:
        cmd = [
            "powershell",
            "-NoProfile",
            "-Command",
            f"(Get-Item '{path}').VersionInfo.FileVersion"
        ]
        out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, text=True, encoding="utf-8")
        return out.strip().lstrip("v")
    except Exception:
        return ""


def load_manifest_data():
    data = fetch_manifest(MANIFEST_URL)
    if data:
        save_cache(CACHE_FILE, data)
        return data
    return load_cache(CACHE_FILE)


def detect_installed_version(install_root: str, tool: ToolItem) -> tuple[str, str]:
    """
    優先順序：
    1. 找最新版本資料夾中的 exe，讀 FileVersion
    2. 若沒有 FileVersion，從資料夾名解析版本
    """
    if not os.path.exists(install_root):
        return "", ""

    best_version = ""
    best_path = ""

    for name in os.listdir(install_root):
        full_dir = os.path.join(install_root, name)
        if not os.path.isdir(full_dir):
            continue

        exe_path = os.path.join(full_dir, tool.exe_name)
        if not os.path.exists(exe_path):
            continue

        folder_ver = extract_version_from_folder_name(name, tool.name)
        file_ver = file_version_windows(exe_path)

        detected_ver = file_ver or folder_ver
        if not detected_ver:
            continue

        if not best_version or compare_versions(detected_ver, best_version) == 1:
            best_version = detected_ver
            best_path = exe_path

    return best_version, best_path


def parse_tools(manifest, install_dir):
    tools = []

    for item in manifest.get("tools", []):
        tool = ToolItem(
            name=item["name"],
            repo_owner=item["repo_owner"],
            repo_name=item["repo_name"],
            exe_name=item["exe_name"],
            description=item.get("description", ""),
            tutorial_url=item.get("tutorial_url", ""),
            homepage_url=item.get("homepage_url", ""),
            enabled=item.get("enabled", True),
            install_subdir=item.get("install_subdir", "{version}{name}")
        )

        try:
            rel = github_latest_release(tool.repo_owner, tool.repo_name)
            tag = str(rel.get("tag_name", "")).lstrip("v")
            assets = rel.get("assets", [])

            tool.latest_version = tag
            tool.latest_download_url = ""

            # 優先找同名 exe
            for a in assets:
                asset_name = a.get("name", "")
                if asset_name.lower() == tool.exe_name.lower():
                    tool.latest_download_url = a.get("browser_download_url", "")
                    break

            # 找不到同名 exe，就抓第一個 .exe
            if not tool.latest_download_url:
                for a in assets:
                    asset_name = a.get("name", "")
                    if asset_name.lower().endswith(".exe"):
                        tool.latest_download_url = a.get("browser_download_url", "")
                        break

            # 再找不到才抓第一個 asset
            if not tool.latest_download_url and assets:
                tool.latest_download_url = assets[0].get("browser_download_url", "")

        except Exception as e:
            print(f"[{tool.name}] latest release 失敗:", e)
            tool.latest_version = item.get("fallback_version", "")
            tool.latest_download_url = item.get("fallback_download_url", "")

        installed_version, installed_path = detect_installed_version(install_dir, tool)
        tool.installed_version = installed_version
        tool.installed_path = installed_path

        if tool.latest_version and tool.installed_version:
            if compare_versions(tool.latest_version, tool.installed_version) == 1:
                tool.status_text = "可更新"
            else:
                tool.status_text = "已安裝"
        elif tool.installed_version:
            tool.status_text = "已安裝"
        else:
            tool.status_text = "未安裝"

        tools.append(tool)

    return tools


def get_install_dir():
    settings = QSettings("KSU-Tools", "ToolBox")
    return settings.value("install_dir", DEFAULT_INSTALL_DIR)


def main():
    app = QApplication(sys.argv)

    manifest = load_manifest_data()
    if not manifest:
        QMessageBox.critical(None, "錯誤", "無法載入 manifest，也沒有快取可用。")
        sys.exit(1)

    install_dir = get_install_dir()
    tools = parse_tools(manifest, install_dir)

    settings = QSettings("KSU-Tools", "ToolBox")
    win = MainWindow(WINDOW_TITLE, tools, install_dir, manifest, settings)
    win.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
    win.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

