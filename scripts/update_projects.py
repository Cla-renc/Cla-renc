#!/usr/bin/env python3
"""Update the auto-generated public repository list in README.md."""

import json
import os
import re
import urllib.request
from datetime import datetime, timezone

USERNAME = "Cla-renc"
PROFILE_REPO = USERNAME.lower()
README_PATH = "README.md"
START_MARKER = "<!-- AUTO-PROJECTS:START -->"
END_MARKER = "<!-- AUTO-PROJECTS:END -->"
MAX_REPOSITORIES = 10


def fetch_repositories():
    url = (
        f"https://api.github.com/users/{USERNAME}/repos"
        "?type=public&sort=updated&direction=desc&per_page=100"
    )
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "github-portfolio-auto-updater",
        },
    )
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        request.add_header("Authorization", f"Bearer {token}")

    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def clean_markdown(value):
    """Keep repository metadata from breaking the generated Markdown."""
    return str(value or "").replace("\r", " ").replace("\n", " ").replace("|", r"\|").strip()


def render_projects(repositories):
    eligible = [
        repo for repo in repositories
        if not repo.get("fork")
        and not repo.get("archived")
        and repo.get("name", "").lower() != PROFILE_REPO
    ][:MAX_REPOSITORIES]

    if not eligible:
        return "_No public projects found yet. Check back soon._"

    lines = [
        "| Project | Description | Main language |",
        "|---|---|---|",
    ]
    for repo in eligible:
        name = clean_markdown(repo.get("name"))
        description = clean_markdown(repo.get("description")) or "No description added yet"
        language = clean_markdown(repo.get("language")) or "Not specified"
        url = repo.get("html_url", f"https://github.com/{USERNAME}/{repo.get('name', '')}")
        lines.append(f"| [**{name}**]({url}) | {description} | {language} |")

    lines.append("")
    lines.append(
        f"_Automatically refreshed from "
        f"[{USERNAME}'s public GitHub repositories](https://github.com/{USERNAME}) "
        f"on {datetime.now(timezone.utc).strftime('%Y-%m-%d')} (UTC)._"
    )
    return "\n".join(lines)


def main():
    with open(README_PATH, "r", encoding="utf-8") as file:
        readme = file.read()

    if START_MARKER not in readme or END_MARKER not in readme:
        raise SystemExit(
            "README.md is missing the AUTO-PROJECTS markers. "
            "Add the supplied marker block before running this script."
        )

    repositories = fetch_repositories()
    generated = render_projects(repositories)
    replacement = f"{START_MARKER}\n{generated}\n{END_MARKER}"

    pattern = re.compile(
        re.escape(START_MARKER) + r".*?" + re.escape(END_MARKER),
        re.DOTALL,
    )
    updated_readme, count = pattern.subn(lambda _: replacement, readme, count=1)
    if count != 1:
        raise SystemExit("Could not safely locate the auto-project section.")

    with open(README_PATH, "w", encoding="utf-8") as file:
        file.write(updated_readme)

    print(f"Updated public repository listing with up to {MAX_REPOSITORIES} projects.")


if __name__ == "__main__":
    main()

