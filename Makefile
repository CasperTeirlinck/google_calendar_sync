SHELL=/bin/bash

.ONESHELL:

run:
	docker compose up --build

build:
	docker build -t casperteirlinck/google_calendar_sync:latest --no-cache .

push:
	docker push casperteirlinck/google_calendar_sync:latest