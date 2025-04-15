# Software Updater

An Windows application for the automated updating of apps installed on the system.<br>
<p align="center">
  <img src="https://github.com/user-attachments/assets/2207099e-2d0b-4ff0-8bb7-f551b1c5d1c4">
</p>

## Requirements

- Windows 10/11 (Older versions not supported)

## Features

- Scans installed applications on the system
- Updates applications with the click of a button
- Lightweight and fast
- Packaged as a standalone portable `.exe`

## Usage

### App Lists
The **Available Updates** list shows all apps with updates that may be installed.<br><br>
The **Skipped Updates** list shows all apps which will not be checked for updates and ignored. <br>Apps may be added to this list from any of the other two lists.<br><br>
The **Installed Apps** list shows all apps detected on the system. <br>Apps in <i>italic</i> are not supported for automatic updates.<br><br><br>

### Buttons
Apps may be updated in two ways:
 - All at once with the **Update All Apps** button, or
 - Only the checkmarked apps with the **Update Selected Apps** button.<br>

The **Number of Apps Updated at Once** box shows how many update processes will run at once. <br>Running many processes may slow down the entire system (since the app will utilize up to 100% of the CPU).<br><br>
The update process may be stopped at any time with the **Stop Update Process** button, only the currently running updates will finish updating.

## FAQ
**- Can the application update all apps?<br>**
No, only apps present in winget (Windows Package Manager) can be updated.<br>
This does not include more uncommon apps.<br><br>

**- How does the exclusion list work?<br>**
Any app in the Installed Apps or Available Updates list can be selected and excluded by pressing the 'Skip Updates' button.<br>
Apps can be returned back to the installed apps list by selecting an app in the exclusion list and pressing the 'Restore Updates' button.<br>
Any apps in the exclusion list will have their updates skipped.

## Installation (for development)

1. Clone the repository:

    ```bash
    git clone https://github.com/cyclonicalperson/software-updater.git
    cd software-updater
    ```

2. Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```

3. Build the executable (optional):

    ```bash
    pyinstaller software_installer.spec
    ```

## Directory Structure

```
software-updater/
├── gui.py                    # Main GUI application
├── gui_functions.py          # Logic for the GUI
├── updater.py                # Logic to automatically update applications
├── software_installer.spec   # .spec file for compiling the app with PyInstaller
└── requirements.txt          # Python dependencies
```

## Contributing

Feel free to open issues or submit pull requests for improvements or bug fixes.

## License

GPL-3.0 License. See [LICENSE](LICENSE) for details.

