import os
import sys


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


def main():
    # Fetch release notes
    release_notes = get_release_notes()
    print("\n--- Release Notes ---\n")
    print(release_notes)

    # Confirm or save the release notes
    confirm = (
        input("Do you want to save these release notes for the release? (y/n): ")
        .strip()
        .lower()
    )
    if confirm == "y":
        # Save to a default file (if needed) or directly use in the release process
        with open("release_notes.txt", "w") as file:
            file.write(release_notes)
        print("\nRelease notes saved to 'release_notes.txt'.")
    else:
        print("Release notes were not saved.")
        sys.exit(1)

    # Add your release process here, e.g., tagging, versioning, etc.
    print("Proceeding with the release process...")


if __name__ == "__main__":
    main()
