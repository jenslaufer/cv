"""Tailoring layer — turn a job posting into a focused CV variant.

A job posting is matched against the project history and skill vocabulary in
data/*.csv. The result is a *profile*: which projects to keep (newest first), which
skill groups to surface, and a suggested headline. The profile only selects and
re-frames — every fact still comes from data/*.csv, so a tailored CV can never
diverge from the source.

The profile is written to disk as YAML so it can be hand-tuned (headline, pitch,
project selection) and re-rendered without re-running the matcher.
"""
from __future__ import annotations

import re
from pathlib import Path

# The flagship/current engagement is always kept, regardless of keyword overlap.
ALWAYS_KEEP = {0}


def _vocabulary(data: dict) -> set[str]:
    vocab: set[str] = set()
    for g in data["skills"]:
        vocab.update(t for t in g["tags"])
    for p in data["projects"]:
        vocab.update(p["tech"])
        vocab.update(p["roles"])
    vocab.update(data["roles"])
    return vocab


def _terms_in(text: str, vocab: set[str]) -> set[str]:
    """Vocabulary terms that literally appear in the job text (case-insensitive)."""
    low = text.lower()
    found = set()
    for term in vocab:
        t = term.lower()
        # unicode word boundary so 'R' doesn't match the 'r' in 'für'
        if re.search(r"(?<!\w)" + re.escape(t) + r"(?!\w)", low):
            found.add(term)
    return found


def score_projects(job_text: str, data: dict) -> list[tuple[int, int]]:
    """Return (project_id, score) pairs, highest score first, ties by recency."""
    matched = _terms_in(job_text, _vocabulary(data))
    matched_low = {m.lower() for m in matched}
    scored = []
    for p in data["projects"]:
        terms = {t.lower() for t in p["tech"]} | {r.lower() for r in p["roles"]}
        score = len(terms & matched_low)
        # branch overlap is a soft signal
        if p["branch"] and any(b.strip().lower() in job_text.lower()
                               for b in p["branch"].split(",")):
            score += 1
        scored.append((p["id"], score))
    scored.sort(key=lambda s: (-s[1], s[0]))
    return scored


def build_profile(job_text: str, data: dict, slug: str,
                  title: str | None = None, top: int = 12) -> dict:
    """Derive a tailoring profile from a job posting.

    Keeps the flagship engagement plus the `top` most relevant projects, so the
    variant is focused rather than the full 21-project history. Projects render
    newest first; drop/reorder by hand in profile.yaml if needed.
    """
    matched = _terms_in(job_text, _vocabulary(data))
    scored = score_projects(job_text, data)
    by_id = dict(scored)

    keep = set(ALWAYS_KEEP) | {pid for pid, _ in scored[:top]}
    # render newest first (CSV row order is already reverse-chronological)
    include = [p["id"] for p in data["projects"] if p["id"] in keep]

    emphasize = sorted(matched, key=lambda t: t.lower())

    return {
        "slug": slug,
        "title": title or f"Jens Laufer — {slug}",
        # headline/pitch left for hand-tuning; sensible defaults from the source
        "headline": "",
        "stack_line": "",
        "pitch": "",
        "highlights": [],
        "include_projects": include,
        "emphasize_skills": emphasize,
        "_scores": {pid: by_id[pid] for pid in include},
    }


# ---- profile <-> disk -------------------------------------------------------

def _clean_profile(profile: dict) -> dict:
    """Drop empty override keys and private (_-prefixed) annotations for render."""
    out = {}
    for k, v in profile.items():
        if k.startswith("_"):
            continue
        if v in ("", [], None):
            continue
        out[k] = v
    return out


def render_profile(profile: dict) -> dict:
    """A profile ready to pass to render.build_context (overrides applied)."""
    p = _clean_profile(profile)
    slug = p.get("slug", "tailored")
    p.setdefault("pdf_href", f"{slug}.pdf")
    p.setdefault("pdf_download", f"Jens-Laufer-CV-{slug}.pdf")
    # tailored variants live in a subfolder; assets sit at the repo root
    p.setdefault("asset_prefix", "../../")
    p.setdefault("docx_href", "")  # no per-variant Word by default
    p.setdefault("noindex", True)  # tailored variants are private per-recruiter links
    return p
