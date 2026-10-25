"""Package only tracked source and compiled UI; never local secrets/state."""

import hashlib
import subprocess
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

root = Path(__file__).resolve().parents[1]
output = root / "release"
output.mkdir(exist_ok=True)
name = output / "BTC-Quant-OS-v0.1.0-paper.zip"
tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=root).decode().split("\0")
with ZipFile(name, "w", ZIP_DEFLATED) as archive:
    for file in tracked:
        if file and not file.startswith((".git/", ".env")):
            archive.write(root / file, "BTC-Quant-OS/" + file)
    archive.write(root / ".env.example", "BTC-Quant-OS/.env.example")
    for path in (root / "frontend" / "dist").rglob("*"):
        if path.is_file():
            archive.write(path, "BTC-Quant-OS/" + str(path.relative_to(root)))
digest = hashlib.sha256(name.read_bytes()).hexdigest()
(name.with_suffix(".zip.sha256")).write_text(f"{digest}  {name.name}\n")
print(f"Created {name.name} ({name.stat().st_size} bytes); SHA-256 {digest}")
