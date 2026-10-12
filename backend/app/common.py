"""Shared API helpers: pagination, structured errors and CSV responses."""
from __future__ import annotations

import csv
import io
import math
from collections.abc import Iterable
from typing import Any

from fastapi import HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel


class PageParams:
    def __init__(
        self,
        page: int = Query(1, ge=1, description="1-based page number"),
        page_size: int = Query(20, ge=1, le=200, description="Items per page (max 200)"),
    ):
        self.page = page
        self.page_size = page_size

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


def page_response(items: list[Any], total: int, params: PageParams) -> dict:
    return {
        "items": items,
        "total": total,
        "page": params.page,
        "page_size": params.page_size,
        "pages": max(1, math.ceil(total / params.page_size)),
    }


class ErrorBody(BaseModel):
    code: str
    message: str
    details: Any | None = None


class ErrorResponse(BaseModel):
    error: ErrorBody


def not_found(entity: str, ident: Any) -> HTTPException:
    return HTTPException(status_code=404, detail={"code": "not_found", "message": f"{entity} {ident} not found"})


def bad_request(message: str, details: Any = None) -> HTTPException:
    return HTTPException(status_code=400, detail={"code": "bad_request", "message": message, "details": details})


def csv_response(rows: Iterable[dict], filename: str, columns: list[str] | None = None) -> StreamingResponse:
    rows = list(rows)
    columns = columns or (list(rows[0].keys()) if rows else [])
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()
    for r in rows:
        writer.writerow({k: ("; ".join(map(str, v)) if isinstance(v, (list, tuple, set)) else v) for k, v in r.items()})
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


ERROR_RESPONSES = {
    400: {"model": ErrorResponse, "description": "Invalid request"},
    404: {"model": ErrorResponse, "description": "Resource not found"},
    422: {"model": ErrorResponse, "description": "Validation error"},
}
