import winreg
from typing import List, Dict


def get_installed_apps() -> List[Dict]:
    """Read installed apps from Windows Registry"""
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
                        name = _get_reg_value(subkey, "DisplayName")
                        if name:
                            apps.append({
                                'name': name,
                                'version': _get_reg_value(subkey, "DisplayVersion"),
                                'publisher': _get_reg_value(subkey, "Publisher"),
                                'ident': subkey_name
                            })
                except OSError:
                    continue
    return apps


def _get_reg_value(key, value_name):
    try:
        value, _ = winreg.QueryValueEx(key, value_name)
        return str(value) if value else ""
    except FileNotFoundError:
        return ""
