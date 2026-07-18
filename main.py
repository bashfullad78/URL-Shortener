from fastapi import FastAPI
from routes import analytics, auth, urls
from database import init_db

app = FastAPI()
init_db()
app.include_router(auth.router)
app.include_router(analytics.router)
app.include_router(urls.router)