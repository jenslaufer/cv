"""Label packs for the template chrome (headings, buttons, fact keys).

Prose lives in ``data/`` (and ``data/en/`` for the English overlay). Only the
fixed furniture of the page lives here. Both packs must carry the same keys —
``tests/test_i18n.py`` fails the build on a missing translation instead of
letting a German word appear in an English CV.
"""
from __future__ import annotations

LABELS: dict[str, dict[str, str]] = {
    "de": {
        "eyebrow": "Freelancer · Softwareentwicklung",
        "pdf_btn": "PDF herunterladen",
        "pdf_aria": "CV als PDF-Datei herunterladen",
        "docx_btn": "Word herunterladen",
        "docx_aria": "CV als Word-Datei herunterladen",
        "print_btn": "Drucken",
        "print_aria": "Lebenslauf drucken",
        "sec_highlights": "Schwerpunkte",
        "sec_roles": "Rollen",
        "sec_skills": "Kenntnisse",
        "sec_projects": "Projekthistorie",
        "sec_contact": "Kontakt & Qualifikation",
        "sub_contact": "Kontakt & Profile",
        "sub_education": "Ausbildung",
        "sub_certificates": "Zertifikate",
        "verify": "Verifizieren →",
        "fact_available": "Verfügbar",
        "fact_worldwide": "Einsatzort",
        "fact_remote": "Remote-Anteil",
        "fact_rate": "Tagessatz",
        "fact_based": "Standort",
        "net": "netto",
        "onsite": "Vor-Ort",
        "country": "Deutschland",
        "c_phone": "Telefon",
        "c_location": "Standort",
        "c_publication": "Publikation",
        "author": "Autor",
        "footer_left": "Jens Laufer · Fullstack · Data · ML · Agentic Engineering · Karlstein am Main",
        "footer_available": "Verfügbar",
        "footer_remote": "Remote",
    },
    "en": {
        "eyebrow": "Freelance · Software Engineering",
        "pdf_btn": "Download PDF",
        "pdf_aria": "Download CV as PDF",
        "docx_btn": "Download Word",
        "docx_aria": "Download CV as a Word file",
        "print_btn": "Print",
        "print_aria": "Print this CV",
        "sec_highlights": "Focus",
        "sec_roles": "Roles",
        "sec_skills": "Skills",
        "sec_projects": "Project history",
        "sec_contact": "Contact & Credentials",
        "sub_contact": "Contact & profiles",
        "sub_education": "Education",
        "sub_certificates": "Certificates",
        "verify": "Verify →",
        "fact_available": "Available",
        "fact_worldwide": "Works",
        "fact_remote": "Remote share",
        "fact_rate": "Day rate",
        "fact_based": "Based in",
        "net": "excl. VAT",
        "onsite": "on-site",
        "country": "Germany",
        "c_phone": "Phone",
        "c_location": "Based in",
        "c_publication": "Publication",
        "author": "author",
        "footer_left": "Jens Laufer · Full-stack · Data · ML · Agentic Engineering · Karlstein am Main, Germany",
        "footer_available": "Available",
        "footer_remote": "remote",
    },
}

DEFAULT_LANG = "de"


def labels(lang: str = DEFAULT_LANG) -> dict[str, str]:
    try:
        return LABELS[lang]
    except KeyError:
        raise ValueError(f"unknown language {lang!r} (have: {', '.join(LABELS)})") from None
