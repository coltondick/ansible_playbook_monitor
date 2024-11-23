import os
import sys
import subprocess
import json
import requests
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    print("Error: GITHUB_TOKEN is not set in the .env file.")
    sys.exit(1)

REPO_NAME = os.getenv("REPO_NAME")
if not REPO_NAME:
    print("Error: REPO_NAME is not set in the .env file.")
    sys.exit(1)


def get_version_number():
    """Prompt for the release version number."""
    while True:
        version = input("Enter the release version number (e.g., 0.1.2): ").strip()
        if version:
            confirm = input(f"Confirm version '{version}'? (y/n): ").strip().lower()
            if confirm == "y":
                return version
        print("Invalid version or confirmation failed. Try again.")


def get_release_notes():
    """Fetch release notes from a file or user input."""
    notes_file = input(
        "Enter the path to the release notes file (leave blank to input manually): "
    ).strip()

    if notes_file and os.path.exists(notes_file):
        with open(notes_file, "r") as file:
            release_notes = file.read()
        print("\nRelease Notes loaded from file:")
    else:
        print("Enter the release notes below (type 'END' on a new line to finish):")
        lines = []
        while True:
            line = input()
            if line.strip().upper() == "END":
                break
            lines.append(line)
        release_notes = "\n".join(lines)

    return release_notes


def update_version_in_files(version):
    """Update the version in the manifest.json file."""
    # Retrieve the manifest.json path from .env
    manifest_path = os.getenv("MANIFEST_JSON_PATH")

    if not manifest_path:
        print("Error: MANIFEST_JSON_PATH not set in .env file.")
        return

    print(f"Updating version to {version} in project file: {manifest_path}")

    if os.path.exists(manifest_path):
        try:
            # Load the JSON file
            with open(manifest_path, "r") as file:
                data = json.load(file)

            # Update the version
            if "version" in data:
                old_version = data["version"]
                data["version"] = version
                print(
                    f"Updated version from {old_version} to {version} in {manifest_path}"
                )

                # Write the changes back to the file
                with open(manifest_path, "w") as file:
                    json.dump(data, file, indent=4)
            else:
                print(f"No 'version' key found in {manifest_path}. Skipping.")
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON in {manifest_path}: {e}")
    else:
        print(f"File {manifest_path} not found. Skipping.")


def commit_and_tag_release(version, release_notes):
    """Commit changes and create a Git tag for the release."""
    try:
        # Commit changes
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", f"Release {version}"], check=True)
        print(f"Committed changes for version {version}.")

        # Tag release
        subprocess.run(
            ["git", "tag", "-a", f"v{version}", "-m", release_notes], check=True
        )
        print(f"Created tag v{version}.")
    except subprocess.CalledProcessError as e:
        print(f"Error during Git operations: {e}")
        sys.exit(1)


def push_to_repository():
    """Push changes and tags to the remote repository."""
    try:
        subprocess.run(["git", "push"], check=True)
        subprocess.run(["git", "push", "--tags"], check=True)
        print("Pushed changes and tags to the remote repository.")
    except subprocess.CalledProcessError as e:
        print(f"Error pushing to repository: {e}")
        sys.exit(1)


def create_github_release(version, release_notes):
    """Create a GitHub release."""
    print("Creating a GitHub release...")
    url = f"https://api.github.com/repos/{REPO_NAME}/releases"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }
    payload = {
        "tag_name": f"v{version}",
        "name": f"Version {version}",
        "body": release_notes,
        "draft": False,
        "prerelease": False,
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 201:
        print("GitHub release created successfully.")
    else:
        print(f"Failed to create GitHub release: {response.status_code}")
        print(response.json())
        sys.exit(1)


def main():
    # Fetch release version number
    version = get_version_number()
    print(f"\nRelease Version: {version}\n")

    # Fetch release notes
    release_notes = get_release_notes()
    print("\n--- Release Notes ---\n")
    print(release_notes)

    # Confirm the release process
    confirm = (
        input(f"Proceed with the release process for version {version}? (y/n): ")
        .strip()
        .lower()
    )
    if confirm != "y":
        print("Release process aborted.")
        sys.exit(1)

    # Update version in project files
    update_version_in_files(version)

    # Commit changes and create Git tag
    commit_and_tag_release(version, release_notes)

    # Push changes to the remote repository
    push_to_repository()

    # Create GitHub release
    create_github_release(version, release_notes)

    print(f"Release process for version {version} completed successfully!")


if __name__ == "__main__":
    main()
