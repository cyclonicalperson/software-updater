import os
import sys
import json
import subprocess
import asyncio
from PyQt6.QtWidgets import (QApplication, QMainWindow, QListWidget, QPushButton,
                             QVBoxLayout, QWidget, QProgressBar, QTextEdit, QHBoxLayout,
                             QGroupBox)
from PyQt6.QtCore import QThreadPool, QRunnable, Qt, QObject, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QIcon, QFont
from app_detector import get_installed_apps
from updater import UpdateManager

# Constants
EXCLUSIONS_DIR = os.path.join(os.getenv("LOCALAPPDATA"), "Software Updater")
EXCLUSIONS_FILE = os.path.join(EXCLUSIONS_DIR, "exclusions.json")

# Ensure the exclusions directory exists
os.makedirs(EXCLUSIONS_DIR, exist_ok=True)


def load_exclusions():
    """Load exclusions from the exclusions.json file in AppData."""
    try:
        with open(EXCLUSIONS_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_exclusions(exclusions):
    """Save exclusions to the exclusions.json file in AppData."""
    with open(EXCLUSIONS_FILE, 'w') as f:
        json.dump(exclusions, f, indent=4)


def check_winget():
    try:
        subprocess.run(["winget", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


class AsyncSignals(QObject):
    finished = pyqtSignal()


class AsyncWorker(QRunnable):
    def __init__(self, async_func, *args):
        super().__init__()
        self.async_func = async_func
        self.args = args
        self.signals = AsyncSignals()

    @pyqtSlot()
    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.async_func(*self.args))
        finally:
            loop.close()
            self.signals.finished.emit()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Software Updater")
        self.setGeometry(100, 100, 600, 600)
        self.setWindowIcon(QIcon("icon.ico"))
        self.threadpool = QThreadPool()
        self.manager = UpdateManager()
        self.exclusions = load_exclusions()
        self._init_ui()

    def _init_ui(self):
        central_widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)  # Consistent spacing
        layout.setSpacing(10)

        # App list group box
        app_list_group = QGroupBox()
        app_list_group.setTitle("Installed Apps")
        app_list_group.setAlignment(Qt.AlignmentFlag.AlignCenter)
        app_list_layout = QVBoxLayout()
        app_list_layout.setSpacing(5)

        self.list_widget = QListWidget()
        self.list_widget.setFont(QFont("Arial", 10))
        app_list_layout.addWidget(self.list_widget)

        app_list_group.setLayout(app_list_layout)
        layout.addWidget(app_list_group)

        # Button layout
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(5)

        self.exclude_btn = QPushButton("Exclude Selected")
        self.exclude_btn.clicked.connect(self.exclude_app)
        self.exclude_btn.setEnabled(False)
        btn_layout.addWidget(self.exclude_btn)

        self.include_btn = QPushButton("Include Selected")
        self.include_btn.clicked.connect(self.include_app)
        self.include_btn.setEnabled(False)
        btn_layout.addWidget(self.include_btn)

        layout.addLayout(btn_layout)

        # Exclusion list group box
        exclusion_list_group = QGroupBox()
        exclusion_list_group.setTitle("Excluded Apps")
        exclusion_list_group.setAlignment(Qt.AlignmentFlag.AlignCenter)
        exclusion_list_layout = QVBoxLayout()
        exclusion_list_layout.setSpacing(5)

        self.exclusion_list = QListWidget()
        self.exclusion_list.setFont(QFont("Arial", 10))  # Clear font
        exclusion_list_layout.addWidget(self.exclusion_list)

        exclusion_list_group.setLayout(exclusion_list_layout)
        layout.addWidget(exclusion_list_group)

        # Start Update Check button
        start_btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start Update Check")
        self.start_btn.clicked.connect(self.start_update)
        self.start_btn.setEnabled(False)
        self.start_btn.setFixedWidth(int(self.width() * 0.5))
        start_btn_layout.addWidget(self.start_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addLayout(start_btn_layout)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # Status box
        self.status_box = QTextEdit()
        self.status_box.setReadOnly(True)
        self.status_box.setFont(QFont("Arial", 10))
        layout.addWidget(self.status_box)

        # Status bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")

        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Connect update signals
        self.manager.update_progress.connect(self.update_status)
        self.manager.update_app_being_processed.connect(self.update_status_bar)

        # Check for winget
        if not check_winget():
            self.status_box.append("<p style='background-color:#FF7F7F; border: 1px solid #8B0000;'>winget not found. Please install it from https://aka.ms/getwinget</p>")

        # Load apps
        self.populate_app_list()
        self.populate_exclusion_list()

        # Connect selection changes
        self.list_widget.itemSelectionChanged.connect(self.update_button_states)
        self.exclusion_list.itemSelectionChanged.connect(self.update_button_states)

    def populate_app_list(self):
        self.list_widget.clear()
        for app in get_installed_apps():
            app_name = app['name']
            if app_name not in self.exclusions:
                self.list_widget.addItem(f"{app_name} v{app['version']}")

        self.update_button_states()

    def populate_exclusion_list(self):
        self.exclusion_list.clear()
        for app in self.exclusions:
            self.exclusion_list.addItem(app)

        self.update_button_states()

    def update_button_states(self):
        self.exclude_btn.setEnabled(self.list_widget.currentItem() is not None)
        self.include_btn.setEnabled(self.exclusion_list.currentItem() is not None)
        self.start_btn.setEnabled(self.list_widget.count() > 0)

    def exclude_app(self):
        selected_item = self.list_widget.currentItem()
        if selected_item:
            app_name = selected_item.text().split(' v')[0]
            if app_name not in self.exclusions:
                self.exclusions.append(app_name)
                save_exclusions(self.exclusions)
                self.populate_exclusion_list()
                self.populate_app_list()

    def include_app(self):
        selected_item = self.exclusion_list.currentItem()
        if selected_item:
            app_name = selected_item.text()
            self.exclusions.remove(app_name)
            save_exclusions(self.exclusions)
            self.populate_exclusion_list()
            self.populate_app_list()

    def start_update(self):
        self.status_box.clear()
        self.progress_bar.setValue(0)
        app_list = [app for app in get_installed_apps() if app['name'] not in self.exclusions]

        # Call async function using QThreadPool
        async_worker = AsyncWorker(self.manager.check_and_install, app_list)
        async_worker.signals.finished.connect(lambda: self.status_bar.showMessage("All updates completed!", 3000))
        self.threadpool.start(async_worker)

    def update_status(self, progress, message):
        self.progress_bar.setValue(progress)
        if "Successfully updated" in message:
            self.status_box.append(f"<p style='background-color:#90EE90; border: 1px solid #008000;'>{message}</p>")
        elif "Could not be updated" in message:
            self.status_box.append(f"<p style='background-color:#FF7F7F; border: 1px solid #8B0000;'>{message}</p>")
        else:
            self.status_box.append(message)

    def update_status_bar(self, message):
        self.status_bar.showMessage(f"Updating {message}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
