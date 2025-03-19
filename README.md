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

- Windows OS
- winget (Install at https://aka.ms/getwinget)
- Python 3.10 or later (for development)

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

## Usage

Run the application:

```bash
python gui.py
```

Or execute the compiled `.exe` from the `dist/` folder.

## Directory Structure

```
software-updater/
├── gui.py              # Main GUI application
├── app_detector.py     # Logic to read Windows registry
├── app_endpoints.py    # Fixed API endpoints for common applications
├── updater.py          # Logic to automatically update applications
├── exclusions.json     # List of exclusions
├── icon.ico            # Application icon
├── README.md           # Project documentation
└── requirements.txt    # Python dependencies
```

## Contributing

Feel free to open issues or submit pull requests for improvements or bug fixes.

## License

GPL-3.0 License. See [LICENSE](LICENSE) for details.

