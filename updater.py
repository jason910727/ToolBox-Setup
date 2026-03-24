#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# updater.py
import os
import requests

from PyQt5.QtCore import QThread, pyqtSignal
from config import REQUEST_TIMEOUT
from utils import ensure_dir


class DownloadWorker(QThread):
    progress_changed = pyqtSignal(int)
    status_changed = pyqtSignal(str)
    finished_ok = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(self, url: str, save_path: str):
        super().__init__()
        self.url = url
        self.save_path = save_path
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        try:
            ensure_dir(os.path.dirname(self.save_path))
            tmp_path = self.save_path + ".part"

            self.status_changed.emit("開始下載")

            with requests.get(self.url, stream=True, timeout=REQUEST_TIMEOUT) as r:
                r.raise_for_status()
                total = int(r.headers.get("Content-Length", 0))
                downloaded = 0

                with open(tmp_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if self._cancelled:
                            self.status_changed.emit("已取消")
                            try:
                                f.close()
                            except Exception:
                                pass
                            if os.path.exists(tmp_path):
                                os.remove(tmp_path)
                            return

                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total > 0:
                                self.progress_changed.emit(int(downloaded * 100 / total))

            if os.path.exists(self.save_path):
                os.remove(self.save_path)
            os.rename(tmp_path, self.save_path)

            self.progress_changed.emit(100)
            self.status_changed.emit("下載完成")
            self.finished_ok.emit(self.save_path)

        except Exception as e:
            self.failed.emit(str(e))

