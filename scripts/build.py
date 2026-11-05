"""Compile without running MacHiDPI, and bind its source and binary hashes."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "MacHiDPI/source/MacHiDPI.swift"
BINARY = ROOT / "MacHiDPI/MacHiDPI"
RECORD = ROOT / "MacHiDPI/build.json"
TARGET = "arm64-apple-macos14.0"


def build_record():
    return {"schema": 1, "target": TARGET,
            "sourceSHA256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
            "binarySHA256": hashlib.sha256(BINARY.read_bytes()).hexdigest()}


def check_build():
    if not RECORD.is_file() or json.loads(RECORD.read_text()) != build_record():
        raise ValueError("Build record is missing or stale; run python3 scripts/build.py")


def build():
    original_source = SOURCE.read_bytes()
    with tempfile.TemporaryDirectory(prefix="open-hidpi-build-") as folder:
        output = Path(folder) / "MacHiDPI"
        subprocess.run(["swiftc", "-target", TARGET, "-warnings-as-errors",
                        "-module-cache-path", str(Path(folder) / "module-cache"),
                        str(SOURCE.relative_to(ROOT)), "-o", str(output)], cwd=ROOT, check=True)
        subprocess.run(["codesign", "--verify", "--strict", str(output)], check=True)
        if SOURCE.read_bytes() != original_source:
            raise ValueError("Source changed during compilation; existing binary was retained")
        if not BINARY.exists() or BINARY.read_bytes() != output.read_bytes():
            shutil.copy2(output, BINARY)
    data = json.dumps(build_record(), indent=2) + "\n"
    if not RECORD.exists() or RECORD.read_text() != data:
        RECORD.write_text(data)
    check_build()
    print("PASS: compiled and signature-verified; source and binary hashes recorded")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Check existing build hashes without compiling")
    arguments = parser.parse_args()
    try:
        if arguments.check:
            check_build()
            print("PASS: build record matches current source and binary")
        else:
            build()
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"Error: {error}\n")
