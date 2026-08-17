"""Command-line interface for the CV generator.

  python -m gen build                       # regenerate base index.html (+ --pdf --docx)
  python -m gen tailor --job posting.txt --slug acme [--title "..."]
  python -m gen tailor --profile tailored/acme/profile.yaml   # re-render after editing
  python -m gen check                       # fail if index.html or any tailored variant is stale
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

from . import parse as _parse
from . import render as _render
from . import tailor as _tailor
from . import exporters

ROOT = Path(__file__).resolve().parent.parent

# Every language that is actually *served*, and the chrome that makes the pair
# navigable. The English CV existed as data (data/en/) for three days while
# `build` still only ever wrote the German index.html — so cv.jenslaufer.com
# answered every English reader in German, and the English work sample at
# jenslaufer.com/harry/en/ linked straight into it (Jens, 17.08.). A language
# that renders but is never written out does not exist for a reader.
#
# This table is the single definition of "published": `build` writes from it and
# `check` verifies from it, so a new language cannot arrive with a guard that
# still only watches the old one.
BASE_PAGES: dict[str, tuple[str, dict]] = {
    "de": ("index.html", {
        "lang_switch": {"href": "en/", "hreflang": "en", "label": "English"},
    }),
    "en": ("en/index.html", {
        # favicon lives at the repo root, one level up from en/
        "asset_prefix": "../",
        "lang_switch": {"href": "../", "hreflang": "de", "label": "Deutsch"},
    }),
}


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    print(f"wrote {path.relative_to(ROOT)}")


def cmd_build(args) -> int:
    try:
        out, profile = BASE_PAGES[args.lang]
    except KeyError:
        print(f"build: {args.lang!r} is not a published language "
              f"(have: {', '.join(BASE_PAGES)})", file=sys.stderr)
        return 2
    page = ROOT / out
    data = _parse.parse(lang=args.lang)
    _write(page, _render.render(data, profile, lang=args.lang))
    # Downloads sit next to their page: the English page offers the English PDF.
    if args.pdf:
        exporters.to_pdf(page, page.parent / "cv.pdf")
        print(f"wrote {(page.parent / 'cv.pdf').relative_to(ROOT)}")
    if args.docx:
        exporters.to_docx(data, page.parent / "cv.docx", lang=args.lang)
        print(f"wrote {(page.parent / 'cv.docx').relative_to(ROOT)}")
    return 0


def cmd_tailor(args) -> int:
    lang = args.lang
    data = _parse.parse(lang=lang)
    if args.profile:
        profile = yaml.safe_load(Path(args.profile).read_text(encoding="utf-8"))
        slug = profile.get("slug") or Path(args.profile).parent.name
        lang = profile.get("lang", lang)
        data = _parse.parse(lang=lang)
    else:
        if not args.job or not args.slug:
            print("tailor: need --job and --slug (or --profile)", file=sys.stderr)
            return 2
        job_text = Path(args.job).read_text(encoding="utf-8")
        slug = args.slug
        profile = _tailor.build_profile(job_text, data, slug,
                                        title=args.title, top=args.top)
        profile["lang"] = lang
        prof_path = ROOT / "tailored" / slug / "profile.yaml"
        _write(prof_path, _profile_yaml(profile))

    html = _render.render(data, _tailor.render_profile(profile), lang=lang)
    out = ROOT / "tailored" / slug / "index.html"
    _write(out, html)
    n = len(_tailor.render_profile(profile).get("include_projects") or data["projects"])
    print(f"tailored '{slug}': {n} projects, "
          f"{len(profile.get('emphasize_skills') or [])} matched skills")
    if args.pdf:
        exporters.to_pdf(out, out.parent / f"{slug}.pdf")
        print(f"wrote tailored/{slug}/{slug}.pdf")
    return 0


def cmd_check(args) -> int:
    """Sync guard: every published page must be byte-for-byte what data/*.csv renders.

    That is every language in BASE_PAGES *and* every tailored variant — they are
    just as public, and a variant nobody re-rendered keeps printing withdrawn
    facts (day rate, availability) long after the source was corrected.

    It checks all languages regardless of ``--lang``: a guard that verifies only
    the language you happen to ask about is how the English page could have been
    missing for three days without a single red test.
    """
    stale = []
    for lang, (out, profile) in BASE_PAGES.items():
        page = ROOT / out
        regenerated = _render.render(_parse.parse(lang=lang), profile, lang=lang)
        if not page.exists() or page.read_text(encoding="utf-8") != regenerated:
            stale.append((out, f"python3 -m gen build --lang {lang} --pdf --docx"))

    for prof_path in sorted((ROOT / "tailored").glob("*/profile.yaml")):
        profile = yaml.safe_load(prof_path.read_text(encoding="utf-8"))
        lang = profile.get("lang", "de")
        regenerated = _render.render(_parse.parse(lang=lang),
                                     _tailor.render_profile(profile), lang=lang)
        page = prof_path.parent / "index.html"
        if not page.exists() or page.read_text(encoding="utf-8") != regenerated:
            rel = page.relative_to(ROOT)
            stale.append((str(rel), f"python3 -m gen tailor --profile "
                                    f"{prof_path.relative_to(ROOT)} --pdf"))

    if stale:
        print(f"OUT OF SYNC ({len(stale)}): never edit generated HTML by hand — "
              "edit data/*.csv and re-render.", file=sys.stderr)
        for path, fix in stale:
            print(f"  {path} -> {fix}", file=sys.stderr)
        return 1

    n = len(list((ROOT / "tailored").glob("*/profile.yaml")))
    langs = "/".join(BASE_PAGES)
    print(f"in sync: {len(BASE_PAGES)} base page(s) [{langs}] + {n} tailored "
          f"variant(s) == generate(data/*.csv)")
    return 0


def _profile_yaml(profile: dict) -> str:
    header = (
        "# Tailoring profile — generated from a job posting, safe to hand-edit.\n"
        "# Facts come from data/*.csv; this only selects/orders/re-frames.\n"
        "# headline/stack_line/pitch/highlights: leave blank to use the base CV.\n"
        "# include_projects: project ids from data/*.csv, render order = listed order.\n"
        "# Re-render after editing:  python -m gen tailor --profile <this file>\n\n"
    )
    return header + yaml.safe_dump(profile, allow_unicode=True, sort_keys=False)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="gen", description="CV generator (source: data/*.csv)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("build", help="regenerate base index.html")
    b.add_argument("--pdf", action="store_true", help="also export cv.pdf")
    b.add_argument("--docx", action="store_true", help="also export cv.docx")
    b.add_argument("--lang", default="de", help="language of the CV (de|en)")
    b.set_defaults(func=cmd_build)

    t = sub.add_parser("tailor", help="build a tailored variant for a job posting")
    t.add_argument("--job", help="path to a job-posting text file")
    t.add_argument("--slug", help="short id for the variant (folder name)")
    t.add_argument("--title", help="HTML <title> for the variant")
    t.add_argument("--profile", help="re-render from an existing profile.yaml")
    t.add_argument("--top", type=int, default=12, help="max projects when overlap is thin")
    t.add_argument("--pdf", action="store_true", help="also export the variant PDF")
    t.add_argument("--lang", default="de", help="language of the variant (de|en)")
    t.set_defaults(func=cmd_tailor)

    c = sub.add_parser("check", help="verify every published page is in sync with data/*.csv")
    c.set_defaults(func=cmd_check)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
