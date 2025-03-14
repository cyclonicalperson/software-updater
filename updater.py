import json
import logging
import subprocess
import threading
from PyQt6.QtCore import QObject, pyqtSignal
from typing import Dict, Optional, Union
from app_endpoints import get_latest_version

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

EXCLUSIONS_FILE = "exclusions.json"


def load_exclusions():
    """Load exclusions from the exclusions.json file."""
    try:
        with open(EXCLUSIONS_FILE, 'r') as f:
            return json.load(f)  # List of app names to exclude
    except (FileNotFoundError, json.JSONDecodeError):
        return []  # Return an empty list if the file is not found or is invalid


class UpdateManager(QObject):
    update_progress = pyqtSignal(int, str)
    completed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.active = True

        # Automatically map handlers for all known apps
        self.handlers = {app: self.handle_common_app for app in get_latest_version.__globals__['APP_APIS'].keys()}

    def check_and_install(self, app_list: Union[Dict, list]):
        """Main update process with progress tracking and timeouts."""
        try:
            exclusions = load_exclusions()

            if isinstance(app_list, dict):
                app_list = [app_list]

            total = len(app_list)
            completed = 0

            def process_app_thread(app):
                nonlocal completed
                if not self.is_valid_app(app):
                    logging.error(f"Invalid app format: {app}")
                    return
                if not self.active:
                    return

                if app['name'] in exclusions:
                    update_status = f"Update skipped: {app['name']}"
                else:
                    update_status = self.process_app(app)

                completed += 1
                progress = int((completed / total) * 100)
                self.update_progress.emit(progress, f"{update_status}: {app['name']}")

                if completed == total:
                    self.update_progress.emit(100, "Update process completed.")
                    self.completed.emit()

            threads = [threading.Thread(target=process_app_thread, args=(app,)) for app in app_list]

            for thread in threads:
                thread.start()

            for thread in threads:
                thread.join()

        except Exception as e:
            logging.error(f"System error during update: {e}", exc_info=True)
            self.update_progress.emit(-1, f"System Error: {str(e)}")

    def is_valid_app(self, app):
        """Validate app structure."""
        required_keys = {'name', 'version', 'ident'}
        return isinstance(app, dict) and required_keys.issubset(app.keys())

    def process_app(self, app) -> str:
        """Handle each app update."""
        try:
            handler = self.get_handler(app.get('name', '').lower())
            if handler:
                logging.info(f"Updating {app['name']} using specialized handler.")
                return "Successfully updated" if handler(app) else "No available update"

            logging.info(f"Updating {app['name']} using winget.")
            updated = self.winget_update(app)
            return "Successfully updated" if updated else "No available update"

        except Exception as e:
            logging.error(f"Error processing {app}: {e}", exc_info=True)
            return "Could not be updated"

    def get_handler(self, app_name: str) -> Optional[callable]:
        """Get a specialized handler for known applications."""
        return self.handlers.get(app_name)

    def handle_common_app(self, app: Dict) -> bool:
        """Generic handler for all known apps in APP_APIS."""
        app_name = app['name'].lower()

        latest = get_latest_version(app_name)
        if latest and app['version'] != latest:
            logging.info(f"Updating {app['name']} from {app['version']} to {latest}")
            return self.run_update_command(f'winget upgrade --name "{app["name"]}" --silent')
        return False

    def winget_update(self, app: Dict) -> bool:
        """Fallback to winget for unknown apps."""
        for option in ['--name', '--id']:
            try:
                result = subprocess.run(
                    f'winget upgrade {option} "{app.get("name" if option == "--name" else "ident", "")}" --silent',
                    shell=True,
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=30
                )
                if "No installed package" in result.stdout or "No available upgrade" in result.stdout:
                    continue
                return True
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                logging.warning(f"Failed using {option} for {app.get('name', 'unknown')}.")

        return False

    def run_update_command(self, command: str) -> bool:
        """Execute a shell command to run updates."""
        try:
            result = subprocess.run(
                command,
                shell=True,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=30
            )
            if "No installed package" in result.stdout or "No available upgrade" in result.stdout:
                return False
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            logging.warning(f"Command timed out or failed: {command}")
            return False
