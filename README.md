<p align="center">
  <picture>
    <img src="https://github.com/CasperTeirlinck/notion_google_calendar/blob/main/logo.png?raw=true" height="128">
  </picture>
  <h1 align="center">Notion → Google Calendar</h1>
  <h2 align="center">One-way sync from Notion databases to Google Calendar Events</h2>
</p>

<p align="center">
  <img alt="Docker Image Size (tag)" src="https://img.shields.io/docker/image-size/casperteirlinck/notion_google_calendar/latest?logo=docker&style=flat-square">
  <img alt="Docker Pulls" src="https://img.shields.io/docker/pulls/casperteirlinck/notion_google_calendar?logo=docker&
  style=flat-square">
</p>

## Configuration

1. Obtain the necessary API tokens from [Notion](#notion-api) and [Google](#google-api)
2. Configure each Notion database and how its properties map to Google Calendar events in `config/config.yaml`. See `config/example.config.yaml` for all available configuration options.

## Google API

> OAuth for google doesn't seem to work in Brave browser, use Google Chrome instead.

1. [Create the credentials](https://developers.google.com/calendar/api/quickstart/python.)
   - scope: "/auth/calendar"
2. Store `credentials.json` in `secrets/credentials.json`.

## Notion API

1. [Create an integration](https://developers.notion.com/docs/create-a-notion-integration) for every workspace you want to sync from.
   - Integration type: "Internal integration"
2. Store the integration tokens in `secrets/notion.json`:

   ```json
   {
   	"integration_tokens": {
   		"<workspace_name>": "<integration_token>"
   	}
   }
   ```

3. Add the integration to each database in Notion.

## Scheduling & Monitoring

- Scheduling using Cron in a Docker container: \
  Deploy as a docker container using `docker-compose.yml` and set the schedule using `CRON_SCHEDULE` in `.env`.

  ```shell
  docker compose up -d
  ```

  OR

  Run the docker container manually, also available on [Docker Hub](https://hub.docker.com/r/casperteirlinck/notion_google_calendar)

- Monitoring using logfile: \
  See logfile at `logs/logfile`

- Monitoring using Uptime Kuma: \
  Set the correct push url using `KUMA_PUSH_URL` in `.env`. \
  If Uptime Kuma is also running inside a container, user the container name and port instead of the external url:
  `http://<kuma_container_name>:3001/api/...` \
  Make sure the cron schedule and hearthbeat interval in uptime kuma match. \
  Make sure to add the running container to a shared docker network with the Uptime Kuma container.
