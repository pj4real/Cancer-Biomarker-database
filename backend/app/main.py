"""CancerBioMap FastAPI application."""
import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy import text

from app.config import get_settings
from app.database import SessionLocal
from app.routers import analysis, catalog, evidence

logger = logging.getLogger("cancerbiomap")

DESCRIPTION = """
**CancerBioMap** integrates cancer biomarkers, genes, proteins, pathways, variants and
publications, and computes a transparent **evidence-support score** for every
biomarker-cancer association.

*For research and education only. Scores summarise evidence recorded in this database;
they are not probabilities of clinical validity and do not indicate clinical approval.*
"""

app = FastAPI(title="CancerBioMap API", version="1.1.0", description=DESCRIPTION)
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origin_list,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-Admin-Token"],
)


@app.exception_handler(HTTPException)
async def http_error(_: Request, exc: HTTPException):
    if isinstance(exc.detail, dict):
        body = exc.detail
    else:
        body = {"code": "http_error", "message": str(exc.detail)}
    return JSONResponse(status_code=exc.status_code, content={"error": body})


@app.exception_handler(RequestValidationError)
async def validation_error(_: Request, exc: RequestValidationError):
    details = [{"location": ".".join(str(p) for p in e["loc"]), "message": e["msg"]} for e in exc.errors()]
    return JSONResponse(status_code=422, content={"error": {
        "code": "validation_error", "message": "Request parameters are invalid", "details": details}})


@app.exception_handler(Exception)
async def unhandled_error(_: Request, exc: Exception):
    # Never leak internal exception text or SQL to clients.
    logger.exception("Unhandled error", exc_info=exc)
    return JSONResponse(status_code=500, content={"error": {
        "code": "internal_error", "message": "An unexpected error occurred"}})


@app.get("/api/health", tags=["Meta"])
def health():
    with SessionLocal() as db:
        db.execute(text("SELECT 1"))
    return {"status": "ok"}


app.include_router(catalog.router)
app.include_router(evidence.router)
app.include_router(analysis.router)


# Single-service deployment: when the React build exists (npm run build), serve it from the same origin so
# the frontend's relative /api calls need no proxy or CORS. In local development Vite serves the UI instead.
FRONTEND_DIST = (Path(__file__).resolve().parents[2] / "frontend" / "dist").resolve()

if (FRONTEND_DIST / "index.html").is_file():
    @app.get("/{full_path:path}", include_in_schema=False)
    def frontend(full_path: str):
        if full_path == "api" or full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Unknown API path"})
        candidate = (FRONTEND_DIST / full_path).resolve()
        if full_path and candidate.is_file() and candidate.is_relative_to(FRONTEND_DIST):
            return FileResponse(candidate)
        # Client-side routes (for example /biomarkers/22) all load the SPA shell.
        return FileResponse(FRONTEND_DIST / "index.html")
