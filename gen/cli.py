"""Command-line interface for the CV generator.

  python -m gen build                       # regenerate base index.html (+ --pdf --docx)
  python -m gen tailor --job posting.txt --slug acme [--title "..."]
  python -m gen tailor --profile tailored/acme/profile.yaml   # re-render after editing
  python -m gen check                       # fail if index.html is out of sync with data.md
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


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    print(f"wrote {path.relative_to(ROOT)}")


def cmd_build(args) -> int:
    data = _parse.parse()
    html = _render.render(data)
    _write(ROOT / "index.html", html)
    if args.pdf:
        exporters.to_pdf(ROOT / "index.html", ROOT / "cv.pdf")
        print("wrote cv.pdf")
    if args.docx:
        exporters.to_docx(data, ROOT / "cv.docx")
        print("wrote cv.docx")
    return 0


def cmd_tailor(args) -> int:
    data = _parse.parse()
    if args.profile:
        profile = yaml.safe_load(Path(args.profile).read_text(encoding="utf-8"))
        slug = profile.get("slug") or Path(args.profile).parent.name
    else:
        if not args.job or not args.slug:
            print("tailor: need --job and --slug (or --profile)", file=sys.stderr)
            return 2
        job_text = Path(args.job).read_text(encoding="utf-8")
        slug = args.slug
        profile = _tailor.build_profile(job_text, data, slug,
                                        title=args.title, top=args.top)
        prof_path = ROOT / "tailored" / slug / "profile.yaml"
        _write(prof_path, _profile_yaml(profile))

    html = _render.render(data, _tailor.render_profile(profile))
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
    """Sync guard: regenerating from data.md must reproduce index.html byte-for-byte."""
    current = (ROOT / "index.html").read_text(encoding="utf-8")
    regenerated = _render.render(_parse.parse())
    if current != regenerated:
        print("OUT OF SYNC: index.html differs from `python -m gen build`. "
              "Edit data.md and rebuild, never edit index.html by hand.", file=sys.stderr)
        return 1
    print("in sync: index.html == generate(data.md)")
    return 0


def _profile_yaml(profile: dict) -> str:
    header = (
        "# Tailoring profile — generated from a job posting, safe to hand-edit.\n"
        "# Facts come from data.md; this only selects/orders/re-frames.\n"
        "# headline/stack_line/pitch/highlights: leave blank to use the base CV.\n"
        "# include_projects: project ids from data.md, render order = listed order.\n"
        "# Re-render after editing:  python -m gen tailor --profile <this file>\n\n"
    )
    return header + yaml.safe_dump(profile, allow_unicode=True, sort_keys=False)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="gen", description="CV generator (source: data.md)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("build", help="regenerate base index.html")
    b.add_argument("--pdf", action="store_true", help="also export cv.pdf")
    b.add_argument("--docx", action="store_true", help="also export cv.docx")
    b.set_defaults(func=cmd_build)

    t = sub.add_parser("tailor", help="build a tailored variant for a job posting")
    t.add_argument("--job", help="path to a job-posting text file")
    t.add_argument("--slug", help="short id for the variant (folder name)")
    t.add_argument("--title", help="HTML <title> for the variant")
    t.add_argument("--profile", help="re-render from an existing profile.yaml")
    t.add_argument("--top", type=int, default=12, help="max projects when overlap is thin")
    t.add_argument("--pdf", action="store_true", help="also export the variant PDF")
    t.set_defaults(func=cmd_tailor)

    c = sub.add_parser("check", help="verify index.html is in sync with data.md")
    c.set_defaults(func=cmd_check)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
