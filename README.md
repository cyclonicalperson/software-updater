# Software Updater

An Windows application for the automated updating of apps installed on the system.<br>
<p align="center">
  <img src="https://github.com/user-attachments/assets/f21ce4f7-4598-4eec-9fca-67d38fb22f72" />
</p>

## Features

- Scans installed applications from both 32-bit and 64-bit registry paths
- Updates all applications with the click of a button
- Lightweight and fast
- Packaged as a standalone portable `.exe`

## Requirements

- Windows 10/11 (Older versions not supported)
- winget (Install at https://aka.ms/getwinget)
- Python 3.10 or later (for development)

## Usage

Run the compiled `.exe` from the `dist/` folder.

Or run the `.py` file:

```bash
python gui.py
```

## FAQ
**- Can the application update all apps?<br>**
No, only apps present in winget (Windows Package Manager) or the fixed API list can be updated.<br>
This does not include more uncommon apps.<br><br>

**- How does the exclusion list work?<br>**
Any app in the installed apps list can be selected and excluded by clicking the 'Exclude Selected' button.<br>
Apps can be returned back to the installed apps list by selecting an app in the exclusion list and pressing the 'Include Selected' button.<br>
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
    pyinstaller --onefile --noconsole --icon=icon.ico --name="Software Updater" gui.py
    ```

## Directory Structure

```
software-updater/
├── gui.py              # Main GUI application
├── app_detector.py     # Logic to read Windows registry
├── app_endpoints.py    # Fixed API endpoints for common applications
├── updater.py          # Logic to automatically update applications
├── icon.ico            # Application icon
├── README.md           # Project documentation
└── requirements.txt    # Python dependencies
```

## Contributing

Feel free to open issues or submit pull requests for improvements or bug fixes.

## License

GPL-3.0 License. See [LICENSE](LICENSE) for details.

