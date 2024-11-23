import os
import sys
import subprocess
import requests

# Add your GitHub Personal Access Token here
GITHUB_TOKEN = "your_github_personal_access_token"
REPO_NAME = "coltondick/ansible_playbook_monitor"  # Format: username/repo


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
    """Update the version in relevant project files."""
    print(f"Updating version to {version} in project files...")
    files_to_update = ["manifest.json"]

    for file_path in files_to_update:
        if os.path.exists(file_path):
            with open(file_path, "r") as file:
                content = file.read()
            updated_content = content.replace(
                '"version": "0.1.2"', f'"version": "{version}"'
            )
            with open(file_path, "w") as file:
                file.write(updated_content)
            print(f"Updated {file_path}")
        else:
            print(f"File {file_path} not found. Skipping.")


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
