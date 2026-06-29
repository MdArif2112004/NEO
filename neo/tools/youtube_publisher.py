import os
import googleapiclient.discovery
import googleapiclient.errors
import google_auth_oauthlib.flow
import google.auth.transport.requests

def youtube_publisher(video_path, title, description):
    try:
        # Set up authentication
        api_service_name = "youtube"
        api_version = "v3"
        scopes = ["https://www.googleapis.com/auth/youtube.upload"]

        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            "client_secrets.json", scopes)
        credentials = flow.run_local_server(port=0)

        youtube = googleapiclient.discovery.build(
            api_service_name, api_version, credentials=credentials)

        # Set up video metadata
        video_metadata = {
            "snippet": {
                "title": title,
                "description": description,
                "category": "22",  # Short videos category
                "tags": ["short", "video"]
            },
            "status": {
                "privacyStatus": "public",
                "embeddable": True
            }
        }

        # Upload video
        request = youtube.videos().insert(
            part="snippet,status",
            body=video_metadata,
            media_body=googleapiclient.http.MediaFileUpload(
                video_path, "video/mp4")
        )
        response = request.execute()

        return '✅ Success: Video uploaded to YouTube as a Short with ID ' + response["id"]
    except googleapiclient.errors.HttpError as e:
        return '❌ Error: ' + str(e)
    except Exception as e:
        return '❌ Error: ' + str(e)