#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# api.py
import requests
from config import REQUEST_TIMEOUT


def fetch_manifest(url: str):
    try:
        r = requests.get(url, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print("fetch_manifest error:", e)
        return None


def github_latest_release(owner: str, repo: str):
    url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "ToolBox"
    }
    r = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
    r.raise_for_status()
    return r.json()

