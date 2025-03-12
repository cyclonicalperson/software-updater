import subprocess
from PyQt6.QtCore import QObject, pyqtSignal


class UpdateManager(QObject):
    update_progress = pyqtSignal(int, str)
    completed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.active = True

    def check_and_install(self, app_list):
        """Multithreaded update process using winget CLI"""
        try:
            for idx, app in enumerate(app_list):
                if not self.active: break
                self._process_app(app, idx + 1, len(app_list))
            self.completed.emit()
        except Exception as e:
            self.update_progress.emit(-1, f"Error: {str(e)}")

    def _process_app(self, app, current, total):
        progress = int((current / total) * 100)
        try:
            result = subprocess.run(
                f'winget upgrade --id {app["ident"]}',
                capture_output=True,
                text=True,
                shell=True
            )
            if "Available" in result.stdout:
                self._install_update(app["ident"], progress)
            else:
                self.update_progress.emit(progress, f"{app['name']} up-to-date")
        except subprocess.CalledProcessError as e:
            self.update_progress.emit(progress, f"Failed to check {app['name']}")
