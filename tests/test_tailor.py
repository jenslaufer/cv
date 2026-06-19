from gen import parse, render, tailor

JAVA_JOB = """
Senior Java / Spring Boot Backend Engineer (m/w/d)

Wir suchen einen erfahrenen Backend-Entwickler mit tiefer Java- und Spring-Boot-
Erfahrung. Microservices, REST, Docker, Kubernetes, Keycloak und OAuth2 sind Teil
des Stacks. Testgetriebene Entwicklung (JUnit, Mockito) wird vorausgesetzt.
Branche: Versicherung.
"""

ML_JOB = """
Machine Learning Engineer — Python, scikit-learn, pandas, Reinforcement Learning.
Data analysis, clustering, model training on AWS SageMaker.
"""


def test_flagship_always_kept():
    d = parse.parse()
    prof = tailor.build_profile(JAVA_JOB, d, "java-backend")
    assert 0 in prof["include_projects"]


def test_matched_skills_detected():
    d = parse.parse()
    prof = tailor.build_profile(JAVA_JOB, d, "java-backend")
    matched = set(prof["emphasize_skills"])
    assert {"Java", "Spring Boot", "Keycloak", "OAuth2"} <= matched
    # unrelated ML term should not be matched by a backend posting
    assert "scikit-learn" not in matched


def test_relevant_projects_outrank_irrelevant():
    d = parse.parse()
    scores = dict(tailor.score_projects(JAVA_JOB, d))
    # Brunata (id 2): Java/Spring/Keycloak/Microservices — strong match
    # Coop (id 8): pure R/Python ML — weak match for a Java backend role
    assert scores[2] > scores[8]


def test_ml_job_surfaces_ml_projects():
    d = parse.parse()
    scores = dict(tailor.score_projects(ML_JOB, d))
    assert scores[8] > 0  # Coop ML project now relevant
    prof = tailor.build_profile(ML_JOB, d, "ml")
    assert "scikit-learn" in prof["emphasize_skills"]


def test_include_order_is_reverse_chronological():
    d = parse.parse()
    prof = tailor.build_profile(JAVA_JOB, d, "java-backend")
    inc = prof["include_projects"]
    assert inc == sorted(inc)  # CSV row order = newest first = ascending ids


def test_tailored_render_only_includes_selected_projects():
    d = parse.parse()
    prof = tailor.build_profile(JAVA_JOB, d, "java-backend")
    html = render.render(d, tailor.render_profile(prof))
    assert html.count('<article class="entry">') == len(prof["include_projects"])


def test_headline_override_applied():
    d = parse.parse()
    prof = tailor.build_profile(JAVA_JOB, d, "java-backend")
    prof["headline"] = "Senior Java & Spring Boot Backend Engineer"
    html = render.render(d, tailor.render_profile(prof))
    assert "Senior Java &amp; Spring Boot Backend Engineer" in html


def test_tailored_variant_is_noindex():
    d = parse.parse()
    prof = tailor.build_profile(JAVA_JOB, d, "java-backend")
    html = render.render(d, tailor.render_profile(prof))
    assert '<meta name="robots" content="noindex">' in html


def test_base_cv_is_indexable():
    html = render.render(parse.parse())
    assert 'content="noindex"' not in html


def test_facts_unchanged_by_tailoring():
    """Tailoring must never alter the underlying facts — only selection/framing."""
    d = parse.parse()
    prof = tailor.build_profile(JAVA_JOB, d, "java-backend")
    html = render.render(d, tailor.render_profile(prof))
    assert "89 €/h" in html and "ab 01.07.2026" in html
