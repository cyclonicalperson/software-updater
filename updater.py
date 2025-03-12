import logging
import subprocess
import requests
from PyQt6.QtCore import QObject, pyqtSignal
from typing import Dict, Optional, Union

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class UpdateManager(QObject):
    update_progress = pyqtSignal(int, str)
    completed = pyqtSignal()

    # API endpoints for common applications
    APP_APIS = {
        'chrome': 'https://versioncheck.googleapis.com/v1/chrome/updates',
        'firefox': 'https://product-details.mozilla.org/1.0/firefox_versions.json',
        'vscode': 'https://update.code.visualstudio.com/api/releases/stable',
        'zoom': 'https://zoom.us/rest/v2/download/checkupdate',
        'slack': 'https://slack.com/api/apps.updates',
        'spotify': 'https://api.spotify.com/v1/updates'
    }

    def __init__(self):
        super().__init__()
        self.active = True
        self.handlers = {
            'chrome': self._handle_chrome,
            'firefox': self._handle_firefox,
            'vscode': self._handle_vscode,
            'zoom': self._handle_zoom,
            'slack': self._handle_slack,
            'spotify': self._handle_spotify,
        }

    def check_and_install(self, app_list: Union[Dict, list]):
        """Multithreaded update process with API integration"""
        try:
            # Ensure app_list is always a list
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

                # Process each app and track progress
                update_status = self._process_app(app)
                completed += 1

                # Emit progress and status message
                progress = int((completed / total) * 100)
                self.update_progress.emit(progress, f"{update_status}: {app['name']}")

            # Ensure the progress bar reaches 100% on completion
            self.update_progress.emit(100, "Update process completed.")
            self.completed.emit()

        except Exception as e:
            logging.error(f"System error during update: {e}", exc_info=True)
            self.update_progress.emit(-1, f"System Error: {str(e)}")

    def _is_valid_app(self, app):
        """Validate if the app has the required structure"""
        if not isinstance(app, dict):
            return False
        required_keys = {'name', 'version', 'ident'}
        return required_keys.issubset(app.keys())

    def _process_app(self, app) -> str:
        try:
            handler = self._get_handler(app.get('name', '').lower())
            if handler:
                logging.info(f"Updating {app['name']} using a specific handler.")
                handler(app)
            else:
                logging.info(f"Updating {app['name']} using winget fallback.")
                self._generic_winget_update(app)
            return "Successfully updated"
        except subprocess.CalledProcessError:
            logging.error(f"No available update for {app['name']}")
            return "No available update"
        except Exception as e:
            logging.error(f"Error processing {app}: {e}", exc_info=True)
            return "Could not be updated"

    def _get_handler(self, app_name: str) -> Optional[callable]:
        """Get specialized handler for known applications"""
        for key in self.handlers:
            if key in app_name:
                return self.handlers[key]
        return None

    def _safe_api_call(self, url):
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logging.error(f"API call to {url} failed: {e}", exc_info=True)
            return {}

    # Specialized handlers for common apps
    def _handle_chrome(self, app: Dict):
        data = self._safe_api_call(self.APP_APIS['chrome'])
        latest = data.get('current_version')
        if latest and app['version'] != latest:
            logging.info(f"Updating Chrome from {app['version']} to {latest}")
            subprocess.run('winget upgrade Google.Chrome --silent', shell=True, check=True)

    def _handle_firefox(self, app: Dict):
        data = self._safe_api_call(self.APP_APIS['firefox'])
        latest = data.get('LATEST_FIREFOX_VERSION')
        if latest and app['version'] != latest:
            logging.info(f"Updating Firefox from {app['version']} to {latest}")
            subprocess.run('winget upgrade Mozilla.Firefox --silent', shell=True, check=True)

    def _handle_vscode(self, app: Dict):
        data = self._safe_api_call(self.APP_APIS['vscode'])
        if isinstance(data, list) and data:
            latest = data[0].get('version')
            if latest and app['version'] != latest:
                logging.info(f"Updating VSCode from {app['version']} to {latest}")
                subprocess.run('winget upgrade Microsoft.VisualStudioCode --silent', shell=True, check=True)

    def _handle_zoom(self, app: Dict):
        data = self._safe_api_call(self.APP_APIS['zoom'])
        latest = data.get('latest_version')
        if latest and app['version'] != latest:
            logging.info(f"Updating Zoom from {app['version']} to {latest}")
            subprocess.run('winget upgrade Zoom.Zoom --silent', shell=True, check=True)

    def _handle_slack(self, app: Dict):
        logging.info(f"Checking Slack for updates.")

    def _handle_spotify(self, app: Dict):
        logging.info(f"Checking Spotify for updates.")

    def _generic_winget_update(self, app: Dict):
        """Fallback to winget for unknown apps"""
        logging.info(f"Performing generic winget update for {app.get('name', 'unknown')}.")

        # Try updating by name
        subprocess.run(f'winget upgrade --name "{app.get("name", "")}" --silent', shell=True, check=True)

        # If that fails, try updating by id
        subprocess.run(f'winget upgrade --id "{app.get("ident", "")}" --silent', shell=True, check=True)
