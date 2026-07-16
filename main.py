"""zgen — generate dummy files, copy them, and zip the results."""

import pathlib
import shutil
import sys

from tqdm import tqdm

BASE_DIR = pathlib.Path("z").resolve()
CHUNK_SIZE = 64 * 1024  # write files in 64 KiB chunks

# ---------------------------------------------------------------- helpers


def _safe_path(filename: str) -> pathlib.Path:
    """Resolves filename against BASE_DIR and ensures the result stays inside it."""
    if not filename or filename in (".", ".."):
        raise ValueError("Invalid filename.")

    candidate = pathlib.Path(filename)
    if candidate.name != filename or candidate.is_absolute():
        raise ValueError("Filename must not contain path components.")

    full_path = (BASE_DIR / filename).resolve()
    if BASE_DIR not in full_path.parents:
        raise ValueError("Access outside the allowed directory.")
    return full_path


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


# ---------------------------------------------------------------- actions


def create_file(filename: str, size: int) -> None:
    """Creates a file of exactly `size` bytes inside BASE_DIR."""
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    path = _safe_path(filename)

    try:
        with open(path, "xb") as f, tqdm(
            total=size, desc="Creating file", unit="B", unit_scale=True
        ) as bar:
            remaining = size
            while remaining > 0:
                chunk = min(remaining, CHUNK_SIZE)
                f.write(b"0" * chunk)
                bar.update(chunk)
                remaining -= chunk
        print(f"  Created {path.name} ({size} bytes).")
    except FileExistsError:
        print(f"  {filename} already exists.")


def copy_file(filename: str, num_copies: int) -> None:
    """Creates numbered copies of filename inside BASE_DIR."""
    source = _safe_path(filename)
    if not source.is_file():
        print(f"  {filename} does not exist.")
        return

    stem = filename.removesuffix(".txt")
    for i in tqdm(range(num_copies), desc="Copying file", unit="copy"):
        destination = _safe_path(f"{stem}_copy_{i + 1}.txt")
        shutil.copy2(source, destination)
    print(f"  Created {num_copies} {'copy' if num_copies == 1 else 'copies'}.")


def zip_base_dir(zip_name: str = "output") -> None:
    """Compresses BASE_DIR into <zip_name>.zip next to the script."""
    if not BASE_DIR.is_dir():
        print(f"  {BASE_DIR} does not exist — nothing to zip.")
        return
    archive = shutil.make_archive(zip_name, "zip", BASE_DIR)
    print(f"  Compressed {BASE_DIR.name}/ into {pathlib.Path(archive).name}.")


def remove_base_dir() -> None:
    """Removes BASE_DIR and everything inside it."""
    try:
        shutil.rmtree(BASE_DIR)
        print(f"  Removed {BASE_DIR}.")
    except FileNotFoundError:
        print(f"  {BASE_DIR} does not exist.")


# ---------------------------------------------------------------- menu


MENU_UNICODE = """
┌──────────────── zgen ────────────────┐
│  1  Create a sample file             │
│  2  Copy the sample file             │
│  3  Zip the base directory           │
│  4  Delete the base directory        │
│  q  Quit                             │
└──────────────────────────────────────┘"""

MENU_ASCII = """
+---------------- zgen ----------------+
|  1  Create a sample file             |
|  2  Copy the sample file             |
|  3  Zip the base directory           |
|  4  Delete the base directory        |
|  q  Quit                             |
+--------------------------------------+"""


def _pick_menu() -> str:
    """Uses the box-drawing menu only if the terminal's encoding can print it."""
    try:
        MENU_UNICODE.encode(sys.stdout.encoding or "ascii")
        return MENU_UNICODE
    except UnicodeEncodeError:
        return MENU_ASCII


def main() -> None:
    menu = _pick_menu()
    print(f"Working directory: {BASE_DIR}")
    while True:
        print(menu)
        choice = input("> ").strip().lower()

        try:
            if choice == "1":
                size = _ask_int("Size of the file in bytes: ")
                create_file("sample.txt", size)
            elif choice == "2":
                num_copies = _ask_int("Number of copies: ")
                copy_file("sample.txt", num_copies)
            elif choice == "3":
                zip_base_dir()
            elif choice == "4":
                if _ask_yes_no(f"Delete {BASE_DIR} and all its contents?"):
                    remove_base_dir()
            elif choice == "q":
                print("Bye!")
                return
            else:
                print("  Unknown option.")
        except ValueError as e:
            print(f"  Error: {e}")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nCancelled by user.")
        sys.exit(1)
