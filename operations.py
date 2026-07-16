"""zgen file operations — generating, copying, zipping, and removing sample files.

This module holds the actual work and knows nothing about the menu, so it can be
imported and tested on its own.
"""

import pathlib
import shutil
import zipfile

from tqdm import tqdm

BASE_DIR = pathlib.Path("z").resolve()
CHUNK_SIZE = 64 * 1024  # read/write files in 64 KiB chunks
BAR_COLOR = "green"  # tqdm progress-bar colour (name or hex like "#00afff")


def safe_path(filename: str) -> pathlib.Path:
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


def create_file(filename: str, size: int) -> None:
    """Creates a file of exactly `size` bytes inside BASE_DIR."""
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    path = safe_path(filename)

    try:
        with open(path, "xb") as f, tqdm(
            total=size, desc="Creating file", unit="B", unit_scale=True, colour=BAR_COLOR
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
    source = safe_path(filename)
    if not source.is_file():
        print(f"  {filename} does not exist.")
        return

    stem = filename.removesuffix(".txt")
    for i in tqdm(range(num_copies), desc="Copying file", unit="copy", colour=BAR_COLOR):
        destination = safe_path(f"{stem}_copy_{i + 1}.txt")
        shutil.copy2(source, destination)
    print(f"  Created {num_copies} {'copy' if num_copies == 1 else 'copies'}.")


def zip_base_dir(zip_name: str = "output") -> None:
    """Compresses BASE_DIR into <zip_name>.zip, with a byte-accurate progress bar."""
    if not BASE_DIR.is_dir():
        print(f"  {BASE_DIR} does not exist — nothing to zip.")
        return

    files = [p for p in BASE_DIR.rglob("*") if p.is_file()]
    if not files:
        print(f"  {BASE_DIR.name}/ is empty — nothing to zip.")
        return

    archive = pathlib.Path(f"{zip_name}.zip")
    total_bytes = sum(p.stat().st_size for p in files)

    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf, tqdm(
        total=total_bytes, desc="Zipping", unit="B", unit_scale=True, colour="cyan"
    ) as bar:
        for path in files:
            arcname = path.relative_to(BASE_DIR)
            # force_zip64 lets individual members exceed 4 GiB (ZIP64).
            with open(path, "rb") as src, zf.open(str(arcname), "w", force_zip64=True) as dst:
                while chunk := src.read(CHUNK_SIZE):
                    dst.write(chunk)
                    bar.update(len(chunk))

    print(f"  Compressed {BASE_DIR.name}/ into {archive.name}.")


def remove_base_dir() -> None:
    """Removes BASE_DIR and everything inside it."""
    try:
        shutil.rmtree(BASE_DIR)
        print(f"  Removed {BASE_DIR}.")
    except FileNotFoundError:
        print(f"  {BASE_DIR} does not exist.")
