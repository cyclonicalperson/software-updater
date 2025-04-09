import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QListWidget, QPushButton, QVBoxLayout, QWidget, QProgressBar,
                             QTextEdit, QHBoxLayout, QStackedWidget, QGroupBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QFont
import gui_functions


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Software Updater")
        self.setGeometry(100, 100, 600, 565)
        self.setWindowIcon(QIcon("icon.ico"))

        self.exclusions_list = gui_functions.load_exclusions()
        self.apps_list = gui_functions.get_installed_apps()
        self.updates_list = gui_functions.get_update_list(self.apps_list, self.exclusions_list)
        self.unsupported_apps_list = gui_functions.get_unsupported_list(self.apps_list)

        self._init_ui()
        self.load_styles()

    def load_styles(self):
        with open("gui_styles.qss", "r") as f:
            self.setStyleSheet(f.read())

    def _init_ui(self):
        central_widget = QWidget()
        main_layout = QVBoxLayout()

        # Navigation Bar
        nav_layout = QHBoxLayout()
        self.nav_buttons = {}

        for i, (text, target_index) in enumerate({
            "Available Updates": 0, "Skipped Updates": 1, "Installed Apps": 2, "Unsupported Apps": 3
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
                             "installed": self.create_list_view("Installed Apps", self.apps_list),
                             "unsupported": self.create_list_view("Unsupported Apps", self.unsupported_apps_list)}

        self.stack.addWidget(self.view_widgets["updates"])
        self.stack.addWidget(self.view_widgets["excluded"])
        self.stack.addWidget(self.view_widgets["installed"])
        self.stack.addWidget(self.view_widgets["unsupported"])

        main_layout.addWidget(self.stack)

        # Buttons
        button_layout_top = QHBoxLayout()
        self.exclude_btn = QPushButton("Skip Updates for Selected App")
        self.include_btn = QPushButton("Restore Updates for Selected App")
        self.start_btn = QPushButton("Start Updates")

        # The buttons start as disabled by default
        for btn in (self.exclude_btn, self.include_btn):
            btn.setEnabled(False)
            button_layout_top.addWidget(btn)

        # Connect buttons to their respective functions
        self.exclude_btn.clicked.connect(self.exclude_app)
        self.include_btn.clicked.connect(self.include_app)
        self.start_btn.clicked.connect(self.start_update)

        main_layout.addLayout(button_layout_top)

        button_layout_bottom = QHBoxLayout()

        # The button will be 60% of the screen size
        button_layout_bottom.addWidget(self.start_btn)
        self.start_btn.setMaximumWidth(int(self.width() * 0.55))

        main_layout.addLayout(button_layout_bottom)

        # Progress bar and status
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        main_layout.addWidget(self.progress_bar)

        self.status_box = QTextEdit()
        self.status_box.setReadOnly(True)
        self.status_box.setFont(QFont("Arial", 10))
        self.status_box.setMaximumHeight(int(self.height() * 0.25))
        main_layout.addWidget(self.status_box)

        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        self.stack.setCurrentIndex(0)

        # Connect selection change signals to update the button states
        self.view_widgets["installed"].findChild(QListWidget).selectionModel().selectionChanged.connect(
            self.update_button_states)
        self.view_widgets["updates"].findChild(QListWidget).selectionModel().selectionChanged.connect(
            self.update_button_states)
        self.view_widgets["excluded"].findChild(QListWidget).selectionModel().selectionChanged.connect(
            self.update_button_states)
        self.view_widgets["unsupported"].findChild(QListWidget).selectionModel().selectionChanged.connect(
            self.update_button_states)

        # Set the first button as active
        self.switch_view(0, list(self.nav_buttons.values())[0])

        # Initial call to update button states when the app starts
        self.update_button_states()

    def create_list_view(self, title, data_list):
        """Creates the lists for the QStackBox widget."""
        box = QGroupBox(title)
        layout = QVBoxLayout()
        list_widget = QListWidget()
        list_widget.setFont(QFont("Arial", 10))
        for app in data_list:
            list_widget.addItem(app.get("name", "Unknown"))
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
        """Updates which buttons can be pressed."""
        current_index = self.stack.currentIndex()
        selected_item = self.get_selected_item(current_index)

        # Check if there are selected items and update button states accordingly
        has_selected_item = bool(selected_item)

        # Enable the "Exclude" button when an item is selected in Installed or Updates list
        self.exclude_btn.setEnabled((current_index == 0 or current_index == 2) and has_selected_item)

        # Enable the "Include" button when an item is selected in the Excluded Apps list
        self.include_btn.setEnabled(current_index == 1 and has_selected_item)

        # Enable "Start Updates" button if there are items in the "Available Updates" list
        self.start_btn.setEnabled(bool(self.view_widgets["updates"].findChild(QListWidget).count()))

    def exclude_app(self):
        """Moves an app from the Updates or Installed Apps list to the Excluded list."""
        selected_item = self.get_selected_item(self.stack.currentIndex())[0]

        if selected_item:
            app_name = selected_item.text()  # Using only app names

            # First, check if the app is in the Updates list
            app = next((app for app in self.updates_list if app["name"] == app_name), None)

            # If not found in the Updates list, check in the Installed Apps list
            if not app:
                app = next((app for app in self.apps_list if app["name"] == app_name), None)

            if app:
                # Remove from the Updates list if present
                if app in self.updates_list:
                    self.updates_list = [app for app in self.updates_list if app["name"] != app_name]
                    list_widget = self.view_widgets["updates"].findChild(QListWidget)
                    list_widget.takeItem(list_widget.row(selected_item))

                # Add to the Exclusions list
                self.exclusions_list.append(app)
                gui_functions.save_exclusions(self.exclusions_list)

                # Add to the Exclusions list widget
                exclusions_widget = self.view_widgets["excluded"].findChild(QListWidget)
                exclusions_widget.addItem(app_name)
                exclusions_widget.sortItems(Qt.SortOrder.AscendingOrder)

                # Update button states after modification
                self.update_button_states()

    def include_app(self):
        """Moves an app from the Excluded list back to the Updates list if it has an available update."""
        # Get the selected item from the Excluded list
        exclusions_widget = self.view_widgets["excluded"].findChild(QListWidget)
        selected_item = exclusions_widget.selectedItems()[0] if exclusions_widget.selectedItems() else None

        if selected_item:
            app_name = selected_item.text()  # Get the app name from the item text

            # Find the app in the Exclusions list
            app = next((app for app in self.exclusions_list if app["name"] == app_name), None)
            if app:
                # Remove from the Exclusions list
                self.exclusions_list = [app for app in self.exclusions_list if app["name"] != app_name]

                # Remove from the Excluded list widget
                exclusions_widget.takeItem(exclusions_widget.row(selected_item))

                # Check if the app has an available update
                if app.get("available"):  # Assuming 'available' is the key indicating the update
                    # The app has an update, so add it back to the Updates list view
                    updates_widget = self.view_widgets["updates"].findChild(QListWidget)
                    updates_widget.addItem(app_name)
                    updates_widget.sortItems(Qt.SortOrder.AscendingOrder)

                # Save the modified Exclusions list
                gui_functions.save_exclusions(self.exclusions_list)

                # Update button states after modification
                self.update_button_states()

    def start_update(self):
        """Starts the update process for all apps on the update list."""
        """self.status_box.clear()
        self.progress_bar.setValue(0)
        app_list = [app for app in get_installed_apps() if app['name'] not in self.exclusions]

        # Call async function using QThreadPool, passing the loop
        async_worker = AsyncWorker(self.manager.check_and_install, app_list, loop=self.loop)
        async_worker.signals.finished.connect(lambda: self.status_bar.showMessage("All updates completed!", 3000))
        async_worker.signals.error.connect(self.show_error_message)
        self.threadpool.start(async_worker)"""

    def update_status(self, progress, message):
        self.progress_bar.setValue(progress)
        if "Successfully updated" in message:
            self.status_box.append(f"<font color='green'>{message}</font>")
        elif "Could not be updated" in message:
            self.status_box.append(f"<font color='red'>{message}</font>")
        else:
            self.status_box.append(message)

    def show_error_message(self, message):
        """Prints an error message in the status text box."""
        self.status_box.append(f"<font color='red'>Error: {message}</font>")


if __name__ == "__main__":
    application = QApplication(sys.argv)
    gui_functions.check_winget()
    gui_functions.check_winget_module()
    window = MainWindow()
    window.show()
    sys.exit(application.exec())
