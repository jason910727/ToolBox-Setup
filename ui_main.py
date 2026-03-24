#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# ui_main.py
import os

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QListWidget, QListWidgetItem, QStackedWidget,
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextBrowser, QScrollArea,
    QGridLayout, QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QProgressBar, QFileDialog
)

from widgets import ToolCard
from utils import open_path, open_url, run_exe, compare_versions, format_install_subdir
from updater import DownloadWorker
from api import fetch_manifest, github_latest_release
from cache import save_cache
from models import ToolItem
from config import CACHE_FILE


class MainWindow(QMainWindow):
    def __init__(self, app_title, tools, install_dir, manifest, manifest_url):
        super().__init__()
        self.app_title = app_title
        self.tools = tools
        self.install_dir = install_dir
        self.manifest = manifest
        # self.settings = settings
        self.manifest_url = manifest_url

        self.download_workers = []
        self.tool_cards = {}

        self.setWindowTitle(app_title)
        self._build_ui()
        self._apply_styles()
        self._load_data_to_ui()

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)

        main_layout = QHBoxLayout(root)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        self.nav = QListWidget()
        self.nav.setFixedWidth(190)
        for text in ["首頁", "工具清單", "更新中心", "公告", "設定"]:
            QListWidgetItem(text, self.nav)

        self.stack = QStackedWidget()
        self.nav.currentRowChanged.connect(self.stack.setCurrentIndex)

        main_layout.addWidget(self.nav)
        main_layout.addWidget(self.stack, 1)

        self.page_home = self._create_home_page()
        self.page_tools = self._create_tools_page()
        self.page_updates = self._create_updates_page()
        self.page_ann = self._create_announcement_page()
        self.page_settings = self._create_settings_page()

        self.stack.addWidget(self.page_home)
        self.stack.addWidget(self.page_tools)
        self.stack.addWidget(self.page_updates)
        self.stack.addWidget(self.page_ann)
        self.stack.addWidget(self.page_settings)

        self.nav.setCurrentRow(0)
    def reload_from_remote(self):
        new_manifest = fetch_manifest(self.manifest_url)
        if not new_manifest:
            QMessageBox.warning(self, "錯誤", "無法重新抓取遠端 manifest。")
            return

        self.manifest = new_manifest
        save_cache(CACHE_FILE, new_manifest)

        self.reload_tools_from_manifest()
        self._load_data_to_ui()
        QMessageBox.information(self, "完成", "已重新載入遠端資料。")

    def reload_tools_from_manifest(self):
        new_tools = []

        for item in self.manifest.get("tools", []):
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

                for a in assets:
                    asset_name = a.get("name", "")
                    if asset_name.lower() == tool.exe_name.lower():
                        tool.latest_download_url = a.get("browser_download_url", "")
                        break

                if not tool.latest_download_url:
                    for a in assets:
                        asset_name = a.get("name", "")
                        if asset_name.lower().endswith(".exe"):
                            tool.latest_download_url = a.get("browser_download_url", "")
                            break

                if not tool.latest_download_url and assets:
                    tool.latest_download_url = assets[0].get("browser_download_url", "")

            except Exception:
                tool.latest_version = ""
                tool.latest_download_url = ""

            old_tool = next((t for t in self.tools if t.name == tool.name), None)
            if old_tool:
                tool.installed_version = old_tool.installed_version
                tool.installed_path = old_tool.installed_path
                tool.status_text = old_tool.status_text

            new_tools.append(tool)

        self.tools = new_tools

    def _apply_styles(self):
        self.setStyleSheet("""
        QWidget {
            background: #F7FBFF;
            color: #1F2D3D;
            font-size: 13px;
        }
        QListWidget {
            background: #FFFFFF;
            border: 1px solid #D5E6F7;
            border-radius: 12px;
            padding: 8px;
        }
        QListWidget::item {
            padding: 12px 10px;
            border-radius: 8px;
        }
        QListWidget::item:selected {
            background: #D9ECFF;
            color: #103A5D;
            font-weight: bold;
        }
        QTableWidget, QTextBrowser, QScrollArea {
            background: #FFFFFF;
            border: 1px solid #D5E6F7;
            border-radius: 12px;
        }
        QPushButton {
            background: #D9ECFF;
            border: 1px solid #B8D8F3;
            border-radius: 10px;
            padding: 8px 14px;
            font-weight: 600;
        }
        QPushButton:hover {
            background: #CBE4FF;
        }
        QPushButton:disabled {
            background: #EEF5FB;
            color: #95A5B2;
        }
        #ToolCard {
            background: #FFFFFF;
            border: 1px solid #D5E6F7;
            border-radius: 16px;
            padding: 10px;
        }
        QHeaderView::section {
            background: #EAF4FF;
            border: none;
            padding: 8px;
            font-weight: bold;
        }
        """)

    def _create_home_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        title = QLabel(f"<h2>{self.app_title}</h2>")
        subtitle = QLabel("工具下載、版本管理、教學與公告中心")

        topbar = QHBoxLayout()
        self.btn_refresh = QPushButton("重新整理")
        self.btn_update_all = QPushButton("更新全部")
        self.btn_open_install_dir = QPushButton("開啟下載資料夾")

        self.btn_refresh.clicked.connect(self.reload_from_remote)
        self.btn_update_all.clicked.connect(self.update_all_tools)
        self.btn_open_install_dir.clicked.connect(lambda: open_path(self.install_dir))

        topbar.addWidget(self.btn_refresh)
        topbar.addWidget(self.btn_update_all)
        topbar.addWidget(self.btn_open_install_dir)
        topbar.addStretch(1)

        self.home_scroll = QScrollArea()
        self.home_scroll.setWidgetResizable(True)

        container = QWidget()
        self.home_grid = QGridLayout(container)
        self.home_grid.setSpacing(12)

        self.home_scroll.setWidget(container)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addLayout(topbar)
        layout.addWidget(self.home_scroll, 1)
        return page

    def _create_tools_page(self):
        page = QWidget()
        layout = QHBoxLayout(page)

        self.tbl_tools = QTableWidget(0, 5)
        self.tbl_tools.setHorizontalHeaderLabels(["工具", "最新版", "本機版", "狀態", "路徑"])
        self.tbl_tools.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_tools.setSelectionBehavior(self.tbl_tools.SelectRows)
        self.tbl_tools.itemSelectionChanged.connect(self.on_tool_table_selected)

        right = QVBoxLayout()
        self.lbl_detail_title = QLabel("<h3>工具詳細資訊</h3>")
        self.txt_detail = QTextBrowser()

        btn_row = QHBoxLayout()
        self.btn_detail_open = QPushButton("開啟程式")
        self.btn_detail_update = QPushButton("下載 / 更新")
        self.btn_detail_tutorial = QPushButton("開啟教學")
        self.btn_detail_homepage = QPushButton("GitHub")

        self.btn_detail_open.clicked.connect(self.detail_open)
        self.btn_detail_update.clicked.connect(self.detail_update)
        self.btn_detail_tutorial.clicked.connect(self.detail_tutorial)
        self.btn_detail_homepage.clicked.connect(self.detail_homepage)

        btn_row.addWidget(self.btn_detail_open)
        btn_row.addWidget(self.btn_detail_update)
        btn_row.addWidget(self.btn_detail_tutorial)
        btn_row.addWidget(self.btn_detail_homepage)

        right.addWidget(self.lbl_detail_title)
        right.addWidget(self.txt_detail, 1)
        right.addLayout(btn_row)

        layout.addWidget(self.tbl_tools, 3)
        layout.addLayout(right, 2)
        return page

    def _create_updates_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        self.tbl_updates = QTableWidget(0, 4)
        self.tbl_updates.setHorizontalHeaderLabels(["工具", "本機版", "最新版", "可更新"])
        self.tbl_updates.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.global_progress = QProgressBar()
        self.global_progress.setValue(0)

        self.btn_updates_selected = QPushButton("更新所有可更新項目")
        self.btn_updates_selected.clicked.connect(self.update_all_tools)

        layout.addWidget(QLabel("<h3>更新中心</h3>"))
        layout.addWidget(self.tbl_updates)
        layout.addWidget(self.global_progress)
        layout.addWidget(self.btn_updates_selected)
        return page

    def _create_announcement_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel("<h3>公告</h3>"))

        self.txt_announcement = QTextBrowser()
        layout.addWidget(self.txt_announcement)
        return page

    def _create_settings_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        layout.addWidget(QLabel("<h3>設定</h3>"))

        row = QHBoxLayout()
        self.lbl_install_dir = QLabel(f"下載資料夾：{self.install_dir}")
        self.btn_pick_install_dir = QPushButton("變更下載資料夾")
        self.btn_pick_install_dir.clicked.connect(self.pick_install_dir)

        row.addWidget(self.lbl_install_dir, 1)
        row.addWidget(self.btn_pick_install_dir)
        layout.addLayout(row)
        layout.addStretch(1)
        return page

    def _load_data_to_ui(self):
        self._fill_cards()
        self._fill_tool_table()
        self._fill_update_table()

        ann_html = self.manifest.get("announcement_html", "")
        print("UI announcement_html =", ann_html)
        self.txt_announcement.setHtml(ann_html or "<h3>目前沒有公告</h3>")

    def _fill_cards(self):
        for i in reversed(range(self.home_grid.count())):
            item = self.home_grid.itemAt(i)
            w = item.widget()
            if w:
                w.deleteLater()

        self.tool_cards.clear()
        row = 0
        col = 0

        for tool in self.tools:
            if not tool.enabled:
                continue

            card = ToolCard(tool)
            card.request_open.connect(self.handle_open_tool)
            card.request_update.connect(self.handle_update_tool)
            card.request_detail.connect(self.handle_detail_tool)
            card.request_tutorial.connect(self.handle_tutorial_tool)

            self.tool_cards[tool.name] = card
            self.home_grid.addWidget(card, row, col)

            col += 1
            if col >= 2:
                col = 0
                row += 1

    def _fill_tool_table(self):
        self.tbl_tools.setRowCount(0)
        for tool in self.tools:
            r = self.tbl_tools.rowCount()
            self.tbl_tools.insertRow(r)
            self.tbl_tools.setItem(r, 0, QTableWidgetItem(tool.name))
            self.tbl_tools.setItem(r, 1, QTableWidgetItem(tool.latest_version or "-"))
            self.tbl_tools.setItem(r, 2, QTableWidgetItem(tool.installed_version or "未安裝"))
            self.tbl_tools.setItem(r, 3, QTableWidgetItem(tool.status_text))
            self.tbl_tools.setItem(r, 4, QTableWidgetItem(tool.installed_path or ""))

        if self.tbl_tools.rowCount() > 0:
            self.tbl_tools.selectRow(0)

    def _fill_update_table(self):
        self.tbl_updates.setRowCount(0)
        for tool in self.tools:
            need = self.tool_need_update(tool)
            r = self.tbl_updates.rowCount()
            self.tbl_updates.insertRow(r)
            self.tbl_updates.setItem(r, 0, QTableWidgetItem(tool.name))
            self.tbl_updates.setItem(r, 1, QTableWidgetItem(tool.installed_version or "未安裝"))
            self.tbl_updates.setItem(r, 2, QTableWidgetItem(tool.latest_version or "-"))
            self.tbl_updates.setItem(r, 3, QTableWidgetItem("是" if need else "否"))

        self.global_progress.setValue(0)

    def current_selected_tool(self):
        row = self.tbl_tools.currentRow()
        if row < 0:
            return None
        name = self.tbl_tools.item(row, 0).text()
        for t in self.tools:
            if t.name == name:
                return t
        return None

    def on_tool_table_selected(self):
        tool = self.current_selected_tool()
        if not tool:
            return

        self.lbl_detail_title.setText(f"<h3>{tool.name}</h3>")
        html = f"""
        <b>工具名稱：</b>{tool.name}<br>
        <b>描述：</b>{tool.description or '尚未填寫'}<br>
        <b>最新版：</b>{tool.latest_version or '-'}<br>
        <b>本機版：</b>{tool.installed_version or '未安裝'}<br>
        <b>狀態：</b>{tool.status_text}<br>
        <b>安裝路徑：</b>{tool.installed_path or '-'}<br>
        <b>教學連結：</b>{tool.tutorial_url or '尚未填寫'}<br>
        <b>GitHub：</b>{tool.homepage_url or '-'}<br>
        """
        self.txt_detail.setHtml(html)

    def detail_open(self):
        tool = self.current_selected_tool()
        if tool:
            self.handle_open_tool(tool)

    def detail_update(self):
        tool = self.current_selected_tool()
        if tool:
            self.handle_update_tool(tool)

    def detail_tutorial(self):
        tool = self.current_selected_tool()
        if tool:
            self.handle_tutorial_tool(tool)

    def detail_homepage(self):
        tool = self.current_selected_tool()
        if tool and tool.homepage_url:
            open_url(tool.homepage_url)

    def pick_install_dir(self):
        folder = QFileDialog.getExistingDirectory(self, "選擇下載資料夾", self.install_dir)
        if folder:
            self.install_dir = folder
            self.lbl_install_dir.setText(f"下載資料夾：{self.install_dir}")
            self.refresh_cards()

    def tool_need_update(self, tool):
        if not tool.latest_version:
            return False
        if not tool.installed_version:
            return True
        return compare_versions(tool.latest_version, tool.installed_version) == 1

    def refresh_cards(self):
        for tool in self.tools:
            if self.tool_need_update(tool):
                tool.status_text = "可更新"
            elif tool.installed_version:
                tool.status_text = "已安裝"
            else:
                tool.status_text = "未安裝"

        for _, card in self.tool_cards.items():
            card.refresh()

        self._fill_tool_table()
        self._fill_update_table()
        self.on_tool_table_selected()

    def handle_open_tool(self, tool):
        if tool.installed_path and os.path.exists(tool.installed_path):
            run_exe(tool.installed_path)
        else:
            QMessageBox.information(self, "提示", f"{tool.name} 尚未安裝。")

    def handle_tutorial_tool(self, tool):
        if tool.tutorial_url:
            open_url(tool.tutorial_url)
        else:
            QMessageBox.information(self, "提示", "目前還沒有教學連結，之後補上即可。")

    def handle_detail_tool(self, tool):
        self.nav.setCurrentRow(1)
        for i in range(self.tbl_tools.rowCount()):
            if self.tbl_tools.item(i, 0).text() == tool.name:
                self.tbl_tools.selectRow(i)
                break

    def handle_update_tool(self, tool):
        if not tool.latest_download_url:
            QMessageBox.warning(self, "錯誤", f"{tool.name} 找不到下載連結。")
            return

        subdir = format_install_subdir(tool.install_subdir, tool.latest_version, tool.name)
        save_dir = os.path.join(self.install_dir, subdir)
        save_path = os.path.join(save_dir, tool.exe_name)

        worker = DownloadWorker(tool.latest_download_url, save_path)
        self.download_workers.append(worker)

        card = self.tool_cards.get(tool.name)
        if card:
            card.progress.setVisible(True)
            card.progress.setValue(0)

        worker.progress_changed.connect(lambda v, c=card: c.progress.setValue(v) if c else None)
        worker.status_changed.connect(lambda msg, t=tool: self.statusBar().showMessage(f"{t.name}: {msg}"))
        worker.finished_ok.connect(lambda path, t=tool, c=card: self.on_download_finished(t, path, c))
        worker.failed.connect(lambda err, t=tool, c=card: self.on_download_failed(t, err, c))
        worker.start()

    def on_download_finished(self, tool, path, card):
        tool.installed_path = path
        tool.installed_version = tool.latest_version
        tool.status_text = "已安裝"
        if card:
            card.progress.setValue(100)
        self.refresh_cards()
        QMessageBox.information(self, "完成", f"{tool.name} 下載完成。")

    def on_download_failed(self, tool, err, card):
        if card:
            card.progress.setVisible(False)
        QMessageBox.warning(self, "下載失敗", f"{tool.name} 下載失敗：\n{err}")

    def update_all_tools(self):
        update_list = [t for t in self.tools if self.tool_need_update(t)]
        if not update_list:
            QMessageBox.information(self, "提示", "目前全部都是最新版本。")
            return

        total = len(update_list)
        done = {"count": 0}

        def one_done():
            done["count"] += 1
            self.global_progress.setValue(int(done["count"] * 100 / total))

        for tool in update_list:
            subdir = format_install_subdir(tool.install_subdir, tool.latest_version, tool.name)
            save_dir = os.path.join(self.install_dir, subdir)
            save_path = os.path.join(save_dir, tool.exe_name)

            worker = DownloadWorker(tool.latest_download_url, save_path)
            self.download_workers.append(worker)
            worker.finished_ok.connect(lambda path, t=tool: self._update_done_apply(t, path))
            worker.finished_ok.connect(lambda _: one_done())
            worker.failed.connect(lambda err, t=tool: self.statusBar().showMessage(f"{t.name} 失敗：{err}"))
            worker.failed.connect(lambda _: one_done())
            worker.start()

    def _update_done_apply(self, tool, path):
        tool.installed_path = path
        tool.installed_version = tool.latest_version
        tool.status_text = "已安裝"
        self.refresh_cards()

