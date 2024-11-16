import json
import os
import subprocess
from github import Github
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # GitHub PAT loaded from .env
REPO_NAME = os.getenv("REPO_NAME")
MANIFEST_FILE = os.getenv("MANIFEST_FILE")

if not GITHUB_TOKEN:
    raise ValueError("GITHUB_TOKEN is not set. Please add it to the .env file.")


def update_version_in_manifest(new_version):
    """Update the version string in manifest.json."""
    with open(MANIFEST_FILE, "r") as file:
        data = json.load(file)

    data["version"] = new_version

    with open(MANIFEST_FILE, "w") as file:
        json.dump(data, file, indent=4)
    print(f"Updated version to {new_version} in {MANIFEST_FILE}")


def git_commit_and_tag(version):
    """Commit changes and create a Git tag."""
    subprocess.run(["git", "add", MANIFEST_FILE], check=True)
    subprocess.run(["git", "commit", "-m", f"Release version {version}"], check=True)
    subprocess.run(["git", "tag", version], check=True)
    print(f"Committed changes and created tag {version}")


def push_to_github():
    """Push commits and tags to GitHub."""
    subprocess.run(["git", "push"], check=True)
    subprocess.run(["git", "push", "--tags"], check=True)
    print("Pushed commits and tags to GitHub")


def create_github_release(version, release_notes="Automated release"):
    """Create a GitHub release using the PyGithub library."""
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)
    release = repo.create_git_release(
        tag=version,
        name=f"Version {version}",
        message=release_notes,
        draft=False,
        prerelease=False,
    )
    print(f"Created GitHub release: {release.html_url}")


def main():
    # Prompt user for new version
    new_version = input("Enter the new version (e.g., 1.0.0): ").strip()
    release_notes = input("Enter release notes: ").strip()

    # Update manifest.json
    update_version_in_manifest(new_version)

    # Commit and tag changes
    git_commit_and_tag(new_version)

    # Push changes to GitHub
    push_to_github()

    # Create GitHub release
    create_github_release(new_version, release_notes)


if __name__ == "__main__":
    main()
