#!/usr/bin/env python3
"""Create a Cookiecutter-ready template from an existing project.

The script:
1. Copies the source tree while substituting well-known identifiers (package
   name, author details, etc.) with Cookiecutter placeholders. Additional
   replacements can be supplied on the command line.
2. Wraps the copied files beneath ``{{ cookiecutter.project_slug }}`` and
   generates ``cookiecutter.json`` plus ``cookiecutter-config.yaml`` so projects
   can be rendered non-interactively (``--no-input``).
3. Adds a ``hooks/post_gen_project.py`` script that bootstraps a uv-based
   development environment after template rendering (or prints instructions when
   ``uv`` is not available).

Example::

    python tools/make_cookiecutter_template.py ./project ./cookiecutter-template
    cookiecutter ./cookiecutter-template --config-file cookiecutter-config.yaml --no-input
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import stat
import sys
import textwrap
from pathlib import Path
from typing import Dict, Iterable, Tuple

DEFAULT_REPLACEMENTS: Dict[str, str] = {
    "coron": "{{ cookiecutter.package_name }}",
    "Coron": "{{ cookiecutter.project_name }}",
    "pypi_packaging_tutorial": "{{ cookiecutter.repository_slug }}",
    "0.1.1": "{{ cookiecutter.project_version }}",
    "simple python packaging tutorial": "{{ cookiecutter.project_description }}",
    "Your Name": "{{ cookiecutter.author_name }}",
    "your name": "{{ cookiecutter.author_name }}",
    "you@example.com": "{{ cookiecutter.author_email }}",
    "your_email@example.com": "{{ cookiecutter.author_email }}",
    "https://github.com/k4144/pypi_packaging_tutorial": "{{ cookiecutter.repository_url }}",
}

DEFAULT_IGNORES: Tuple[str, ...] = (
    ".git",
    ".svn",
    ".hg",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "build",
    "dist",
    "tools/make_cookiecutter_template.py"
    "__pycache__",
    "**/*.pyc",
)

DEFAULT_CONTEXT: Dict[str, str] = {
    "project_name": "Coron",
    "project_slug": "coron",
    "package_name": "coron",
    "project_version": "0.1.0",
    "project_description": "simple python project",
    "author_name": "k4144",
    "author_email": "k4144.github@gmail.com",
    "repository_slug": "coron",
    "repository_url": "https://github.com/k4144/coron",
    "python_version": "3.11",
}

POST_GEN_SCRIPT = textwrap.dedent(
    """\
    #!/usr/bin/env python3
    \"\"\"Post-generation hook for Cookiecutter projects.

    Attempts to create a uv virtual environment and install the project plus
    development dependencies. When uv is unavailable, prints the recommended
    commands instead of failing.
    \"\"\"
    from __future__ import annotations

    import shutil
    import subprocess
    import sys
    from pathlib import Path

    PROJECT_ROOT = Path.cwd()

    def run(cmd: list[str]) -> bool:
        try:
            subprocess.run(cmd, check=True)
        except FileNotFoundError:
            return False
        except subprocess.CalledProcessError as exc:
            print(f\"Command failed ({' '.join(cmd)}): {exc}\", file=sys.stderr)
            return False
        return True

    def main() -> None:
        if shutil.which(\"uv\") is None:
            print(\"uv is not installed; skipping automatic environment setup.\")
            print(\"Run these commands manually:\")
            print(\"  uv venv\")
            print(\"  uv pip install -e '.[dev]'\")
            return

        env_dir = PROJECT_ROOT / \".venv\"
        if not run([\"uv\", \"venv\", str(env_dir)]):
            return
        run([\"uv\", \"pip\", \"install\", \"-e\", \".[dev]\"])

    if __name__ == \"__main__\":
        main()
    """
)


def parse_key_value(items: Iterable[str]) -> Dict[str, str]:
    result: Dict[str, str] = {}
    for item in items:
        if "=" not in item:
            raise argparse.ArgumentTypeError(f"Expected KEY=VALUE pair, got '{item}'")
        key, value = item.split("=", 1)
        if not key:
            raise argparse.ArgumentTypeError(f"Key missing in '{item}'")
        result[key] = value
    return result


def should_ignore(path: Path, ignores: Tuple[str, ...]) -> bool:
    return any(path.match(pattern) for pattern in ignores)


def apply_replacements(text: str, replacements: Dict[str, str]) -> str:
    result = text
    for old, new in replacements.items():
        if old:
            result = result.replace(old, new)
    return result


def transform_path(rel_path: Path, replacements: Dict[str, str]) -> Path:
    transformed = [apply_replacements(part, replacements) for part in rel_path.parts]
    return Path(*transformed)


GITHUB_ACTIONS_EXPR = re.compile(r"\${{.*?}}", re.DOTALL)


def escape_cookiecutter_conflicts(text: str) -> str:
    """Wrap GitHub Actions expressions in raw blocks to avoid Jinja conflicts."""

    def wrap(match: re.Match[str]) -> str:
        return "{% raw %}" + match.group(0) + "{% endraw %}"

    return GITHUB_ACTIONS_EXPR.sub(wrap, text)


def copy_with_replacements(
    src_root: Path,
    dest_root: Path,
    replacements: Dict[str, str],
    ignores: Tuple[str, ...],
) -> None:
    for src_path in src_root.rglob("*"):
        rel_path = src_path.relative_to(src_root)

        if any(part in ignores for part in rel_path.parts) or should_ignore(rel_path, ignores):
            continue

        dest_path = dest_root / transform_path(rel_path, replacements)
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        if src_path.is_dir():
            dest_path.mkdir(exist_ok=True)
            continue

        try:
            text = src_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            shutil.copy2(src_path, dest_path)
            continue

        rewritten = apply_replacements(text, replacements)
        dest_path.write_text(escape_cookiecutter_conflicts(rewritten), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("src", type=Path, help="Existing project directory to transform.")
    parser.add_argument("dest", type=Path, help="Destination directory for the Cookiecutter template.")
    parser.add_argument(
        "--replace",
        action="append",
        default=None,
        metavar="OLD=NEW",
        help="Additional replacement mapping (may be supplied multiple times).",
    )
    parser.add_argument(
        "--replacements-json",
        type=Path,
        default=None,
        help="Optional JSON file containing extra replacements (object of old->new).",
    )
    parser.add_argument(
        "--ignore",
        action="append",
        default=None,
        metavar="PATTERN",
        help="Extra glob pattern to ignore during copy (directories or files).",
    )
    parser.add_argument(
        '--context',
        action='append',
        default=None,
        metavar="KEY=VALUE",
        help="Override a value used for cookiecutter.json defaults.",
    )
    parser.add_argument(
        '--context-json',
        type=Path,
        default=None,
        help="Load additional context defaults from a JSON file.",
    )
    parser.add_argument(
        '--force',
        '-f',
        action='store_true',
        help="overwrite existing folder and files",
    )
    return parser


def load_replacements(args: argparse.Namespace) -> Dict[str, str]:
    replacements = DEFAULT_REPLACEMENTS.copy()

    if args.replacements_json:
        try:
            data = json.loads(args.replacements_json.read_text(encoding="utf-8"))
        except Exception as exc:
            raise RuntimeError(f"Failed to load replacements JSON: {exc}") from exc
        if not isinstance(data, dict):
            raise ValueError("Replacement JSON must be an object of string keys to values.")
        replacements.update({str(k): str(v) for k, v in data.items()})

    if args.replace:
        replacements.update(parse_key_value(args.replace))

    return replacements


def load_context(args: argparse.Namespace) -> Dict[str, str]:
    context = DEFAULT_CONTEXT.copy()

    if args.context_json:
        try:
            data = json.loads(args.context_json.read_text(encoding="utf-8"))
        except Exception as exc:
            raise RuntimeError(f"Failed to load context JSON: {exc}") from exc
        if not isinstance(data, dict):
            raise ValueError("Context JSON must be an object of string keys to values.")
        context.update({str(k): str(v) for k, v in data.items()})

    if args.context:
        context.update(parse_key_value(args.context))

    project_name = context.get("project_name", "Project")
    context.setdefault("project_slug", project_name.lower().replace(" ", "-"))
    context.setdefault("package_name", context["project_slug"].replace("-", "_"))
    context.setdefault("repository_slug", context["project_slug"])
    context.setdefault("project_description", "Generated project")
    context.setdefault("project_version", "0.1.0")
    context.setdefault("python_version", "3.11")
    return context


def write_cookiecutter_metadata(dest: Path, context: Dict[str, str]) -> None:
    cookiecutter_json = {
        "project_name": context["project_name"],
        "project_slug": "{{ cookiecutter.project_name.lower().replace(' ', '-') }}",
        "package_name": "{{ cookiecutter.project_slug.replace('-', '_') }}",
        "project_version": context["project_version"],
        "project_description": context["project_description"],
        "author_name": context["author_name"],
        "author_email": context["author_email"],
        "repository_slug": "{{ cookiecutter.project_slug }}",
        "repository_url": context["repository_url"],
        "python_version": context["python_version"],
    }
    (dest / "cookiecutter.json").write_text(json.dumps(cookiecutter_json, indent=2) + "\n", encoding="utf-8")

    config_lines = ["default_context:"]
    for key in sorted(context):
        config_lines.append(f"  {key}: {json.dumps(context[key])}")
    (dest / "cookiecutter-config.yaml").write_text("\n".join(config_lines) + "\n", encoding="utf-8")

    hooks_dir = dest / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    post_gen_path = hooks_dir / "post_gen_project.py"
    post_gen_path.write_text(POST_GEN_SCRIPT, encoding="utf-8")
    post_gen_path.chmod(post_gen_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    force = args.force
    src = args.src.resolve()
    dest = args.dest.resolve()

    if not src.exists() or not src.is_dir():
        parser.error(f"Source directory '{src}' does not exist or is not a directory.")

    if dest.exists() and not force:
        if any(dest.iterdir()):
            parser.error(f"Destination '{dest}' already exists and is not empty.")
    else:
        dest.mkdir(parents=True, exist_ok=True)

    replacements = load_replacements(args)
    context = load_context(args)
    ignores = DEFAULT_IGNORES + tuple(args.ignore or [])

    project_dir = dest / "{{ cookiecutter.project_slug }}"
    project_dir.mkdir(parents=True, exist_ok=True)
    
    copy_with_replacements(src, project_dir, replacements, ignores)
    write_cookiecutter_metadata(dest, context)

    #print(f"Cookiecutter template written to {dest}")
    return 0


if __name__ == "__main__":  # pragma: no cover - script entry point
    raise SystemExit(main())
