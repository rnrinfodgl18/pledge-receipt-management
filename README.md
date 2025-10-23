# FastAPI with PostgreSQL

A modern Python web application built with **FastAPI** and **PostgreSQL**.

## Features

- 🚀 FastAPI web framework with async support
- 🗄️ PostgreSQL database with SQLAlchemy ORM
- ✅ Pydantic data validation
- 📚 Interactive API documentation (Swagger UI)
- 🔄 CRUD operations for items
- 🏥 Health check endpoint

## Prerequisites

- Python 3.8+
- PostgreSQL 12+
- pip or conda

## Quick Start

### 1. Clone and Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Create .env file from template
cp .env.example .env
```

### 2. Configure Database

Update `.env` with your PostgreSQL credentials:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/fastapi_db
```

Ensure PostgreSQL is running and the database exists:

```sql
CREATE DATABASE fastapi_db;
```

### 3. Run the Application

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### 4. Access Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## Project Structure

```
.
├── app/
│   ├── __init__.py              # Package initialization
│   ├── main.py                  # FastAPI app entry point
│   ├── database.py              # SQLAlchemy setup
│   ├── models.py                # ORM models
│   ├── schemas.py               # Pydantic schemas
│   └── routes/
│       ├── __init__.py
│       └── items.py             # Item CRUD routes
├── .env.example                 # Environment template
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## API Endpoints

### Health & Status
- `GET /` - Welcome message
- `GET /health` - Health check

### Items
- `POST /items` - Create a new item
- `GET /items` - List all items (with pagination)
- `GET /items/{item_id}` - Get a specific item
- `PUT /items/{item_id}` - Update an item
- `DELETE /items/{item_id}` - Delete an item

## Example Usage

### Create an Item

```bash
curl -X POST "http://localhost:8000/items" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Laptop",
    "description": "A powerful laptop",
    "price": 100000
  }'
```

### List Items

```bash
curl "http://localhost:8000/items?skip=0&limit=10"
```

### Get Item by ID

```bash
curl "http://localhost:8000/items/1"
```

### Update Item

```bash
curl -X PUT "http://localhost:8000/items/1" \
  -H "Content-Type: application/json" \
  -d '{
    "price": 95000
  }'
```

### Delete Item

```bash
curl -X DELETE "http://localhost:8000/items/1"
```

## Development

### Database Migrations

The application automatically creates tables on startup. For more advanced migrations, consider using Alembic:

```bash
pip install alembic
alembic init migrations
```

### Running Tests

Create a `tests/` directory and run tests with pytest:

```bash
pip install pytest pytest-asyncio httpx
pytest
```

## Troubleshooting

### Connection refused to PostgreSQL

- Ensure PostgreSQL is running
- Check `DATABASE_URL` in `.env`
- Verify database exists: `psql -l`

### Import errors after installing dependencies

- Ensure virtual environment is activated
- Reinstall dependencies: `pip install -r requirements.txt`

### Rust/Cargo compilation errors during deployment

If you encounter errors about `maturin`, `cargo`, or "Read-only file system" when deploying:

- Use the provided `build.sh` script for deployment
- Set build command to `bash build.sh` on your platform
- See [BUILD_FIX.md](BUILD_FIX.md) for detailed information

## Technology Stack

| Tool | Version | Purpose |
|------|---------|---------|
| FastAPI | 0.109.0 | Web framework |
| Uvicorn | 0.27.0 | ASGI server |
| SQLAlchemy | 2.0.23 | ORM |
| Psycopg2 | 2.9.9 | PostgreSQL adapter |
| Pydantic | 2.5.0 | Data validation |
| Python-dotenv | 1.0.0 | Environment management |

## License

MIT License - feel free to use this project as a template.

## Next Steps

- Add authentication and authorization
- Implement comprehensive error handling
- Add logging and monitoring
- Create API tests
- Deploy to production (Docker, Kubernetes, etc.)
