#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# config.py
import os

APP_NAME = "ToolBox"
APP_VERSION = "1.0.0"
WINDOW_TITLE = "ToolBox v1.0.0"

MANIFEST_URL = "https://raw.githubusercontent.com/jason910727/ToolBox-Setup/main/manifest"

CACHE_DIR = "cache"
CACHE_FILE = os.path.join(CACHE_DIR, "manifest_cache.json")

# 依你的需求：電腦預設(C槽下載)
DEFAULT_INSTALL_DIR = os.path.join(os.path.expanduser("~"), "Downloads")

REQUEST_TIMEOUT = 15

WINDOW_WIDTH = 1240
WINDOW_HEIGHT = 800

PRIMARY_COLOR = "#D9ECFF"
PRIMARY_COLOR_DARK = "#A9D3FF"
CARD_BG = "#FFFFFF"
APP_BG = "#F7FBFF"
BORDER_COLOR = "#D5E6F7"
TEXT_COLOR = "#1F2D3D"
SUBTEXT_COLOR = "#5B6B7A"

