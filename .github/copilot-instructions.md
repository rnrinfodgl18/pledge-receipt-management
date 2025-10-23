# FastAPI with PostgreSQL - Development Guidelines

## Project Overview
This is a Python FastAPI web application with PostgreSQL database integration. The project uses SQLAlchemy ORM for database operations and includes REST API endpoints.

## Tech Stack
- **Framework**: FastAPI
- **Web Server**: Uvicorn
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy
- **Validation**: Pydantic
- **Environment Management**: python-dotenv

## Project Structure
```
.
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Configuration and database setup
│   ├── models.py            # SQLAlchemy ORM models
│   ├── schemas.py           # Pydantic schemas for validation
│   ├── database.py          # Database connection and session
│   └── routes/
│       └── items.py         # API endpoint routes
├── requirements.txt         # Python dependencies
├── .env.example            # Environment variables template
├── README.md               # Project documentation
└── .vscode/
    └── tasks.json          # VS Code tasks
```

## Development Workflow
1. Set up PostgreSQL database and environment variables
2. Run `pip install -r requirements.txt` to install dependencies
3. Use VS Code task or `uvicorn app.main:app --reload` to start dev server
4. API will be available at http://localhost:8000
5. Interactive docs at http://localhost:8000/docs

## Database Configuration
- Update `.env` file with PostgreSQL credentials
- Run database migrations/initialization as needed
- SQLAlchemy handles schema creation automatically

## Key Dependencies
- fastapi: Web framework
- uvicorn: ASGI server
- sqlalchemy: ORM
- psycopg2-binary: PostgreSQL adapter
- pydantic: Data validation
- python-dotenv: Environment configuration
