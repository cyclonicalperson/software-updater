import difflib
import json
import os
import re
import subprocess
import sys
from PyQt6.QtWidgets import QMessageBox

# Constants
EXCLUSIONS_DIR = os.path.join(os.getenv("LOCALAPPDATA"), "Software Updater")
EXCLUSIONS_FILE = os.path.join(EXCLUSIONS_DIR, "exclusions.json")


def show_error(message: str):
    """Display a critical error dialog and exit."""
    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Icon.Critical)
    msg_box.setWindowTitle("Error")
    msg_box.setText(message)
    msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
    msg_box.exec()
    sys.exit()


def show_warning(message: str):
    """Display a warning dialog."""
    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Icon.Warning)
    msg_box.setWindowTitle("Warning")
    msg_box.setText(message)
    msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
    msg_box.exec()


def check_winget():
    """Checks whether a properly installed winget is present."""
    try:
        subprocess.run(
            ["winget", "--version"],
            check=True,
            shell=False,
            creationflags=subprocess.CREATE_NO_WINDOW,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    except FileNotFoundError:
        show_error("Winget is not installed on this system.")
    except subprocess.CalledProcessError:
        show_error("Winget is installed but returned an error.")


def check_winget_module():
    """Checks whether Microsoft.WinGet.Client module is installed. Attempts installation if missing."""

    ps_script = r'''
    $ErrorActionPreference = 'Stop'
    $ProgressPreference = 'SilentlyContinue'
    $moduleName = 'Microsoft.WinGet.Client'

    # Check if already installed
    if (Get-Module -ListAvailable -Name $moduleName) {
        Write-Output "INSTALLED"
        exit 0
    }

    # Check if running as admin
    $isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
        [Security.Principal.WindowsBuiltInRole] "Administrator")

    if (-not $isAdmin) {
        Write-Output "NEED_ADMIN"
        exit 1
    }

    # Install NuGet provider (required by PowerShellGet)
    if (-not (Get-PackageProvider -Name NuGet -ErrorAction SilentlyContinue)) {
        Install-PackageProvider -Name NuGet -Force -Scope AllUsers -Confirm:$false
    }

    # Trust PSGallery explicitly
    Set-PSRepository -Name PSGallery -InstallationPolicy Trusted

    # Force install/update to latest PowerShellGet (v2+)
    try {
        Install-Module -Name PowerShellGet -Force -AllowClobber -Scope AllUsers -Confirm:$false -Repository PSGallery
        Import-Module PowerShellGet -Force
    } catch {
        Write-Output "FAILED: PowerShellGet update failed: $($_.Exception.Message)"
        exit 2
    }

    # Now install Microsoft.WinGet.Client
    try {
        Install-Module -Name $moduleName -Repository PSGallery -Scope AllUsers -Force -Confirm:$false -AllowClobber
        Write-Output "INSTALLED_SUCCESS"
        exit 0
    } catch {
        Write-Output "FAILED: Module install failed: $($_.Exception.Message)"
        exit 3
    }
    '''

    result = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        shell=False,
        creationflags=subprocess.CREATE_NO_WINDOW
    )

    output = result.stdout.strip()

    if "INSTALLED" in output or "INSTALLED_SUCCESS" in output:
        return
    elif "NEED_ADMIN" in output:
        show_error("Administrator privileges are required to install Microsoft.WinGet.Client.")
    elif "FAILED" in output:
        show_error(f"Failed to install Microsoft.WinGet.Client:\n\n{output}")
    else:
        show_error(f"Unknown error occurred:\n\n{output}\n{result.stderr.strip()}")


def load_exclusions() -> list[dict]:
    """Loads exclusions from the exclusions.json file in AppData."""
    try:
        with open(EXCLUSIONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_exclusions(exclusions: list[dict]):
    """Saves exclusions to the exclusions.json file in AppData."""
    with open(EXCLUSIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(exclusions, f, indent=4)


def get_installed_apps():
    """Gets a list of installed applications using winget and parses the output."""
    try:
        # Get the full app names using PowerShell command
        names_result = subprocess.run(
            ["powershell", "-Command", "Get-WinGetPackage | Select Name"],
            capture_output=True, text=True, check=True
        )

        # Get the name, id, version, availability, and source from WinGet using PowerShell command
        winget_result = subprocess.run(
            ["winget", "list", "--accept-source-agreements"],
            capture_output=True, text=True, check=True
        )

        # Parse clean full names
        full_names = [line.strip() for line in names_result.stdout.splitlines() if line.strip()]

        # Parse winget list output
        winget_lines = winget_result.stdout.splitlines()[8:]
        winget_lines = [line.strip().replace('â€¦', '   ') for line in winget_lines if line.strip()]

        # Create a list to store app details
        apps = []
        used_names = set()
        for line in winget_lines:
            # Regex to match name, id, version, available, and source
            match = re.match(
                r"^(?P<name>.+?)\s{2,}(?P<id>\S+)\s{2,}(?P<version>\S+|Unknown)(?:\s{2,}(?P<available>\S+))?(?:\s{2,}(?P<source>\S+))?$",
                line.strip()
            )

            if match:
                # Splits the match into the found components
                parts = re.split(r'\s{2,}', line)

                if len(parts) < 3:
                    continue  # Skip malformed lines

                winget_name = parts[0]
                if winget_name == "Name":  # Since the name column can still sneak through, hardcoded it out
                    pass
                app_id = parts[1]
                version = parts[2] if parts[2] != '' else 'Unknown'
                available = ''
                source = ''

                if len(parts) >= 5:
                    available = parts[3]
                    source = parts[4]
                elif len(parts) == 4:
                    # Heuristic for version-vs-source
                    if re.match(r"^\d+(\.\d+)*$", parts[3]):
                        available = parts[3]
                    else:
                        source = parts[3]

                resolved_name = get_best_full_name(winget_name, full_names, used_names)
                used_names.add(resolved_name)

                apps.append({
                    "name": resolved_name,
                    "id": app_id,
                    "version": version,
                    "available": available,
                    "source": source
                })

        return apps

    except subprocess.CalledProcessError:
        return []


def get_update_list(apps_list, exclusions_list):
    """Add apps to the update list when the application is run."""
    apps = []
    for app in apps_list:
        if app not in exclusions_list and app["available"] != "":
            apps.append(app)

    return apps


def get_best_full_name(raw_name, full_names, used_names):
    """Tries matching the best full name possible from a cut-off name."""
    raw_name = raw_name.strip()

    # Tier 1: Exact match
    if raw_name in full_names and raw_name not in used_names:
        return raw_name

    # Tier 2: Startswith match (prefer longest, unused)
    startswith_matches = [name for name in full_names if name.startswith(raw_name) and name not in used_names]
    if startswith_matches:
        return max(startswith_matches, key=lambda name: len(name))

    # Tier 3: Fuzzy match — ensure uniqueness
    fuzzy_matches = difflib.get_close_matches(raw_name, full_names, n=5, cutoff=0.6)
    for match in fuzzy_matches:
        if match not in used_names:
            return match

    # Fallback
    return raw_name
