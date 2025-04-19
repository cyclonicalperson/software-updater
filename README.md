# Software Updater

A GUI-based software updater for Windows 10/11, built with Python and PyQt6.<br>
Designed to streamline the process of checking for, downloading, and installing updates for various applications.<br>
<p align="center">
  <img src="https://github.com/user-attachments/assets/829a1fed-0485-42a6-bda7-fb5369166768">
</p>

## Requirements

- **Windows 10/11** (Older versions not supported)

## Features

- **Frameless Custom UI**: Modern interface with draggable title bar and custom window controls.
- **Update Management**: Check for updates, download, and install them seamlessly.
- **Selective Updates**: Choose specific applications to update.
- **Skip Updates**: Option to skip updates for selected applications.
- **Process Control**: Ability to stop ongoing update processes.

## Usage

The app should be **ran as administrator** on first boot to install neccesary dependencies.<br>
It also won't show UAC prompts, requesting administrator access to update apps.<br>

### - App Lists -
The **Available Updates** list shows all apps with updates that may be installed.<br><br>
The **Skipped Updates** list shows all apps which will not be checked for updates and ignored. <br>Apps may be added to this list from any of the other two lists.<br><br>
The **Installed Apps** list shows all apps detected on the system. <br>Apps in <i>italic</i> with a red background are not supported for automatic updates.<br><br>

### - Buttons -
Apps may be updated in two ways:
 - All at once with the **Update All Apps** button, or
 - Only the checkmarked apps with the **Update Selected Apps** button.<br>

The **Stop Update Process** button appears when the update process starts, and will stop further app updates. <br> Currently running updates will still finish.<br><br>
The **Skip/Restore Updates for Selected App** button will appear when an app is selected, and moves the app to and from the **Skipped Updates** list.<br>

The **cogwheel button** right of the progress bar opens the app config:
- The **Number of Apps Updated at Once** setting is how many update processes will run at once. <br>Running many processes may slow down the entire system (since the app will utilize up to 100% of the CPU).<br><br>

## FAQ
**- Can the application update all apps?<br>**
No, only apps present in winget (Windows Package Manager) can be updated.<br>
This does not include more uncommon apps.<br><br>

**- How does the exclusion list work?<br>**
Any app in the **Installed Apps** or **Available Updates** list can be selected and excluded by pressing the '**Skip Updates**' button.
Apps can be returned back to the installed apps list by selecting an app in the exclusion list and pressing the '**Restore Updates**' button.<br>
Any apps in the exclusion list will have their updates skipped.

## Installation (for development)

1. Clone the repository:

    ```bash
    git clone https://github.com/cyclonicalperson/software-updater.git
    cd software-updater
    ```

2. Create a Virtual Environment (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```

Run the application using:
  ```bash
  python main.py
  ```

## Directory Structure

```
software-updater/
├── OLD/                      # Folder containing old, no longer used 1.x.x files
├── gui.py                    # Main GUI application
├── frameless_window.py       # GUI component for replacing the default Windows window
├── gui_functions.py          # Logic for the GUI
├── gui_styles.qss            # CSS for the GUI
├── updater.py                # Logic for automatically updating applications
├── icon.ico                  # App icon
├── settings.ico              # Settings button icon
└── requirements.txt          # Python dependencies
```

## Contributing

Feel free to open issues or submit pull requests for improvements or bug fixes.

## License

GPL-3.0 License. See [LICENSE](LICENSE) for details.

