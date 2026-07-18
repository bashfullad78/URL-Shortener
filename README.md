# URL Shortener with Analytics

A backend REST API that lets users shorten URLs and track engagement through 
click analytics, including daily breakdowns and summary statistics per link.

## Tech Stack

Language: Python
Framework: FastAPI, Pydantic
Database: PostgreSQL (raw SQL)
Auth: JWT via python jose, bcrypt password hashing
Driver: psycopg2

## Setup

### Prerequisites
- Python 3.10+
- PostgreSQL running locally

### Installation
```bash
git clone <your-repo>
cd url-shortener
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Database Setup
```bash
sudo -u postgres psql
CREATE DATABASE urlshortener;
CREATE USER youruser WITH PASSWORD 'yourpassword';
GRANT ALL PRIVILEGES ON DATABASE urlshortener TO youruser;
\q
```

Create a `.env` file in root:
DATABASE_URL=postgresql://youruser:yourpassword@localhost/urlshortener
SECRET_KEY=yoursecretkey
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

### Run
```bash
uvicorn main:app --reload
```

## API Endpoints

## API Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | /auth/register | Register a new user | No |
| POST | /auth/login | Login and receive JWT token | No |
| POST | /urls | Create a shortened URL | Yes |
| GET | /urls | List all your shortened URLs | Yes |
| GET | /{short_code} | Redirect to original URL | No |
| DELETE | /urls/{url_id} | Delete a shortened URL | Yes |
| GET | /urls/{url_id}/analytics/summary | Total clicks, first and last click date | Yes |
| GET | /urls/{url_id}/analytics/daily | Clicks grouped by day | Yes |

## Design Decisions

Raw SQL over ORM: deliberate choice to maintain visibility into queries,
especially for analytics aggregations where ORM abstractions obscure performance.
PostgreSQL over SQLite: production grade database supporting concurrent users
and native INET type for IP address storage.
Click tracking at redirect time: every redirect atomically records the click
and increments the counter in the same transaction, keeping counts accurate.

## Future Improvements

Rate limiting via slowapi, pytest coverage, Docker containerization,
GitHub Actions CI/CD pipeline, custom short code support.
