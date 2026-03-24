#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# widgets.py
import os
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QFrame, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QProgressBar


class ToolCard(QFrame):
    request_open = pyqtSignal(object)
    request_update = pyqtSignal(object)
    request_detail = pyqtSignal(object)
    request_tutorial = pyqtSignal(object)

    def __init__(self, tool):
        super().__init__()
        self.tool = tool
        self.setObjectName("ToolCard")

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        title = QLabel(f"<b style='font-size:18px'>{tool.name}</b>")
        desc = QLabel(tool.description or "尚未填寫說明")
        desc.setWordWrap(True)

        self.lbl_latest = QLabel()
        self.lbl_installed = QLabel()
        self.lbl_status = QLabel()

        self.progress = QProgressBar()
        self.progress.setVisible(False)

        btn_row = QHBoxLayout()
        self.btn_open = QPushButton("開啟")
        self.btn_update = QPushButton("下載 / 更新")
        self.btn_detail = QPushButton("詳細")
        self.btn_tutorial = QPushButton("教學")

        self.btn_open.clicked.connect(lambda: self.request_open.emit(self.tool))
        self.btn_update.clicked.connect(lambda: self.request_update.emit(self.tool))
        self.btn_detail.clicked.connect(lambda: self.request_detail.emit(self.tool))
        self.btn_tutorial.clicked.connect(lambda: self.request_tutorial.emit(self.tool))

        btn_row.addWidget(self.btn_open)
        btn_row.addWidget(self.btn_update)
        btn_row.addWidget(self.btn_detail)
        btn_row.addWidget(self.btn_tutorial)

        layout.addWidget(title)
        layout.addWidget(desc)
        layout.addWidget(self.lbl_latest)
        layout.addWidget(self.lbl_installed)
        layout.addWidget(self.lbl_status)
        layout.addWidget(self.progress)
        layout.addLayout(btn_row)

        self.refresh()

    def refresh(self):
        self.lbl_latest.setText(f"最新版：{self.tool.latest_version or '-'}")
        self.lbl_installed.setText(f"本機版：{self.tool.installed_version or '未安裝'}")
        self.lbl_status.setText(f"狀態：{self.tool.status_text}")
        self.btn_open.setEnabled(bool(self.tool.installed_path and os.path.exists(self.tool.installed_path)))

