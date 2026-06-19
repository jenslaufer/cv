from gen import parse


def test_counts():
    d = parse.parse()
    assert len(d["projects"]) == 21
    assert len(d["skills"]) == 11
    assert len(d["roles"]) == 10
    assert len(d["education"]) == 2
    assert len(d["certificates"]) == 2


def test_flagship_project():
    d = parse.parse()
    p0 = d["projects"][0]
    assert p0["id"] == 0
    assert p0["client"] == "Solytics GmbH"
    assert p0["location"] == "Remote"
    assert p0["branch"] == "KI / SaaS"
    assert p0["dur"] == "laufend"
    assert "Claude / Anthropic API" in p0["tech"]
    # roles split on commas even though the section uses '·'
    assert "Harness Engineering" in p0["roles"]


def test_client_location_variants():
    d = parse.parse()
    by_id = {p["id"]: p for p in d["projects"]}
    # parens + trailing comma: 'Co-operative Group (Coop), Manchester'
    coop = by_id[8]
    assert coop["client"] == "Co-operative Group (Coop)"
    assert coop["location"] == "Manchester"
    # comma form, no parens: 'Deutsche Verrechnungstelle / DVAG, Frankfurt a. Main'
    dvag = by_id[10]
    assert dvag["client"] == "Deutsche Verrechnungstelle / DVAG"
    assert dvag["location"] == "Frankfurt a. Main"


def test_duration_expanded():
    d = parse.parse()
    durs = {p["dur"] for p in d["projects"]}
    assert "12 Monate" in durs
    assert not any("Mon." in x for x in durs)


def test_aws_tag_not_split_inside_parens():
    d = parse.parse()
    devops = next(g for g in d["skills"] if g["name"].startswith("DevOps"))
    assert "AWS (EC2, S3, SageMaker, VPC)" in devops["tags"]


def test_certificate_url_extracted():
    d = parse.parse()
    cert = d["certificates"][0]
    assert cert["url"].startswith("https://confirm.udacity.com/")
    assert cert["org"] == "Udacity"
