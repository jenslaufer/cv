"""Render the model (+ optional tailoring profile) into a self-contained CV page.

Everything visible is derived from data/*.csv. A Profile only *selects*, *orders*
and *re-frames* (headline/pitch/highlights) — it never introduces new facts, so
tailored variants cannot drift from the source.
"""
from __future__ import annotations

import html
import re
from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup

from . import parse as _parse
from .labels import DEFAULT_LANG, labels as _labels

HERE = Path(__file__).resolve().parent
CSS = (HERE / "style.css").read_text(encoding="utf-8")

_MD_LINK = re.compile(r"\[([^\]]+)\]\((https?://[^)]+)\)")
_MD_BOLD = re.compile(r"\*\*([^*]+)\*\*")


def md(text: str) -> str:
    """Escape, then apply a tiny safe inline-markdown subset (links, bold)."""
    out = html.escape(text or "", quote=False)
    out = _MD_LINK.sub(lambda m: f'<a href="{html.escape(m.group(2))}">{m.group(1)}</a>', out)
    out = _MD_BOLD.sub(r"<strong>\1</strong>", out)
    return Markup(out)


def _env() -> Environment:
    env = Environment(
        loader=FileSystemLoader(str(HERE)),
        autoescape=select_autoescape(["html", "j2"]),
        trim_blocks=False,
        lstrip_blocks=False,
    )
    env.filters["md"] = md
    return env


def career_years(person: dict) -> int:
    """Years since ``Karrierebeginn`` — the career figure, computed once.

    It used to be typed into the prose ("~16 Jahre ... seit 2009") and was wrong
    on both counts: 2009 is where ``projects.csv`` starts, not where the career
    did. A typed number also cannot age. See tests/test_career_span.py.
    """
    month, year = person["Karrierebeginn"].split("/")
    start = date(int(year), int(month), 1)
    return round((date.today() - start).days / 365.2425)


def _fill(text: str, years: int) -> str:
    return text.replace("{career_years}", str(years)) if text else text


def _project_window(projects: list[dict]) -> str:
    """Earliest year the project list reaches back to — the heading says so.

    23 entries starting in 2009 under a 29-year career reads as a contradiction
    unless the heading names the list as a selection.
    """
    # min over *every* year in every period, not the first period's last year:
    # "05/2009-03/2010" ends in 2010, and reading the end date turned the
    # earliest project into a window that starts a year after it did.
    years = [y for p in projects for y in re.findall(r"\d{2}/(\d{4})", p.get("period", ""))]
    return min(years, default="")


def _facts(data: dict, L: dict, profile: dict | None = None) -> list[dict]:
    k = data["konditionen"]
    p = data["person"]
    profile = profile or {}
    # The rate is negotiated per engagement — the only fact a variant may override.
    rate = _rate(profile.get("rate") or k.get("Tagessatz", ""))
    return [
        {"k": L["fact_available"], "v": k.get("Verfügbarkeit", "")},
        {"k": L["fact_worldwide"], "v": k.get("Einsatzort", "")},
        {"k": L["fact_remote"], "v": data["remote_pct"],
         "small": f"{data['onsite_pct']} {L['onsite']}"},
        {"k": profile.get("rate_label") or L["fact_rate"], "v": rate,
         "small": L["net"], "rate": True},
        {"k": L["fact_based"], "v": p.get("Wohnort", ""), "small": L["country"]},
    ]


def _rate(raw: str) -> str:
    # "2.000 €/Tag (netto)" -> "2.000 €/Tag"
    return re.sub(r"\s*\(.*\)\s*$", "", raw).strip()


def _contact(data: dict, L: dict) -> list[dict]:
    p = data["person"]
    phone = p.get("Telefon", "")
    tel = "tel:" + phone.replace(" ", "")
    pub_href = ""
    m = re.search(r"\((https?://[^)]+)\)", p.get("Sonstiges", ""))
    if m:
        pub_href = m.group(1)
    out = [{"lbl": L["c_phone"], "text": phone, "href": tel}]
    out.append({"lbl": L["c_location"], "text": f"{p.get('Wohnort','')}, {L['country']}"})
    for lbl, key in (("Website", "Website"), ("GitHub", "GitHub"),
                     ("LinkedIn", "LinkedIn"), ("Kaggle", "Kaggle")):
        url = p.get(key, "")
        if url:
            text = re.sub(r"^https?://(www\.)?", "", url).rstrip("/")
            out.append({"lbl": lbl, "text": text, "href": url, "external": True})
    if pub_href:
        out.append({"lbl": L["c_publication"], "text": f"Towards Data Science — {L['author']}",
                    "href": pub_href, "external": True})
    return out


def build_context(data: dict, profile: dict | None = None,
                  lang: str = DEFAULT_LANG) -> dict:
    """Assemble the template context, applying the tailoring profile if given."""
    profile = profile or {}
    p = data["person"]
    L = _labels(lang)

    # --- projects: select + order (facts always from data/*.csv by id) ---
    by_id = {pr["id"]: pr for pr in data["projects"]}
    order = profile.get("include_projects")
    if order:
        projects = [by_id[i] for i in order if i in by_id]
    else:
        projects = list(data["projects"])

    # --- skills: optionally surface matched groups/tags first ---
    skills = _order_skills(data["skills"], profile.get("emphasize_skills"))

    # --- the career figure is computed, never carried in the prose ---
    years = career_years(p)
    L = dict(L, sec_projects=L["sec_projects"].format(von=_project_window(projects)))

    name = p.get("Name", "")
    role_line = _fill(profile.get("headline") or p.get("Titel/Positionierung", ""), years)
    stack_line = _fill(profile.get("stack_line") or p.get("Untertitel", ""), years)
    pitch = _fill(profile.get("pitch") or p.get("Pitch", ""), years)
    highlights = [_fill(h, years) for h in (profile.get("highlights") or data["highlights"])]
    eyebrow = profile.get("eyebrow") or L["eyebrow"]
    kond = data["konditionen"]
    footer_right = " · ".join([
        f"{L['footer_available']} {kond.get('Verfügbarkeit', '')}",
        kond.get("Einsatzort", ""),
        f"{data['remote_pct']} {L['footer_remote']}",
    ])

    return {
        "L": L,
        "html_lang": lang,
        "title": _fill(profile.get("title") or p.get("SEO-Titel"), years) or f"{name} — {role_line}",
        "description": _fill(profile.get("description"), years) or pitch,
        "css": CSS,
        "noindex": profile.get("noindex", False),
        "asset_prefix": profile.get("asset_prefix", ""),
        # {"href", "hreflang", "label"} on the two base pages, None on tailored
        # variants — those are single-language, so a switch there is a 404.
        "lang_switch": profile.get("lang_switch"),
        "pdf_href": profile.get("pdf_href", "cv.pdf"),
        "pdf_download": profile.get("pdf_download", "Jens-Laufer-CV.pdf"),
        "docx_href": profile.get("docx_href", "cv.docx"),
        "docx_download": profile.get("docx_download", "Jens-Laufer-CV.docx"),
        "eyebrow": eyebrow,
        "name": name,
        "role_line": role_line,
        "stack_line": stack_line,
        "pitch": pitch,
        "facts": _facts(data, L, profile),
        "highlights": highlights,
        "roles": data["roles"],
        "skills": skills,
        "projects": projects,
        "contact": _contact(data, L),
        "education": data["education"],
        "certificates": data["certificates"],
        "footer_left": profile.get("footer_left", L["footer_left"]),
        "footer_right": profile.get("footer_right", footer_right),
    }


def _order_skills(skills: list[dict], emphasize: list[str] | None) -> list[dict]:
    if not emphasize:
        return skills
    want = {e.lower() for e in emphasize}

    def score(group: dict) -> int:
        return sum(1 for t in group["tags"] if t.lower() in want)

    # stable sort: groups with matched tags first, original order preserved within
    return sorted(skills, key=lambda g: (-score(g),), reverse=False)


def render(data: dict, profile: dict | None = None, lang: str = DEFAULT_LANG) -> str:
    ctx = build_context(data, profile, lang)
    tmpl = _env().get_template("template.html.j2")
    return tmpl.render(**ctx).rstrip() + "\n"


def render_from_source(path=None, profile: dict | None = None,
                       lang: str = DEFAULT_LANG) -> str:
    return render(_parse.parse(path, lang), profile, lang)
