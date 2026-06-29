import os
import requests

def discord_bridge(message, file_path=None):
    webhook_url = os.environ.get('DISCORD_WEBHOOK_URL')
    if not webhook_url:
        return '❌ Error: DISCORD_WEBHOOK_URL environment variable is not set'

    data = {'content': message}
    files = None
    if file_path:
        if not os.path.exists(file_path):
            return '❌ Error: File not found at the specified path'
        files = {'file': open(file_path, 'rb')}

    try:
        response = requests.post(webhook_url, data=data, files=files)
        if response.status_code in [200, 204]:
            return '✅ Success: Message sent to Discord'
        else:
            return f'❌ Error: Failed to send message to Discord (Status code: {response.status_code})'
    except requests.exceptions.RequestException as e:
        return f'❌ Error: Failed to send message to Discord ({str(e)})'