"""THIS FILE IS NO LONGER USED AS OF v2.0"""


import json
import logging
import os
import subprocess
import asyncio
from PyQt6.QtCore import QObject, pyqtSignal
from app_endpoints import get_latest_version

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
    try:
        with open(EXCLUSIONS_FILE, 'w') as f:
            json.dump(exclusions, f, indent=4)
    except Exception as e:
        logging.error(f"Failed to save exclusions: {e}")


class UpdateManager(QObject):
    update_progress = pyqtSignal(int, str)
    update_app_being_processed = pyqtSignal(str)
    completed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.active = True
        self.handlers = {app: self.handle_common_app for app in get_latest_version.__globals__['APP_APIS'].keys()}
        self.completed_count = 0  # Initialize count of completed updates
        self.lock = asyncio.Lock()  # Add a lock for shared variables
        self.semaphore = asyncio.Semaphore(2)  # Limit to 2 concurrent updates
        self.total_apps = 0  # Total number of apps to update

    async def check_and_install(self, app_list):
        """Main update process with progress tracking and concurrency control."""
        try:
            exclusions = load_exclusions()
            if isinstance(app_list, dict):
                app_list = [app_list]

            filtered_app_list = [app for app in app_list
                                 if app['name'] not in exclusions and self.is_valid_app(app)]
            self.total_apps = len(filtered_app_list)
            self.completed_count = 0  # Reset completed count
            logging.info(f"Total apps to update: {self.total_apps}")

            if not filtered_app_list:
                self.update_progress.emit(100, "No updates available.")
                self.completed.emit()
                return

            tasks = [
                self.run_with_semaphore(self.process_app_and_update_status, app)
                for app in filtered_app_list
            ]

            # Run all tasks concurrently but limited by the semaphore
            await asyncio.gather(*tasks)

            # Ensure completion signal is emitted when all tasks are done
            if self.completed_count >= self.total_apps:
                self.update_progress.emit(100, "Update process completed.")
                self.completed.emit()
            else:
                logging.warning(f"Completed {self.completed_count} out of {self.total_apps} updates.")
                self.update_progress.emit(int((self.completed_count / self.total_apps) * 100),
                                            "Update process finished with possible errors.")
                self.completed.emit()

        except Exception as e:
            logging.error(f"System error during update: {e}", exc_info=True)
            self.update_progress.emit(-1, f"System Error: {str(e)}")
            self.completed.emit()  # Ensure completion signal is always emitted

    async def run_with_semaphore(self, func, app):
        """Run a task with semaphore control."""
        async with self.semaphore:
            return await func(app)

    async def process_app_and_update_status(self, app):
        """Process an app and update the progress."""
        try:
            self.update_app_being_processed.emit(app['name'])
            update_status = await self.process_app(app)

            async with self.lock:  # Lock for shared variable updates
                self.completed_count += 1
                progress = int((self.completed_count / self.total_apps) * 100) if self.total_apps > 0 else 100
                self.update_progress.emit(progress, f"{update_status}: {app['name']}")

        except Exception as e:
            logging.error(f"Error processing {app}: {e}", exc_info=True)

    def is_valid_app(self, app):
        """Validate app structure."""
        required_keys = {'name', 'version', 'ident'}
        return isinstance(app, dict) and required_keys.issubset(app.keys())

    async def process_app(self, app):
        """Handle each app update."""
        try:
            handler = self.get_handler(app.get('name', '').lower())
            if handler:
                logging.info(f"Updating {app['name']} using specialized handler.")
                return "Successfully updated" if handler(app) else "No available update"

            logging.info(f"Updating {app['name']} using winget.")
            updated = await self.winget_update(app)
            return "Successfully updated" if updated else "No available update"

        except Exception as e:
            logging.error(f"Error processing {app}: {e}", exc_info=True)
            return "Could not be updated"

    def get_handler(self, app_name):
        """Get a specialized handler for known applications."""
        return self.handlers.get(app_name)

    def handle_common_app(self, app):
        """Generic handler for all known apps in APP_APIS."""
        app_name = app['name'].lower()
        latest = get_latest_version(app_name)
        if latest and app['version'] != latest:
            logging.info(f"Updating {app['name']} from {app['version']} to {latest}")
            return self.run_update_command(f'winget upgrade --name "{app["name"]}" --silent')
        return False

    async def winget_update(self, app):
        """Fallback to winget for unknown apps."""
        updated = False  # Track if update was successful
        for option in ['--name', '--id']:
            if not self.active:
                return False

            # Emit signal without holding the lock
            self.update_app_being_processed.emit(app['name'])

            if await self.run_winget_update_option(app, option):
                updated = True

        return updated

    async def run_winget_update_option(self, app, option):
        """Run winget update for a specific option."""
        try:
            process = await asyncio.create_subprocess_shell(
                f'winget upgrade {option} "{app.get("name" if option == "--name" else "ident", "")}" --silent',
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            result_stdout = stdout.decode()
            result_stderr = stderr.decode()

            # Check for messages indicating the app was already up-to-date
            if "No installed package" in result_stdout or "No available upgrade" in result_stdout:
                logging.info(f"{app.get('name', 'Unknown')} is already up to date or not installed.")
                return False

            # Check if the upgrade was successful based on stdout content or return code
            if "Success" in result_stdout or process.returncode == 0:
                logging.info(f"Successfully updated {app.get('name', 'Unknown')}")
                return True

            logging.warning(f"Update for {app.get('name', 'Unknown')} failed: {result_stderr}")
            return False

        except Exception as e:
            logging.warning(f"Failed using {option} for {app.get('name', 'unknown')}: {e}")
            return False

    def run_update_command(self, command):
        """Execute a shell command to run updates. This does not need to be async."""
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

            # Check if the upgrade was successful based on stdout content
            if "No installed package" in result.stdout or "No available upgrade" in result.stdout:
                return False

            if "Success" in result.stdout:
                logging.info(f"Update command succeeded: {command}")
                return True

            return False

        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            logging.warning(f"Command timed out or failed: {command}")
            return False
