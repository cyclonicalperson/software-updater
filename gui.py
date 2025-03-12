import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QListWidget, QPushButton, QVBoxLayout, QWidget, QProgressBar
from PyQt6.QtCore import QThreadPool, QRunnable
from app_detector import get_installed_apps
from updater import UpdateManager


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Update Manager")
        self.setGeometry(100, 100, 800, 600)
        # self.setWindowIcon(QIcon("icon.ico"))  ADD ICON
        self.threadpool = QThreadPool()
        self.manager = UpdateManager()
        self._init_ui()

    def _init_ui(self):
        central_widget = QWidget()
        layout = QVBoxLayout()

        # List of detected apps
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

        # Progress bar for translation progress
        self.progress_bar = QProgressBar(self)
        layout.addWidget(self.progress_bar)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.show()

        # Update check start button
        self.start_btn = QPushButton("Start Update Check")
        layout.addWidget(self.start_btn)

        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Connect signals
        self.start_btn.clicked.connect(self.start_update)
        self.manager.update_progress.connect(self.update_status)
        self.manager.completed.connect(self.on_complete)

        # Find installed apps
        self.populate_app_list()

    def populate_app_list(self):
        """Add all detected apps to the list."""
        self.list_widget.clear()
        for app in get_installed_apps():
            self.list_widget.addItem(f"{app['name']} v{app['version']}")

    def start_update(self):
        """Update all detected apps."""
        worker = QRunnable.create(self.manager.check_and_install, get_installed_apps())
        self.threadpool.start(worker)

    def update_status(self, progress, message):
        """Update the progress bar with the current progress."""
        self.progress_bar.setValue(progress)
        self.statusBar().showMessage(message)

    def on_complete(self):
        self.statusBar().showMessage("Update process completed")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
