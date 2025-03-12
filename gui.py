import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QListWidget, QPushButton, QVBoxLayout, QWidget, QProgressBar, QTextEdit
from PyQt6.QtCore import QThreadPool, QRunnable
from app_detector import get_installed_apps
from updater import UpdateManager


class UpdateWorker(QRunnable):
    def __init__(self, manager, app_list):
        super().__init__()
        self.manager = manager
        self.app_list = app_list

    def run(self):
        """Run the update task in a separate thread."""
        self.manager.check_and_install(self.app_list)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Update Manager")
        self.setGeometry(100, 100, 800, 600)
        self.threadpool = QThreadPool()
        self.manager = UpdateManager()
        self._init_ui()

    def _init_ui(self):
        central_widget = QWidget()
        layout = QVBoxLayout()

        # List of detected apps
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

        # Progress bar for update progress
        self.progress_bar = QProgressBar(self)
        layout.addWidget(self.progress_bar)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)

        # Status box for update messages
        self.status_box = QTextEdit(self)
        self.status_box.setReadOnly(True)  # Make it read-only
        layout.addWidget(self.status_box)

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
        app_list = get_installed_apps()

        # Clear status box for new run
        self.status_box.clear()

        # Create a worker task and start it in the thread pool
        worker = UpdateWorker(self.manager, app_list)
        self.threadpool.start(worker)

    def update_status(self, progress, message):
        """Update the progress bar and status box with the current progress."""
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
