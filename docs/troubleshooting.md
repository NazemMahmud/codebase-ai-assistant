# Troubleshooting

## `port is already allocated` on `docker compose up`
If you see this kind of error:
```
Bind for 0.0.0.0:8000 failed: port is already allocated
```
This means another container or local application is already using port 8000.

First, stop the current Docker Compose services:
```shell
docker compose down
```

Then check if another container is still using port `8000`:

```shell
docker ps --filter publish=8000
```
If another application on your computer is using that port, 
change the API port in `.env`, for example: `API_PORT=8001`

Then start the containers again.

## `container name "..." is already in use`

Two services were given the same `container_name`, or a container from a previous
run is lingering.

```bash
docker compose down --remove-orphans
```

## PyCharm Docker interpreter: `port is already allocated` / packaging errors

When PyCharm builds a Docker Compose remote interpreter it starts the `api`
service, which publishes port 8000 and collides with your running API. Use the
IDE-only override that has no published ports — see below.

## PyCharm remote interpreter (optional)

The app never needs this; it's only for IDE code intelligence / debugging inside
the container. If you'd rather not deal with it, point PyCharm at a local
virtualenv instead (`backend/.venv`) and keep running the app in Docker.

To use the container as the interpreter:

1. **PyCharm → Add Interpreter → On Docker Compose.**
2. Configuration files: select **both** `docker-compose.yml` **and**
   `docker-compose.ide.yml`.
3. Service: **`api-ide`** (ports-less, so no conflict with the running `api`).
4. Interpreter path: `/usr/local/bin/python3`. Create.

You can keep `docker compose up` running the real API at the same time.
