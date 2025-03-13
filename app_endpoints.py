import requests
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# API endpoints for known applications
APP_APIS = {
    'chrome': 'https://versioncheck.googleapis.com/v1/chrome/updates',
    'firefox': 'https://product-details.mozilla.org/1.0/firefox_versions.json',
    'vscode': 'https://update.code.visualstudio.com/api/releases/stable',
    'zoom': 'https://zoom.us/rest/v2/download/checkupdate',
    'slack': 'https://slack.com/api/apps.updates',
    'spotify': 'https://api.spotify.com/v1/updates',
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
        data = response.json()

        if app_name == 'chrome':
            return data.get('current_version', "")
        elif app_name == 'firefox':
            return data.get('LATEST_FIREFOX_VERSION', "")
        elif app_name == 'vscode' and isinstance(data, list):
            return data[0].get('version', "")
        elif app_name == 'zoom':
            return data.get('latest_version', "")
        # Placeholder for Slack and Spotify (expand as needed)
        elif app_name in ['slack', 'spotify']:
            return ""

    except Exception as e:
        logging.error(f"Error fetching latest version for {app_name}: {e}")

    return ""
