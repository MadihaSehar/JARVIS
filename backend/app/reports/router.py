from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

from app.reports.builder import build_report
from app.reports.renderers import to_html, to_json, to_markdown

router = APIRouter(prefix="/api/scans", tags=["reports"])

RENDERERS = {
    "json": (to_json, "application/json", "json"),
    "markdown": (to_markdown, "text/markdown", "md"),
    "html": (to_html, "text/html", "html"),
}


@router.get("/{scan_id}/report")
async def get_scan_report(
    scan_id: str,
    format: str = Query("json", pattern="^(json|markdown|html)$"),
):
    data = build_report(scan_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Scan not found")

    render, media_type, ext = RENDERERS[format]
    body = render(data)
    filename = f"jarvis-report-{scan_id}.{ext}"
    return Response(
        content=body,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
