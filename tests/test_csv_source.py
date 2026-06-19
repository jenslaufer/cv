"""The source of truth is data/*.csv — not data.md, not index.html.

These tests pin the CSV-source contract: the files exist, the parser reads them
(including an alternative data dir), list cells survive round-trips, and the old
markdown source is gone so it cannot silently drift back in.
"""
import csv
from pathlib import Path

import pytest

from gen import parse

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

EXPECTED_CSVS = {
    "person.csv", "konditionen.csv", "roles.csv", "highlights.csv",
    "skills.csv", "projects.csv", "education.csv", "certificates.csv",
}


def test_all_source_csvs_present():
    present = {p.name for p in DATA.glob("*.csv")}
    assert EXPECTED_CSVS <= present, f"missing: {EXPECTED_CSVS - present}"


def test_markdown_source_is_gone():
    # data.md was the old source; CSVs replaced it. Its return would mean two
    # sources of truth and silent drift.
    assert not (ROOT / "data.md").exists(), "data.md must not be the source anymore"


def test_parse_reads_an_alternative_data_dir(tmp_path):
    # minimal data dir -> parse must read from it, proving it is CSV-driven
    (tmp_path / "person.csv").write_text("field,value\nName,Test Person\n", encoding="utf-8")
    (tmp_path / "konditionen.csv").write_text(
        "field,value\nAnteil Vor-Ort,10 %\nAnteil Remote,90 %\n", encoding="utf-8")
    (tmp_path / "roles.csv").write_text("role\nBackend\n", encoding="utf-8")
    (tmp_path / "highlights.csv").write_text("highlight\nHi\n", encoding="utf-8")
    (tmp_path / "skills.csv").write_text("group,skill\nLang,Java\nLang,Python\n", encoding="utf-8")
    (tmp_path / "projects.csv").write_text(
        "id,period,dur,title,client,location,branch,roles,desc,tech\n"
        '0,2025,laufend,T,C,Remote,KI,Backend; DevOps,Desc,"AWS (EC2, S3); Docker"\n',
        encoding="utf-8")
    (tmp_path / "education.csv").write_text("date,title,org\n2000,Dipl,Uni\n", encoding="utf-8")
    (tmp_path / "certificates.csv").write_text("date,title,org,url\n2018,ML,Udacity,\n", encoding="utf-8")

    d = parse.parse(tmp_path)
    assert d["person"]["Name"] == "Test Person"
    assert d["onsite_pct"] == "10 %" and d["remote_pct"] == "90 %"
    assert d["skills"] == [{"name": "Lang", "tags": ["Java", "Python"]}]
    p0 = d["projects"][0]
    assert p0["roles"] == ["Backend", "DevOps"]
    # comma INSIDE a tech item survives because items are joined with '; '
    assert p0["tech"] == ["AWS (EC2, S3)", "Docker"]


def test_tech_comma_in_parens_preserved_from_real_data():
    d = parse.parse()
    devops = next(g for g in d["skills"] if g["name"].startswith("DevOps"))
    assert "AWS (EC2, S3, SageMaker, VPC)" in devops["tags"]


def test_skills_grouped_in_first_appearance_order():
    d = parse.parse()
    names = [g["name"] for g in d["skills"]]
    assert names[0] == "Sprachen"
    assert len(names) == len(set(names)), "groups must be merged, not duplicated"
