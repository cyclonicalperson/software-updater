import sys
import json
from PyQt6.QtWidgets import (QApplication, QMainWindow, QListWidget, QPushButton,
                             QVBoxLayout, QWidget, QProgressBar, QTextEdit, QHBoxLayout)
from PyQt6.QtCore import QThreadPool, QRunnable
from app_detector import get_installed_apps
from updater import UpdateManager

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
        self.setWindowTitle("Update Manager")
        self.setGeometry(100, 100, 800, 600)
        self.threadpool = QThreadPool()
        self.manager = UpdateManager()

        self.exclusions = load_exclusions()

        self._init_ui()

    def _init_ui(self):
        central_widget = QWidget()
        layout = QVBoxLayout()

        # App list
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

        # Exclusion list
        self.exclusion_list = QListWidget()
        layout.addWidget(self.exclusion_list)

        # Button layout
        btn_layout = QHBoxLayout()

        self.exclude_btn = QPushButton("Exclude Selected")
        self.exclude_btn.clicked.connect(self.exclude_app)
        btn_layout.addWidget(self.exclude_btn)

        self.include_btn = QPushButton("Include Selected")
        self.include_btn.clicked.connect(self.include_app)
        btn_layout.addWidget(self.include_btn)

        layout.addLayout(btn_layout)

        # Progress bar
        self.progress_bar = QProgressBar(self)
        layout.addWidget(self.progress_bar)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)

        # Status box
        self.status_box = QTextEdit(self)
        self.status_box.setReadOnly(True)
        layout.addWidget(self.status_box)

        # Start button
        self.start_btn = QPushButton("Start Update Check")
        self.start_btn.clicked.connect(self.start_update)
        layout.addWidget(self.start_btn)

        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Connect update signals
        self.manager.update_progress.connect(self.update_status)
        self.manager.completed.connect(self.on_complete)

        # Load apps
        self.populate_app_list()
        self.populate_exclusion_list()

    def populate_app_list(self):
        self.list_widget.clear()
        for app in get_installed_apps():
            app_name = app['name']
            if app_name not in self.exclusions:
                self.list_widget.addItem(f"{app_name} v{app['version']}")

    def populate_exclusion_list(self):
        self.exclusion_list.clear()
        for app in self.exclusions:
            self.exclusion_list.addItem(app)

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
        self.status_box.append(message)

    def on_complete(self):
        self.status_box.append("Update process completed.")
        self.statusBar().showMessage("Update process completed")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
