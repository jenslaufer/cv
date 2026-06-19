"""Export a rendered CV to PDF and Word — both derived from the same source.

PDF: headless Chromium prints the generated HTML (same engine that produced the
original cv.pdf), so the PDF matches the print stylesheet exactly.

Word: a clean, editable .docx built from the model. It does not pixel-match the
HTML (recruiters want editable text), but it is generated from data/*.csv, so it
stays in sync with everything else.
"""
from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

CHROMIUM_CANDIDATES = ["chromium", "chromium-browser", "google-chrome", "chrome"]


def _chromium() -> str:
    for c in CHROMIUM_CANDIDATES:
        if shutil.which(c):
            return c
    raise RuntimeError("no chromium/chrome binary found for PDF export")


def to_pdf(html_path: str | Path, pdf_path: str | Path) -> Path:
    html_path, pdf_path = Path(html_path).resolve(), Path(pdf_path).resolve()
    with tempfile.TemporaryDirectory() as profile:
        cmd = [
            _chromium(), "--headless", "--no-sandbox", "--disable-gpu",
            f"--user-data-dir={profile}", "--no-pdf-header-footer",
            "--virtual-time-budget=8000",
            f"--print-to-pdf={pdf_path}", html_path.as_uri(),
        ]
        # Chromium emits harmless dbus/AppArmor warnings to stderr and a non-zero
        # exit even on success, so success is judged by the output file, not rc.
        subprocess.run(cmd, capture_output=True, timeout=120)
    if not pdf_path.exists() or pdf_path.stat().st_size < 1000:
        raise RuntimeError(f"PDF export produced no usable file at {pdf_path}")
    return pdf_path


def to_docx(data: dict, path: str | Path, profile: dict | None = None) -> Path:
    from docx import Document
    from docx.shared import Pt, RGBColor

    profile = profile or {}
    person = data["person"]
    accent = RGBColor(0x0A, 0x46, 0x40)

    by_id = {p["id"]: p for p in data["projects"]}
    order = profile.get("include_projects")
    projects = [by_id[i] for i in order if i in by_id] if order else data["projects"]

    doc = Document()
    doc.add_heading(person.get("Name", ""), level=0)
    sub = doc.add_paragraph()
    run = sub.add_run(profile.get("headline") or person.get("Titel/Positionierung", ""))
    run.bold = True
    doc.add_paragraph(person.get("Untertitel", ""))

    kond = data["konditionen"]
    doc.add_paragraph(
        f"Verfügbar {kond.get('Verfügbarkeit','')} · {kond.get('Einsatzort','')} · "
        f"Remote {data['remote_pct']} · {kond.get('Rate Remote','')} remote / "
        f"{kond.get('Rate Vor-Ort','')} vor Ort"
    )

    def heading(text):
        h = doc.add_heading(text, level=1)
        for r in h.runs:
            r.font.color.rgb = accent

    heading("Schwerpunkte")
    for h in (profile.get("highlights") or data["highlights"]):
        clean = h.replace("**", "")
        doc.add_paragraph(clean, style="List Bullet")

    heading("Kenntnisse")
    for g in data["skills"]:
        p = doc.add_paragraph()
        p.add_run(f"{g['name']}: ").bold = True
        p.add_run(", ".join(g["tags"]))

    heading("Projekthistorie")
    for pr in projects:
        head = doc.add_paragraph()
        r = head.add_run(f"{pr['period']} ({pr['dur']}) — {pr['title']}")
        r.bold = True
        meta = " · ".join(x for x in (pr["client"], pr["location"], pr["branch"]) if x)
        doc.add_paragraph(meta)
        if pr["roles"]:
            doc.add_paragraph("Rollen: " + " · ".join(pr["roles"]))
        doc.add_paragraph(pr["desc"].replace("**", ""))
        if pr["tech"]:
            doc.add_paragraph("Tech: " + ", ".join(pr["tech"]))

    heading("Ausbildung & Zertifikate")
    for e in data["education"] + data["certificates"]:
        p = doc.add_paragraph()
        p.add_run(f"{e['date']} — {e['title']}").bold = True
        p.add_run(f", {e['org']}")

    heading("Kontakt")
    for key in ("Telefon", "Website", "GitHub", "LinkedIn", "Kaggle"):
        if person.get(key):
            doc.add_paragraph(f"{key}: {person[key]}")

    path = Path(path)
    doc.save(str(path))
    return path
