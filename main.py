"""zgen — a small terminal menu to generate, copy, and zip sample files."""

import sys

from operations import (
    BASE_DIR,
    copy_file,
    create_file,
    remove_base_dir,
    zip_base_dir,
)

# ---------------------------------------------------------------- input helpers


def _ask_int(prompt: str, minimum: int = 0) -> int:
    """Asks until the user enters an integer >= minimum."""
    while True:
        raw = input(prompt).strip()
        try:
            value = int(raw)
        except ValueError:
            print("  Please enter a whole number.")
            continue
        if value < minimum:
            print(f"  Please enter a number >= {minimum}.")
            continue
        return value


def _ask_yes_no(prompt: str) -> bool:
    return input(f"{prompt} (y/n) ").strip().lower() == "y"


# ---------------------------------------------------------------- menu

# (label, action). action is None for "Quit".
MENU_ITEMS = [
    ("Create a sample file", lambda: create_file("sample.txt", _ask_int("Size of the file in bytes: "))),
    ("Copy the sample file", lambda: copy_file("sample.txt", _ask_int("Number of copies: "))),
    ("Zip the base directory", zip_base_dir),
    ("Delete the base directory",
     lambda: remove_base_dir() if _ask_yes_no(f"Delete {BASE_DIR} and all its contents?") else None),
    ("Quit", None),
]


def _dispatch(label: str) -> bool:
    """Runs the action for a menu label. Returns False if the app should quit."""
    for item_label, action in MENU_ITEMS:
        if item_label == label:
            if action is None:  # Quit
                return False
            try:
                action()
            except ValueError as e:
                print(f"  Error: {e}")
            return True
    return True


def _run_interactive() -> None:
    """Arrow-key menu (questionary) for real terminals."""
    import questionary

    labels = [label for label, _ in MENU_ITEMS]
    print(f"Working directory: {BASE_DIR}")
    while True:
        choice = questionary.select(
            "zgen — choose an action:",
            choices=labels,
            use_shortcuts=True,  # number keys 1-9 jump to a choice
            qmark="»",
        ).ask()
        if choice is None or not _dispatch(choice):  # None = Esc/Ctrl-C
            print("Bye!")
            return


def _run_basic() -> None:
    """Numbered fallback for when stdin isn't an interactive terminal (pipes/CI)."""
    print(f"Working directory: {BASE_DIR}")
    while True:
        print("\nzgen — choose an action:")
        for i, (label, _) in enumerate(MENU_ITEMS, 1):
            print(f"  {i}  {label}")
        choice = input("> ").strip().lower()

        if choice in {"q", "quit", str(len(MENU_ITEMS))}:
            print("Bye!")
            return
        if choice.isdigit() and 1 <= int(choice) <= len(MENU_ITEMS):
            if not _dispatch(MENU_ITEMS[int(choice) - 1][0]):
                print("Bye!")
                return
        else:
            print("  Unknown option.")


def main() -> None:
    if sys.stdin.isatty():
        _run_interactive()
    else:
        _run_basic()


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nCancelled by user.")
        sys.exit(1)
