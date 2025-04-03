from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from routes import router
from utils import init_db
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup event
    init_db()  # Note: init_db is synchronous, but we can call it directly since it doesn't need to be awaited
    yield
    # Shutdown event (if needed)
    # Add cleanup code here if necessary

app = FastAPI(lifespan=lifespan)

# Setup for templates
templates = Jinja2Templates(directory="templates")

# Include routes from routes.py
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)