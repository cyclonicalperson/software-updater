"""THIS FILE IS NO LONGER USED AS OF v2.0"""


import winreg


def get_installed_apps():
    """Improved registry reader with filtering for common app exclusions"""
    apps = []
    reg_paths = [
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
        r"SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
    ]

    for path in reg_paths:
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path) as key:
                for i in range(winreg.QueryInfoKey(key)[0]):
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        with winreg.OpenKey(key, subkey_name) as subkey:
                            app = read_app_details(subkey, subkey_name)
                            if app and is_valid_app(app):
                                apps.append(app)
                    except OSError:
                        continue
        except FileNotFoundError:
            continue
    return apps


def get_reg_value(key, value_name):
    """Helper function to safely get registry values"""
    try:
        value, _ = winreg.QueryValueEx(key, value_name)
        return str(value) if value else None
    except FileNotFoundError:
        return None


def read_app_details(subkey, subkey_name):
    """Extract app details from registry"""
    name = get_reg_value(subkey, "DisplayName")
    if not name:
        return None

    return {
        'name': name,
        'version': get_reg_value(subkey, "DisplayVersion"),
        'publisher': get_reg_value(subkey, "Publisher"),
        'ident': get_reg_value(subkey, "BundleIdentifier") or subkey_name,
        'install_source': get_reg_value(subkey, "InstallSource"),
        'uninstall_string': get_reg_value(subkey, "UninstallString")
    }


def is_valid_app(app):
    """Check if the app is still valid (installed) and exclude unwanted types."""
    name = app['name']
    uninstall_string = app.get('uninstall_string')
    publisher = app.get('publisher')
    install_source = app.get('install_source')

    # Ensure the app has an uninstall string and display name
    if not uninstall_string or not name:
        return False

    # Exclude apps by known names, publishers, or install source
    exclusion_keywords = [
        'driver', 'update', 'chipset', 'python', 'jdk', 'java', 'windows', 'microsoft', 'amd', 'intel'
    ]

    # Check name, publisher, or install source against exclusion keywords
    if any(keyword.lower() in (name + (publisher or "") + (install_source or "")).lower() for keyword in
           exclusion_keywords):
        return False

    return True
