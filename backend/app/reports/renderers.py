import json
from datetime import datetime
from html import escape


def _json_default(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    return str(obj)


def to_json(data: dict) -> str:
    return json.dumps(data, indent=2, default=_json_default)


def _fmt_dt(value) -> str:
    if value is None:
        return "-"
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def to_markdown(data: dict) -> str:
    scan = data["scan"]
    summary = data["summary"]
    lines = [
        f"# J.A.R.V.I.S. Scan Report: {scan['target']}",
        "",
        f"- **Scan ID:** {scan['id']}",
        f"- **Status:** {scan['status']}",
        f"- **Profile:** {scan['profile']}",
        f"- **Created:** {_fmt_dt(scan['created_at'])}",
        f"- **Started:** {_fmt_dt(scan['started_at'])}",
        f"- **Completed:** {_fmt_dt(scan['completed_at'])}",
        "",
        "## Summary",
        "",
        f"- Assets discovered: **{summary['asset_count']}**",
        f"- Findings: **{summary['finding_count']}**",
        "",
    ]
    if summary["findings_by_severity"]:
        lines.append("| Severity | Count |")
        lines.append("|---|---|")
        for sev, count in sorted(summary["findings_by_severity"].items()):
            lines.append(f"| {sev} | {count} |")
        lines.append("")

    lines.append("## Findings")
    lines.append("")
    if not data["findings"]:
        lines.append("No findings recorded for this scan.")
    for f in data["findings"]:
        lines.append(f"### [{f['severity'].upper()}] {f['category']}")
        lines.append("")
        lines.append(f["observation"])
        lines.append("")
        if f["remediation"]:
            lines.append(f"**Remediation:** {f['remediation']}")
            lines.append("")
        lines.append(f"- Confidence: {f['confidence']}")
        lines.append(f"- Human review required: {f['human_review_required']}")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(f["evidence"], indent=2, default=_json_default))
        lines.append("```")
        lines.append("")

    lines.append("## Assets")
    lines.append("")
    lines.append("| Type | Value | Discovered |")
    lines.append("|---|---|---|")
    for a in data["assets"]:
        lines.append(f"| {a['asset_type']} | {a['value']} | {_fmt_dt(a['discovered_at'])} |")

    return "\n".join(lines)


def to_html(data: dict) -> str:
    scan = data["scan"]
    summary = data["summary"]

    severity_rows = "".join(
        f"<tr><td>{escape(sev)}</td><td>{count}</td></tr>"
        for sev, count in sorted(summary["findings_by_severity"].items())
    )

    finding_blocks = "".join(
        f"""
        <div class="finding sev-{escape(f['severity'])}">
          <h3>[{escape(f['severity'].upper())}] {escape(f['category'])}</h3>
          <p>{escape(f['observation'])}</p>
          {f'<p><strong>Remediation:</strong> {escape(f["remediation"])}</p>' if f['remediation'] else ''}
          <p class="meta">Confidence: {f['confidence']} &middot; Human review required: {f['human_review_required']}</p>
          <pre>{escape(json.dumps(f['evidence'], indent=2, default=_json_default))}</pre>
        </div>
        """
        for f in data["findings"]
    ) or "<p>No findings recorded for this scan.</p>"

    asset_rows = "".join(
        f"<tr><td>{escape(a['asset_type'])}</td><td>{escape(a['value'])}</td><td>{escape(_fmt_dt(a['discovered_at']))}</td></tr>"
        for a in data["assets"]
    )

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>J.A.R.V.I.S. Scan Report: {escape(scan['target'])}</title>
<style>
  body {{ background: #0a0b0d; color: #e6e8eb; font-family: -apple-system, sans-serif; max-width: 900px; margin: 40px auto; padding: 0 20px; }}
  h1, h2, h3 {{ font-family: monospace; }}
  table {{ width: 100%; border-collapse: collapse; margin: 12px 0; }}
  th, td {{ text-align: left; padding: 6px 10px; border-bottom: 1px solid #22262c; font-size: 13px; }}
  .finding {{ border: 1px solid #22262c; border-radius: 6px; padding: 14px; margin: 12px 0; }}
  .sev-critical {{ border-left: 4px solid #f87171; }}
  .sev-high {{ border-left: 4px solid #fb923c; }}
  .sev-medium {{ border-left: 4px solid #fbbf24; }}
  .sev-low {{ border-left: 4px solid #60a5fa; }}
  .sev-info {{ border-left: 4px solid #8b929c; }}
  .meta {{ color: #8b929c; font-size: 12px; }}
  pre {{ background: #111317; padding: 10px; border-radius: 4px; overflow-x: auto; font-size: 12px; }}
</style>
</head>
<body>
  <h1>Scan Report: {escape(scan['target'])}</h1>
  <p class="meta">
    Scan ID: {escape(scan['id'])} &middot; Status: {escape(scan['status'])} &middot;
    Profile: {escape(scan['profile'])} &middot; Completed: {escape(_fmt_dt(scan['completed_at']))}
  </p>

  <h2>Summary</h2>
  <p>Assets discovered: <strong>{summary['asset_count']}</strong> &middot; Findings: <strong>{summary['finding_count']}</strong></p>
  <table><tr><th>Severity</th><th>Count</th></tr>{severity_rows}</table>

  <h2>Findings</h2>
  {finding_blocks}

  <h2>Assets</h2>
  <table><tr><th>Type</th><th>Value</th><th>Discovered</th></tr>{asset_rows}</table>
</body>
</html>"""
