import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import alerts, companies, insiders, transactions
from app.config import settings
from app.database import Base, engine
from app.etl.scheduler import start_scheduler, stop_scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Starting ETL scheduler...")
    start_scheduler()
    yield
    # Shutdown
    stop_scheduler()


app = FastAPI(
    title="InsiderFlow",
    description="Insider stock trading intelligence dashboard API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(transactions.router)
app.include_router(companies.router)
app.include_router(insiders.router)
app.include_router(alerts.router)


@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "InsiderFlow"}


@app.post("/api/ingest")
def trigger_ingestion():
    """Manually trigger a Form 4 ingestion cycle."""
    from app.etl.ingestion import ingest_recent_filings

    ingest_recent_filings()
    return {"status": "ingestion triggered"}
