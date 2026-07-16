# Times Table Bot

A private, invitation-only Telegram bot for learning multiplication and related exact division facts from 1 through 10. The Telegram platform is topic-independent; all mathematics lives behind the `TopicModule` contract.

The project targets Python 3.14, aiogram 3, PostgreSQL, async SQLAlchemy, Alembic, Pillow, and Docker Compose. It uses long polling, so no public domain, webhook, or TLS certificate is needed.

## Quick start

1. Create a bot with [BotFather](https://t.me/BotFather), keep the token private, and note the bot username.
2. Send any message to the bot, then obtain the teacher’s numeric Telegram ID from `https://api.telegram.org/bot<TOKEN>/getUpdates` in the returned message’s `from.id` field. Delete the token from browser history afterward.
3. Configure the application:

```bash
cp .env.example .env
chmod 600 .env
```

Fill every secret or identity field. Generate a strong database password, for example with `openssl rand -hex 24`. `ADMIN_TELEGRAM_ID` must be the one teacher account.

4. Build the database, run the migration, and start the bot:

```bash
docker compose up -d db
docker compose run --rm bot alembic upgrade head
docker compose up -d --build bot
docker compose ps
docker compose logs --tail=100 bot
```

The normal bot container also runs `alembic upgrade head` before polling, making restarts safe. The explicit migration command above makes the schema step visible during first setup.

Open `/admin` as the configured teacher, select **Invite link**, and generate the first invitation. Students join only through that deep link.

## Environment variables

- `BOT_TOKEN`: required BotFather token; secret.
- `BOT_USERNAME`: bot username without `@`.
- `ADMIN_TELEGRAM_ID`: positive numeric ID of the single teacher.
- `POSTGRES_PASSWORD`: strong database password used by Compose; secret.
- `DATABASE_URL`: async PostgreSQL URL. Compose supplies its internal URL to the bot.
- `DEFAULT_TIMEZONE`: IANA timezone, normally `Europe/Zurich`.
- `DEFAULT_REMINDER_HOUR`: whole hour from 07 through 20.
- `DEFAULT_REMINDER_DAYS`: `DAILY`, `WEEKDAYS`, `MWF`, or `OFF`.
- `ENABLED_TOPIC_IDS`: comma-separated topic IDs; production uses `times_tables`.
- `DEFAULT_TOPIC_ID`: must be included in the enabled list.
- `APP_ENV`: `development`, `test`, or `production`.
- `LOG_LEVEL`: standard logging level such as `INFO`.

The application refuses to start with invalid secrets, identity, timezone, topic, content, database, or migration state. `.env` and `metadata.py` are excluded from Git and Docker build contexts.

## Local development and tests

Use Python 3.14 and a PostgreSQL test database:

```bash
python3.14 -m venv .venv
.venv/bin/pip install -e '.[dev]'
docker run --rm -d --name times-bot-test-db \
  -e POSTGRES_PASSWORD=test -e POSTGRES_USER=mathbot -e POSTGRES_DB=mathbot \
  -p 55432:5432 postgres:17.9-alpine
export TEST_DATABASE_URL=postgresql+asyncpg://mathbot:test@127.0.0.1:55432/mathbot
```

Run the complete quality suite:

```bash
ruff check .
ruff format --check .
mypy app tests
pytest
python scripts/validate_topics.py
python scripts/validate_content.py
```

Verify an empty database migration and model alignment:

```bash
alembic upgrade head
alembic check
```

Regenerate deterministic assets with:

```bash
python scripts/generate_times_table_images.py
```

## Operations

Follow logs without printing environment variables:

```bash
docker compose logs -f --tail=100 bot
```

Create a PostgreSQL backup:

```bash
docker compose exec -T db pg_dump -U mathbot -Fc mathbot > mathbot.backup
```

Restore into an empty database during maintenance:

```bash
docker compose stop bot
docker compose exec -T db dropdb -U mathbot --if-exists mathbot
docker compose exec -T db createdb -U mathbot mathbot
docker compose exec -T db pg_restore -U mathbot -d mathbot --clean --if-exists < mathbot.backup
docker compose up -d bot
```

Deploy updates from GitHub:

```bash
git pull --ff-only
docker compose build --pull bot
docker compose run --rm bot alembic upgrade head
docker compose up -d bot
```

Never place `.env`, `metadata.py`, a BotFather token, or a database dump in Git. Transfer production secrets directly to the server over SSH and restrict the file to the deployment user.

See [TOPIC_DEVELOPMENT_GUIDE.md](TOPIC_DEVELOPMENT_GUIDE.md) for the extension contract and [ACCEPTANCE_CHECKLIST.md](ACCEPTANCE_CHECKLIST.md) for verification evidence.

