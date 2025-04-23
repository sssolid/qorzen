import os
import shutil
import subprocess
from pathlib import Path


def run_command(command: list[str]) -> None:
    result = subprocess.run(command, check=True)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(command)}")


def main() -> None:
    base_dir = Path("processed_project")
    print("[INFO] Cleaning processed_project directory...")
    if base_dir.exists():
        shutil.rmtree(base_dir)
    base_dir.mkdir(parents=True, exist_ok=True)

    print("[INFO] Running project processors...")
    run_command(
        [
            "python",
            "backend-stripper.py",
            "backend/",
            "--output",
            "processed_project/backend_stripped/",
        ]
    )
    run_command(
        [
            "python",
            "frontend-stripper.py",
            "frontend/",
            "--output",
            "processed_project/frontend_stripped/",
        ]
    )
    run_command(
        [
            "python",
            "code-structure-mapper2.py",
            "backend/",
            "--output",
            "processed_project/backend_structure",
            "--format",
            "directory",
        ]
    )
    run_command(
        [
            "python",
            "code-structure-mapper.py",
            "backend/",
            "--output",
            "processed_project/backend_structure.md",
            "--include-docstrings",
        ]
    )
    run_command(
        [
            "python",
            "frontend-structure-mapper.py",
            "frontend/",
            "--output",
            "processed_project/frontend_structure.md",
        ]
    )

    print("[INFO] Concatenating documentation...")
    with open("processed_project/full_structure.md", "w", encoding="utf-8") as out_file:
        for file in [
            "processed_project/backend_structure.md",
            "processed_project/frontend_structure.md",
        ]:
            with open(file, encoding="utf-8") as f:
                out_file.write(f.read())
                out_file.write("\n")

    print("[INFO] processed_project successfully regenerated.")


if __name__ == "__main__":
    main()
