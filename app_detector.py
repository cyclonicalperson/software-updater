import winreg


def get_installed_apps():
    """Improved registry reader with common app detection"""
    apps = []
    reg_paths = [
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
        r"SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
    ]

    for path in reg_paths:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path) as key:
            for i in range(winreg.QueryInfoKey(key)[0]):
                try:
                    subkey_name = winreg.EnumKey(key, i)
                    with winreg.OpenKey(key, subkey_name) as subkey:
                        if app := read_app_details(subkey, subkey_name):
                            apps.append(app)
                except OSError:
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

