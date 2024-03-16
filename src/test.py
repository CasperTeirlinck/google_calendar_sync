from pathlib import Path

from google.oauth2.service_account import Credentials
from googleapiclient import discovery

SCOPES = [
    "https://www.googleapis.com/auth/calendar",
]

secrets_path = Path(__file__).parents[1] / "config" / "secrets"
credentials_path = str(secrets_path / "google.json")

credentials = Credentials.from_service_account_file(
    credentials_path,
    scopes=SCOPES,
)

calendar = discovery.build("calendar", "v3", credentials=credentials)

request = calendar.events().list(
    calendarId="046a8ed6f3e1d526bcccf429d8c80d4dc13813ba5f6e48343f2a7d230d1b3cf0@group.calendar.google.com",
    singleEvents=False,
    maxResults=2500,
)

response = request.execute().get("items", [])

print(response)
