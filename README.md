# rss-to-email

One-shot RSS/Atom → email job intended to be triggered by cron (typically via Docker).

## Feed list file

Plaintext file containing one RSS/Atom URL per line. Blank lines and `#` comments are ignored.

## State

Uses a small JSON state file to store:

- `last_run_utc` timestamp cutoff
- per-feed `seen_uids` list for dedupe

On the very first run, the default behavior is a warm start (`INITIAL_RUN_SEND=false`): it records the current state and sends no email.

## Environment variables

Required:

- `FEED_LIST_PATH`
- `STATE_PATH`
- `SMTP_HOST`
- `SMTP_PORT` (default `587`)
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `SMTP_FROM`
- `SMTP_TO` (single recipient)

Optional:

- `SMTP_USE_TLS` (default `true`)
- `SMTP_USE_SSL` (default `false`)
- `MAIL_SUBJECT_PREFIX` (default `RSS updates`)
- `USER_AGENT` (default `rss-to-email/0.1`)
- `HTTP_TIMEOUT_SECONDS` (default `20`)
- `MAX_ITEMS_PER_FEED` (default: no limit)
- `SEEN_UIDS_PER_FEED_LIMIT` (default `2000`)
- `INITIAL_RUN_SEND` (default `false`)

## Running locally

```sh
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt

export FEED_LIST_PATH=./feeds.txt
export STATE_PATH=./state.json
export SMTP_HOST=...
export SMTP_USERNAME=...
export SMTP_PASSWORD=...
export SMTP_FROM=...
export SMTP_TO=...

python -m rss_to_email
```

## Running with Docker

```sh
docker build -t rss-to-email .

docker run --rm \
  -v "$PWD/feeds.txt:/data/feeds.txt:ro" \
  -v "$PWD/state.json:/data/state.json" \
  -e FEED_LIST_PATH=/data/feeds.txt \
  -e STATE_PATH=/data/state.json \
  -e SMTP_HOST=... \
  -e SMTP_PORT=587 \
  -e SMTP_USERNAME=... \
  -e SMTP_PASSWORD=... \
  -e SMTP_FROM=... \
  -e SMTP_TO=... \
  rss-to-email
```

## Running with docker-compose

Create `.env` with your SMTP settings, plus any optional vars from above.

Example `feeds.txt` in the repo root, one URL per line.

```sh
docker compose run --rm rss-to-email
```

The feed list is bind-mounted from `./feeds.txt`, and `state.json` is persisted in the named volume `rss_to_email_state`.

## Cron example (host-triggered)

Run every 15 minutes:

```cron
*/15 * * * * docker run --rm \
  -v /path/to/feeds.txt:/data/feeds.txt:ro \
  -v /path/to/state.json:/data/state.json \
  --env-file /path/to/rss-to-email.env \
  rss-to-email
```
