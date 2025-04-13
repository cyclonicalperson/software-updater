import logging
import subprocess
import asyncio
from PyQt6.QtCore import QObject, pyqtSignal


class UpdateManager(QObject):
    update_progress = pyqtSignal(int, str)
    update_app_being_processed = pyqtSignal(str)
    completed = pyqtSignal()

    def __init__(self, concurrent_limit):
        super().__init__()
        self.active = True
        self.lock = asyncio.Lock()  # Add a lock for shared variables
        self.semaphore = asyncio.Semaphore(concurrent_limit)  # Limit number of concurrent updates
        self.completed_count = 0  # Initialize count of completed updates
        self.total_apps = 0  # Total number of apps to update
        self.stop_requested = False  # Track whether stopping updates was requested

    async def check_and_install(self, app_list):
        """Main update process with progress tracking and concurrency control."""
        try:
            self.total_apps = len(app_list)
            self.completed_count = 0  # Reset completed count
            logging.info(f"Total apps to update: {self.total_apps}")

            tasks = []

            for app in app_list:
                if self.stop_requested:
                    logging.info("Update process stopped by user.")
                    self.update_progress.emit(int((self.completed_count / self.total_apps) * 100),
                                              "<font color='orange'>Update process was stopped.</font>")
                    self.completed.emit()
                    return

                # Don't create the coroutine unless you're definitely using it
                task = self.run_with_semaphore(self.process_app_and_update_status, app)
                tasks.append(task)

            if not self.stop_requested:
                await asyncio.gather(*tasks)

            # Ensure completion signal is emitted when all tasks are done
            if self.completed_count >= self.total_apps:
                self.update_progress.emit(100, "<b>All updates completed!</b>")
                self.completed.emit()
            else:
                logging.warning(f"Completed {self.completed_count} out of {self.total_apps} updates.")
                self.update_progress.emit(int((self.completed_count / self.total_apps) * 100), "Update process finished with possible errors.")
                self.completed.emit()

        except Exception as e:
            logging.error(f"System error during update: {e}", exc_info=True)
            self.update_progress.emit(-1, f"System Error: {str(e)}")
            self.completed.emit()

    async def run_with_semaphore(self, func, app):
        """Run a task with semaphore control."""
        async with self.semaphore:
            return await func(app)

    async def process_app_and_update_status(self, app):
        """Process an app and update the progress."""
        if self.stop_requested:
            return

        try:
            self.update_app_being_processed.emit(app['name'])
            update_status = await self.process_app(app)

            async with self.lock:  # Lock for shared variable updates
                self.completed_count += 1
                progress = int((self.completed_count / self.total_apps) * 100) if self.total_apps > 0 else 100
                self.update_progress.emit(progress, f"{update_status}: {app['name']}")

        except Exception as e:
            logging.error(f"Error processing {app}: {e}", exc_info=True)

    async def process_app(self, app):
        """Handle each app update."""
        try:
            logging.info(f"Updating {app['name']} using winget.")
            updated = await self.winget_update(app)
            return "Successfully updated" if updated else "No available update"

        except Exception as e:
            logging.error(f"Error processing {app}: {e}", exc_info=True)
            return "Could not be updated"

    async def winget_update(self, app):
        """Use winget to update apps."""
        updated = False  # Track if update was successful
        for option in ['--id', '--name']:
            if self.stop_requested:
                logging.info(f"Update stopped during app {app.get('name', 'Unknown')}")
                return False

            if await self.run_winget_update_option(app, option):
                updated = True

        return updated

    async def run_winget_update_option(self, app, option):
        """Runs the winget update command and parses it's output."""
        try:
            name_or_id = app.get("name" if option == "--name" else "id")
            if not name_or_id:
                logging.debug(f"Skipping {option}: no identifier for {app.get('name', 'Unknown')}")
                return False

            logging.debug(f"Running winget update: winget upgrade {option} \"{name_or_id}\" --silent")
            process = await asyncio.create_subprocess_shell(
                f'winget upgrade {option} "{name_or_id}" --silent',
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()

            result_stdout = stdout.decode()
            result_stderr = stderr.decode()

            if "No installed package" in result_stdout or "No available upgrade" in result_stdout:
                logging.info(f"{app.get('name', 'Unknown')} is already up to date or not installed.")
                return False

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
                timeout=60
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
