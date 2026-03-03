from fastapi import FastAPI

from app.routes.ingest import router as ingest_router

app = FastAPI(title="Legal AI Tool — Agent Backend", version="0.1.0")

app.include_router(ingest_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
