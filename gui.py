import sys
import json
import subprocess
from PyQt6.QtWidgets import (QApplication, QMainWindow, QListWidget, QPushButton,
                             QVBoxLayout, QWidget, QProgressBar, QTextEdit, QHBoxLayout,
                             QGroupBox)
from PyQt6.QtCore import QThreadPool, QRunnable, Qt
from PyQt6.QtGui import QIcon, QFont
from app_detector import get_installed_apps
from updater import UpdateManager

# Constants
EXCLUSIONS_FILE = "exclusions.json"


def load_exclusions():
    try:
        with open(EXCLUSIONS_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_exclusions(exclusions):
    with open(EXCLUSIONS_FILE, 'w') as f:
        json.dump(exclusions, f)


def check_winget():
    try:
        subprocess.run(["winget", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


class UpdateWorker(QRunnable):
    def __init__(self, manager, app_list):
        super().__init__()
        self.manager = manager
        self.app_list = app_list

    def run(self):
        self.manager.check_and_install(self.app_list)


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
        start_btn_layout.addStretch()  # Stretch before button
        self.start_btn = QPushButton("Start Update Check")
        self.start_btn.clicked.connect(self.start_update)
        self.start_btn.setEnabled(False)  # Initially disabled
        self.start_btn.setFixedWidth(int(self.width() * 0.5))  # Set button width to 50% of GUI width
        start_btn_layout.addWidget(self.start_btn, alignment=Qt.AlignmentFlag.AlignCenter)  # Center the button
        start_btn_layout.addStretch()  # Stretch after button
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
        self.status_box.setFont(QFont("Arial", 10))  # Clear font
        layout.addWidget(self.status_box)

        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Connect update signals
        self.manager.update_progress.connect(self.update_status)
        self.manager.completed.connect(self.on_complete)

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

        app_list = [app for app in get_installed_apps() if app['name'] not in self.exclusions]

        worker = UpdateWorker(self.manager, app_list)
        self.threadpool.start(worker)

    def update_status(self, progress, message):
        self.progress_bar.setValue(progress)
        if "Successfully updated" in message:
            self.status_box.append(f"<p style='background-color:#90EE90; border: 1px solid #008000;'>{message}</p>")
        elif "Could not be updated" in message:
            self.status_box.append(f"<p style='background-color:#FF7F7F; border: 1px solid #8B0000;'>{message}</p>")
        else:
            self.status_box.append(message)

    def on_complete(self):
        self.status_box.append("Update process completed.")
        self.statusBar().showMessage("Update process completed")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())