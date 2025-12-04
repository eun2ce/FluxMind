# FluxMind

Event-driven LLM chatbot backend monorepo built with Polylith architecture.

## Architecture

- `components/fluxmind/`: Reusable components (domain_core, conversation, llm, mq, database, analytics, etc.)
- `bases/fluxmind/`: Service layers (api, events_consumer, worker, migrations)
- `projects/fluxmind-*`: Entry points for each runtime

## Quick Start

### Docker Compose (Recommended)

**1. Download Ollama Model (one-time setup):**
```bash
docker-compose up -d ollama
docker exec fluxmind-ollama ollama pull llama3.1
```

**2. Run Database Migrations:**
```bash
docker-compose --profile migrations up db-migrations
```

**3. Start All Services:**
```bash
docker-compose up -d
```

### Manual Setup

### 1. Start Infrastructure

```bash
docker-compose -f development/infra/docker-compose.ollama.yml up -d
```

This starts Postgres, Kafka, Redis, and Ollama.

### 2. Download Ollama Model

```bash
docker exec fluxmind-ollama ollama pull llama3.1
```

### 3. Run Database Migrations

```bash
uv run python -m projects.fluxmind_db_migrations.main upgrade head
```

### 4. Run Services

**API Server:**
```bash
uv run python -m projects.fluxmind-api.main
```

**Event Consumer:**
```bash
uv run python -m projects.fluxmind-events-consumer.main
```

**Worker (Archive Job):**
```bash
uv run python -m projects.fluxmind-worker.main
```

### 5. Test

```bash
TOKEN=$(docker-compose exec -T api uv run python -c "from fluxmind.jwt.token import create_access_token; from datetime import timedelta; print(create_access_token({'sub': 'test-user'}, timedelta(hours=1)))") && curl -X POST http://localhost:8000/conversations -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" -d '{"initial_message": "Hello"}'
```

## Environment Variables

Configure via `.env` file or environment variables:

```bash
FLUXMIND_API_PORT=8000
FLUXMIND_MQ_URL=kafka://localhost:9092
FLUXMIND_MQ_TOPIC_CONVERSATION_EVENTS=conversation-events
FLUXMIND_MQ_GROUP_ID_EVENTS_CONSUMER=fluxmind-events-consumer
FLUXMIND_DB_URL=postgresql+asyncpg://fluxmind:fluxmind@localhost:5432/fluxmind
FLUXMIND_OLLAMA_BASE_URL=http://localhost:11434
FLUXMIND_OLLAMA_MODEL=llama3.1
FLUXMIND_WORKER_ARCHIVE_INTERVAL_SECONDS=3600
FLUXMIND_WORKER_ARCHIVE_OLDER_THAN_DAYS=30
```

## Development

### Install Dependencies

```bash
uv sync
```

### Run Tests

```bash
uv run pytest tests/
```

### Code Quality

**Lint:**
```bash
uv run ruff check .
```

**Format:**
```bash
uv run ruff format .
```

## Project Structure

This project follows the [Polylith](https://polylith.gitbook.io/polylith) architecture:

- **Components**: Reusable business logic and domain models
- **Bases**: Service implementations (API, event consumers, workers)
- **Projects**: Deployment units that compose components and bases

## Technology Stack

- **FastAPI**: Web framework
- **SQLAlchemy**: ORM with async support
- **Alembic**: Database migrations
- **Kafka**: Message queue for event-driven communication
- **Ollama**: Local LLM inference
- **Pydantic**: Data validation and settings management
- **pytest**: Testing framework
- **ruff**: Linting and formatting
