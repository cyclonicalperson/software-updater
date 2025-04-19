import asyncio
import os
import sys
from PyQt6.QtWidgets import (QApplication, QListWidget, QPushButton, QVBoxLayout, QWidget, QProgressBar, QTextEdit,
                             QHBoxLayout, QStackedWidget, QGroupBox, QLabel, QListWidgetItem, QSizePolicy, QComboBox,
                             QMessageBox, QDialog)
from PyQt6.QtCore import Qt, QRunnable, pyqtSignal, QObject, pyqtSlot, QThreadPool
from PyQt6.QtGui import QIcon, QFont, QColor
import gui_functions
from updater import UpdateManager


class AsyncSignals(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(str)


class AsyncWorker(QRunnable):
    def __init__(self, async_func, *args):
        super().__init__()
        self.async_func = async_func
        self.args = args
        self.signals = AsyncSignals()

    @pyqtSlot()
    def run(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.async_func(*self.args))
        except Exception as e:
            self.signals.error.emit(str(e))
            print(f"AsyncWorker error: {e}")
        finally:
            self.signals.finished.emit()


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Software Updater")
        self.setGeometry(100, 100, 600, 565)
        self.setWindowIcon(QIcon("icon.ico"))

        # Fetch the app lists
        self.exclusions_list = gui_functions.load_exclusions()
        self.apps_list = gui_functions.get_installed_apps()
        self.updates_list = gui_functions.get_update_list(self.apps_list, self.exclusions_list)

        # Set up variables for QThread
        self.threadpool = QThreadPool()
        self.concurrent_update_number = 2  # How many apps update at once
        self.warning_not_shown = True  # Check to only show the update number warning once
        self.manager = None  # Placeholder for check_updates()

        # Stylize the UI
        self._init_ui()
        self.load_styles()

    def load_styles(self):
        """Loads the app's CSS from gui_styles.qss."""
        try:
            if getattr(sys, 'frozen', False):
                # Running as compiled .exe
                base_path = sys._MEIPASS
            else:
                # Running from source
                base_path = os.path.dirname(os.path.abspath(__file__))

            qss_path = os.path.join(base_path, "gui_styles.qss")
            with open(qss_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())

        except Exception as e:
            print(f"[Style Load Error] {e}")

    def _init_ui(self):
        """Initializes all the GUI elements."""
        central_widget = QWidget()
        main_layout = QVBoxLayout()

        # Navigation Bar
        nav_layout = QHBoxLayout()
        self.nav_buttons = {}

        for i, (text, target_index) in enumerate({
            "Available Updates": 0, "Skipped Updates": 1, "Installed Apps": 2
        }.items()):
            btn = QPushButton(text)
            btn.setProperty("navButton", True)
            btn.clicked.connect(lambda _, idx=target_index, button=btn: self.switch_view(idx, button))
            self.nav_buttons[text] = btn
            nav_layout.addWidget(btn)

        main_layout.addLayout(nav_layout)

        # Stack of Views
        self.stack = QStackedWidget()
        self.view_widgets = {"updates": self.create_list_view("Apps to Update", self.updates_list),
                             "excluded": self.create_list_view("Skipped Updates", self.exclusions_list),
                             "installed": self.create_list_view("Installed Apps", self.apps_list)}

        self.stack.addWidget(self.view_widgets["updates"])
        self.stack.addWidget(self.view_widgets["excluded"])
        self.stack.addWidget(self.view_widgets["installed"])

        main_layout.addWidget(self.stack)

        # === Row 1 ===
        button_row1 = QHBoxLayout()

        # Skip Updates button
        self.toggle_btn = QPushButton("Skip Updates for Selected App")
        self.toggle_btn.setEnabled(False)
        self.toggle_btn.clicked.connect(self.update_button_states)
        self.toggle_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)  # Make it expandable

        button_row1.addWidget(self.toggle_btn)

        # Settings button
        self.settings_btn = QPushButton()
        self.settings_btn.setIcon(QIcon("settings.ico"))
        self.settings_btn.setToolTip("Open Settings")
        self.settings_btn.setFixedSize(32, 32)
        self.settings_btn.clicked.connect(self.open_settings_dialog)

        button_row1.addWidget(self.settings_btn)

        main_layout.addLayout(button_row1)

        # === Row 2 ===
        button_row2 = QHBoxLayout()

        # Update Selected Apps button
        self.selected_btn = QPushButton("Update Selected Apps")
        self.selected_btn.setEnabled(False)
        self.selected_btn.clicked.connect(self.update_selected_apps)
        button_row2.addWidget(self.selected_btn)

        # Update All Apps button
        self.start_btn = QPushButton("Update All Apps")
        self.start_btn.clicked.connect(lambda: self.start_update(self.updates_list))
        button_row2.addWidget(self.start_btn)

        # Stop Updates button
        self.stop_btn = QPushButton("Stop Update Process")
        self.stop_btn.clicked.connect(self.stop_updates)
        self.stop_btn.hide()  # Hidden at app start
        button_row2.addWidget(self.stop_btn)

        main_layout.addLayout(button_row2)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        main_layout.addWidget(self.progress_bar)

        # Status box
        self.status_box = QTextEdit()
        self.status_box.setReadOnly(True)
        self.status_box.setFont(QFont("Arial", 10))
        self.status_box.setMaximumHeight(int(self.height() * 0.25))
        main_layout.addWidget(self.status_box)

        central_widget.setLayout(main_layout)
        self.setLayout(main_layout)
        self.stack.setCurrentIndex(0)  # QStackWidget starts on first list

        # Connect selection change signals to update the button states
        self.view_widgets["installed"].findChild(QListWidget).selectionModel().selectionChanged.connect(
            self.update_button_states)
        self.view_widgets["updates"].findChild(QListWidget).selectionModel().selectionChanged.connect(
            self.update_button_states)
        self.view_widgets["excluded"].findChild(QListWidget).selectionModel().selectionChanged.connect(
            self.update_button_states)

        # Set the first button as active
        self.switch_view(0, list(self.nav_buttons.values())[0])

        # Initial call to update button states when the app starts
        self.update_button_states()

    def create_list_view(self, title, data_list):
        """Creates the lists for the QStackWidget."""
        box = QGroupBox(title)
        layout = QVBoxLayout()
        list_widget = QListWidget()
        list_widget.setFont(QFont("Arial", 10))

        for app in data_list:
            if isinstance(app, dict):  # Ensure app is a dictionary
                name = app.get("name", "Unknown")
                version = app.get("version", "Unknown")
                available_version = app.get("available", "Unknown")
            else:
                # Handle the case where `app` is not a dictionary
                name = version = available_version = "Invalid data"

            # Format the list entries
            if title == "Apps to Update":
                text = f"{name} - {version} -> {available_version}"
            elif title == "Installed Apps":
                text = f"{name} - {version}"
            else:
                text = name

            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, app)

            # Set checkbox only for update list
            if title == "Apps to Update":
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Unchecked)

            # If updates are not supported, visually denote that
            if app.get("source", "") == "":
                font = item.font()
                font.setItalic(True)
                item.setFont(font)
                item.setBackground(QColor("#4e1e1e"))

            list_widget.addItem(item)

        if title == "Apps to Update":
            list_widget.itemChanged.connect(self.update_button_states)

        layout.addWidget(list_widget)
        list_widget.sortItems(Qt.SortOrder.AscendingOrder)
        box.setLayout(layout)
        return box

    def switch_view(self, index, button):
        """Switches which list (and associated button) is currently active in the GUI."""
        # Remove the 'active' property from all buttons
        for btn in self.nav_buttons.values():
            btn.setProperty("active", False)
            btn.setStyleSheet(btn.styleSheet())  # Update styles to remove active styling

        # Set the clicked button as active
        button.setProperty("active", True)
        button.setStyleSheet(button.styleSheet())  # Apply active state styling

        # Clear the selection in the current list view before switching
        current_view = list(self.view_widgets.values())[self.stack.currentIndex()]
        current_list_widget = current_view.findChild(QListWidget)
        current_list_widget.clearSelection()

        # Switch the view
        self.stack.setCurrentIndex(index)
        self.update_button_states()

    def get_selected_item(self, index):
        """Returns which app is selected in the index's list."""
        if index == 0:  # Available Updates
            return self.view_widgets["updates"].findChild(QListWidget).selectedItems()
        elif index == 1:  # Excluded Apps
            return self.view_widgets["excluded"].findChild(QListWidget).selectedItems()
        elif index == 2:  # Installed Apps
            return self.view_widgets["installed"].findChild(QListWidget).selectedItems()
        return None

    def update_button_states(self):
        """Updates which buttons can be pressed and adjusts the button text."""
        current_index = self.stack.currentIndex()
        selected_item = self.get_selected_item(current_index)

        # Enable/disable the toggle button based on selection
        self.toggle_btn.setEnabled(bool(selected_item))

        # Change toggle button text based on view
        if current_index == 1:  # Excluded Apps
            self.toggle_btn.setText("Restore Updates for Selected App")
            self.toggle_btn.clicked.disconnect()
            self.toggle_btn.clicked.connect(self.include_app)
        else:
            self.toggle_btn.setText("Skip Updates for Selected App")
            self.toggle_btn.clicked.disconnect()
            self.toggle_btn.clicked.connect(self.exclude_app)

        # Enable "Start Updates" if update list has entries
        self.start_btn.setEnabled(bool(self.view_widgets["updates"].findChild(QListWidget).count()))

        # Enable "Update Selected Apps" if at least one checkbox is checked
        update_list = self.view_widgets["updates"].findChild(QListWidget)
        has_checked = any(update_list.item(i).checkState() == Qt.CheckState.Checked for i in range(update_list.count()))
        self.selected_btn.setEnabled(has_checked)

    def exclude_app(self):
        """Moves an app from the installed apps/available updates lists to the excluded apps list."""
        selected_item = self.get_selected_item(self.stack.currentIndex())[0]

        if selected_item:
            # Fetch the app with all of it's data
            app = selected_item.data(Qt.ItemDataRole.UserRole)
            if app:
                app_name = app.get("name")

                # Remove from updates list if present
                self.updates_list = [a for a in self.updates_list if a.get("name") != app_name]
                updates_widget = self.view_widgets["updates"].findChild(QListWidget)
                for i in range(updates_widget.count()):
                    if updates_widget.item(i).data(Qt.ItemDataRole.UserRole).get("name") == app_name:
                        updates_widget.takeItem(i)
                        break

                # Only add to exclusions if not already there
                if app_name not in [a["name"] for a in self.exclusions_list]:
                    self.exclusions_list.append(app)
                    gui_functions.save_exclusions(self.exclusions_list)

                    exclusions_widget = self.view_widgets["excluded"].findChild(QListWidget)
                    item = QListWidgetItem(app_name)
                    item.setData(Qt.ItemDataRole.UserRole, app)
                    exclusions_widget.addItem(item)
                    exclusions_widget.sortItems(Qt.SortOrder.AscendingOrder)

                self.update_button_states()

    def include_app(self):
        """Moves an app from the excluded apps list back to the installed apps/available updates lists."""
        exclusions_widget = self.view_widgets["excluded"].findChild(QListWidget)
        selected_item = exclusions_widget.selectedItems()[0] if exclusions_widget.selectedItems() else None

        if selected_item:
            # Fetch the app with all of it's data
            app = selected_item.data(Qt.ItemDataRole.UserRole)
            app_name = app.get("name")

            # Remove from exclusions list
            self.exclusions_list = [a for a in self.exclusions_list if a.get("name") != app_name]
            exclusions_widget.takeItem(exclusions_widget.row(selected_item))

            if app.get("available"):
                # Add back to updates list if it has an update
                if app_name not in [a.get("name") for a in self.updates_list]:
                    self.updates_list.append(app)

                updates_widget = self.view_widgets["updates"].findChild(QListWidget)
                item = QListWidgetItem(f"{app_name} - {app['version']} -> {app['available']}")
                item.setData(Qt.ItemDataRole.UserRole, app)
                updates_widget.addItem(item)
                updates_widget.sortItems(Qt.SortOrder.AscendingOrder)

            gui_functions.save_exclusions(self.exclusions_list)
            self.update_button_states()

    def start_update(self, apps_to_update):
        """Starts the update process for the given app list."""
        # Reset GUI progress widgets
        self.status_box.clear()
        self.progress_bar.setValue(0)

        # Remove update buttons, show stop button
        self.start_btn.hide()
        self.selected_btn.hide()
        self.stop_btn.show()

        # Ensure no malformed entries are sent to the function
        clean_updates = [app for app in apps_to_update if isinstance(app, dict) and "name" in app and "id" in app]
        if not clean_updates:
            self.status_box.append("<font color='red'>No valid apps to update.</font>")
            return

        # Setup variables and signals for the QThread
        self.concurrent_update_number = int(self.concurrent_combobox.currentText())
        self.manager = UpdateManager(concurrent_limit=self.concurrent_update_number)
        self.manager.stop_requested = False
        self.manager.update_progress.connect(self.update_status)
        self.manager.update_app_being_processed.connect(
            lambda name: self.status_box.append(f"<b>Processing:</b> {name}")
        )
        self.manager.completed.connect(self.on_update_complete)

        # Call the update function in the new thread
        async_worker = AsyncWorker(self.manager.check_and_install, clean_updates)
        async_worker.signals.error.connect(self.show_error_message)
        self.threadpool.start(async_worker)

    def on_update_complete(self):
        """Fetches the new app and update lists after the update process is completed, and refreshes them in the GUI."""
        self.updates_list = gui_functions.get_update_list(self.apps_list, self.exclusions_list)

        updates_widget = self.view_widgets["updates"].findChild(QListWidget)
        updates_widget.blockSignals(True)  # Prevent premature signal triggering
        updates_widget.clear()  # Clears the QListWidget

        # Adds back entries to the QListWidget
        for app in self.updates_list:
            name = app.get("name", "Unknown")
            version = app.get("version", "Unknown")
            available = app.get("available", "Unknown")

            item = QListWidgetItem(f"{name} - {version} -> {available}")
            item.setData(Qt.ItemDataRole.UserRole, app)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)

            if app.get("source", "") == "":
                font = item.font()
                font.setItalic(True)
                item.setFont(font)

            updates_widget.addItem(item)

        updates_widget.sortItems(Qt.SortOrder.AscendingOrder)
        updates_widget.blockSignals(False)

        # Return update buttons, remove stop button
        self.start_btn.show()
        self.selected_btn.show()
        self.stop_btn.hide()

        self.update_button_states()

    def update_selected_apps(self):
        """Updates all apps marked with the checkmark box."""
        list_widget = self.view_widgets["updates"].findChild(QListWidget)
        selected_apps = []

        # Parse all entries in the update list, add checked entries to a new list
        for i in range(list_widget.count()):
            item = list_widget.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                app = item.data(Qt.ItemDataRole.UserRole)
                if app:
                    selected_apps.append(app)

        self.start_update(apps_to_update=selected_apps)

    def stop_updates(self):
        """Stops the ongoing update process."""
        if self.manager:
            self.manager.stop_requested = True
            self.status_box.append("<font color='orange'>Update process has been requested to stop...</font>")

    def open_settings_dialog(self):
        """Opens the settings dialog for changing the app configuration."""
        dialog = QDialog(self)
        dialog.setObjectName("SettingsDialog")
        dialog.setWindowTitle("Settings")
        dialog.setModal(True)
        dialog.setFixedSize(270, 100)

        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)

        # Row for label + combobox
        row_layout = QHBoxLayout()

        label = QLabel("Number of Apps Updated At Once:")
        label.setObjectName("SettingsLabel")

        combo = QComboBox()
        combo.setObjectName("SettingsComboBox")
        combo.addItems([str(i) for i in range(1, 11)])
        combo.setCurrentText(str(self.concurrent_update_number))
        combo.setFixedWidth(40)
        combo.currentTextChanged.connect(lambda val: self.handle_concurrency_change(int(val)))

        row_layout.addWidget(label)
        row_layout.addWidget(combo)
        layout.addLayout(row_layout)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.setObjectName("SettingsCloseButton")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)

        dialog.setLayout(layout)
        dialog.exec()

    def update_status(self, progress, message):
        """Prints the update status of apps in the update process to the status box."""
        self.progress_bar.setValue(progress)
        if "Successfully updated" in message:
            self.status_box.append(f"<font color='green'>{message}</font>")
        elif "No available update" in message:
            # Extract the app name from the message (assuming it's in the format "No available update: <app_name>")
            app_name = message.split(":")[-1].strip() if ":" in message else "Unknown App"
            self.status_box.append(f"<font color='green'>Successfully updated: {app_name}</font>")

            # self.status_box.append(f"<font color='yellow'>{message}</font>")  <-- Original code, updates always succeed though
        elif "Could not be updated" in message:
            self.status_box.append(f"<font color='red'>{message}</font>")
        else:
            self.status_box.append(message)

    def handle_concurrency_change(self, value):
        """Tracks the number of concurrent updates and shows a warning for large values."""
        self.concurrent_update_number = value
        if value >= 5 and self.warning_not_shown:
            gui_functions.show_warning("Running more than 5 concurrent updates may slow down your system.")
            self.warning_not_shown = False

    def show_error_message(self, message):
        """Prints an error message in the status text box."""
        self.status_box.append(f"<font color='red'>Error: {message}</font>")

    def closeEvent(self, event):
        """Called when the window is closing. Confirms and stops updates before exit."""
        if self.manager and not self.manager.stop_requested:
            reply = QMessageBox.question(
                self,
                "Confirm Exit",
                "Updates are still running. Are you sure you want to exit?\n The currently running updates will still finish.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.stop_updates()
                event.accept()
            else:
                event.ignore()
        else:
            self.stop_updates()
            event.accept()


if __name__ == "__main__":
    application = QApplication(sys.argv)
    gui_functions.check_winget()
    gui_functions.check_winget_module()

    main_widget = MainWindow()
    from frameless_window import FramelessWindow
    window = FramelessWindow(main_widget)

    window.setWindowIcon(QIcon("icon.ico"))
    window.resize(600, 565)
    window.show()

    sys.exit(application.exec())
