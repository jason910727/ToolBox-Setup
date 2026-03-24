#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# models.py
from dataclasses import dataclass


@dataclass
class ToolItem:
    name: str 
    repo_owner: str
    repo_name: str
    exe_name: str
    description: str = ""
    tutorial_url: str = ""
    homepage_url: str = ""
    enabled: bool = True
    install_subdir: str = "{version}{name}"

    latest_version: str = ""
    latest_download_url: str = ""
    installed_version: str = ""
    installed_path: str = ""
    status_text: str = "未知"

