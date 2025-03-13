import logging
import subprocess
from PyQt6.QtCore import QObject, pyqtSignal
from typing import Dict, Optional, Union
from app_endpoints import get_latest_version

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class UpdateManager(QObject):
    update_progress = pyqtSignal(int, str)
    completed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.active = True
        self.handlers = {
            'chrome': self._handle_common_app,
            'firefox': self._handle_common_app,
            'vscode': self._handle_common_app,
            'zoom': self._handle_common_app,
            'slack': self._handle_common_app,
            'spotify': self._handle_common_app,
        }

    def check_and_install(self, app_list: Union[Dict, list]):
        """Main update process with progress tracking and timeouts."""
        try:
            if isinstance(app_list, dict):
                app_list = [app_list]

            logging.info(f"Received app list: {app_list}")
            total = len(app_list)
            completed = 0

            for app in app_list:
                if not self._is_valid_app(app):
                    logging.error(f"Invalid app format: {app}")
                    continue
                if not self.active:
                    break

                update_status = self._process_app(app)
                completed += 1

                progress = int((completed / total) * 100)
                self.update_progress.emit(progress, f"{update_status}: {app['name']}")

            # Ensure the progress bar reaches 100% once all updates are done
            self.update_progress.emit(100, "Update process completed.")
            self.completed.emit()

        except Exception as e:
            logging.error(f"System error during update: {e}", exc_info=True)
            self.update_progress.emit(-1, f"System Error: {str(e)}")

    def _is_valid_app(self, app):
        """Validate app structure."""
        if not isinstance(app, dict):
            return False
        required_keys = {'name', 'version', 'ident'}
        return required_keys.issubset(app.keys())

    def _process_app(self, app) -> str:
        """Handle each app update."""
        try:
            handler = self._get_handler(app.get('name', '').lower())
            if handler:
                logging.info(f"Updating {app['name']} using specialized handler.")
                return "Successfully updated" if handler(app) else "No available update"

            logging.info(f"Updating {app['name']} using winget fallback.")
            updated = self._generic_winget_update(app)
            return "Successfully updated" if updated else "No available update"

        except Exception as e:
            logging.error(f"Error processing {app}: {e}", exc_info=True)
            return "Could not be updated"

    def _get_handler(self, app_name: str) -> Optional[callable]:
        """Get a specialized handler for known applications."""
        for key in self.handlers:
            if key in app_name:
                return self.handlers[key]
        return None

    def _handle_common_app(self, app: Dict) -> bool:
        """
        Generic handler for apps like Chrome, Firefox, VSCode, Zoom.
        Uses app_endpoints.py to fetch the latest version.
        """
        app_name = app['name'].lower()
        known_keys = {'chrome', 'firefox', 'vscode', 'zoom', 'slack', 'spotify'}

        for key in known_keys:
            if key in app_name:
                latest = get_latest_version(key)
                if latest and app['version'] != latest:
                    logging.info(f"Updating {app['name']} from {app['version']} to {latest}")
                    return self._run_update_command(f'winget upgrade --name "{app["name"]}" --silent')
        return False

    def _generic_winget_update(self, app: Dict) -> bool:
        """Fallback to winget for unknown apps."""
        logging.info(f"Attempting winget update for {app.get('name', 'unknown')}.")

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

    def _run_update_command(self, command: str) -> bool:
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
