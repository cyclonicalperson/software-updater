import requests
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Expanded API endpoints for known applications
APP_APIS = {
    'chrome': 'https://versioncheck.googleapis.com/v1/chrome/updates',
    'firefox': 'https://product-details.mozilla.org/1.0/firefox_versions.json',
    'vscode': 'https://update.code.visualstudio.com/api/releases/stable',
    'zoom': 'https://zoom.us/rest/v2/download/checkupdate',
    'slack': 'https://slack.com/api/apps.updates',
    'spotify': 'https://api.spotify.com/v1/updates',
    'edge': 'https://edgeupdates.microsoft.com/api/products',
    'opera': 'https://autoupdate.geo.opera.com/pub/opera/desktop/',
    'notepad++': 'https://notepad-plus-plus.org/update/getDownloadUrl.php',
    'discord': 'https://discord.com/api/v9/updates',
    'steam': 'https://api.steampowered.com/ISteamApps/GetAppList/v2/',
    'thunderbird': 'https://product-details.mozilla.org/1.0/thunderbird_versions.json',
    'git': 'https://api.github.com/repos/git/git/releases/latest',
    '7zip': 'https://7-zip.org/a/7z2201-x64.exe',
    'brave': 'https://updates.bravesoftware.com/latest/win64',
    'malwarebytes': 'https://downloads.malwarebytes.com/file/mb4_offline',
    'avast': 'https://www.avast.com/download-update',
    'avg': 'https://www.avg.com/en-us/download-update',
    'avira': 'https://www.avira.com/en/downloads',
    'skype': 'https://get.skype.com/',
    'dropbox': 'https://www.dropbox.com/download',
    'google_drive': 'https://dl.google.com/drive-file-stream/GoogleDriveSetup.exe',
    'onedrive': 'https://go.microsoft.com/fwlink/p/?LinkID=2124703',
    'python': 'https://www.python.org/downloads/',
    'filezilla': 'https://filezilla-project.org/download.php',
    'putty': 'https://www.chiark.greenend.org.uk/~sgtatham/putty/latest.html',
    'eclipse': 'https://www.eclipse.org/downloads/',
    'itunes': 'https://www.apple.com/itunes/download/',
    'vlc': 'https://www.videolan.org/vlc/index.html',
    'aimp': 'https://www.aimp.ru/',
    'foobar2000': 'https://www.foobar2000.org/download',
    'winamp': 'https://www.winamp.com/',
    'audacity': 'https://www.audacityteam.org/download/',
    'gom': 'https://www.gomlab.com/gomplayer-media-player/',
    'blender': 'https://www.blender.org/download/',
    'paint.net': 'https://www.getpaint.net/download.html',
    'gimp': 'https://www.gimp.org/downloads/',
    'xnview': 'https://www.xnview.com/en/xnview/',
    'inkscape': 'https://inkscape.org/release/',
    'faststone': 'https://www.faststone.org/',
    'sharex': 'https://getsharex.com/',
    'winrar': 'https://www.win-rar.com/download.html',
    'foxit_reader': 'https://www.foxit.com/pdf-reader/',
    'libreoffice': 'https://www.libreoffice.org/download/download/',
    'qbittorrent': 'https://www.qbittorrent.org/download.php',
    'anydesk': 'https://anydesk.com/en/downloads',
    'teamviewer': 'https://www.teamviewer.com/en/download/',
    'ccleaner': 'https://www.ccleaner.com/ccleaner/download',
}


def get_latest_version(app_name: str) -> str:
    """
    Fetch the latest version for a known application.
    :param app_name: The name of the application (e.g., 'chrome', 'firefox').
    :return: Latest version string if found, else an empty string.
    """
    if app_name not in APP_APIS:
        return ""

    try:
        response = requests.get(APP_APIS[app_name], timeout=10)
        response.raise_for_status()
        data = response.json() if response.headers.get('Content-Type') == 'application/json' else response.text

        if app_name == 'chrome':
            return data.get('current_version', "")
        elif app_name == 'firefox':
            return data.get('LATEST_FIREFOX_VERSION', "")
        elif app_name == 'vscode' and isinstance(data, list):
            return data[0].get('version', "")
        elif app_name == 'zoom':
            return data.get('latest_version', "")
        elif app_name == 'edge':
            return data[0]['ProductVersion'] if data else ""
        elif app_name == 'discord':
            return data.get('version', "")
        elif app_name == 'steam':
            return data['applist']['apps'][0]['name'] if 'applist' in data else ""
        elif app_name == 'notepad++':
            return data.split('/')[-1].replace('.exe', '')
        elif app_name == 'git':
            return data.get('tag_name', "")
        elif app_name == '7zip':
            return '22.01'  # Static version from URL
        elif app_name == 'thunderbird':
            return data.get('LATEST_THUNDERBIRD_VERSION', "")
        elif app_name == 'brave':
            return data.strip() if data else ""
        elif app_name == 'malwarebytes':
            return 'latest'  # Static fallback
        elif app_name == 'avast' or app_name == 'avg':
            return 'latest'  # No version info available from API
        elif app_name == 'putty':
            return 'latest'  # Static fallback

    except Exception as e:
        logging.error(f"Error fetching latest version for {app_name}: {e}")

    return ""
