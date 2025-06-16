import os
import platform
import shutil
from pathlib import Path


def install_bookkeeppr():
    """
    Install wizard for Bookkeeppr
    """
    system = platform.system()

    if system == "Windows":
        target_dir = (
            Path(os.getenv("ProgramFiles", "C:/Program Files")) / "Bookkeeppr"
        )
    elif system == "Darwin":
        target_dir = Path("/Applications/Bookkeeppr")
    else:
        target_dir = Path.home() / ".local" / "bin" / "Bookkeeppr"

    print(f"[INSTALL] Installing to: {target_dir}")
    target_dir.mkdir(parents=True, exist_ok=True)

    # Copy files from source (current dir) to target
    source_root = Path(__file__).parent
    for item in os.listdir(source_root):
        if item in {"tests", ".git", "__pycache__"}:
            continue  # skip unwanted directories/files

        src = source_root / item
        dst = target_dir / item

        if src.is_dir():
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)

    print("[INSTALL] Done.")


if __name__ == "__main__":
    install_bookkeeppr()
