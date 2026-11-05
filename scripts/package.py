"""Package the existing tool bundle, or check artifacts without modifying files."""
import argparse
import hashlib
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile

sys.dont_write_bytecode = True
from build import check_build
from privacy import check_privacy, public_files


ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "MacHiDPI"
BUNDLE_SUMS = BUNDLE / "SHA256SUMS"
PROJECT_SUMS = ROOT / "release/SHA256SUMS.project"
ARCHIVE = ROOT / "release/MacHiDPI.zip"
BUNDLE_INPUTS = (
    "MacHiDPI", "source/MacHiDPI.swift", "build.json", "使用说明.md", "验证记录.md",
    "LICENSE", "THIRD_PARTY_NOTICES.md",
    "安装并开启.command", "恢复原配置.command", "检查状态.command",
    "直接开启HiDPI.command", "重新连接并开启.command",
)


def bundle_files():
    paths = [BUNDLE / name for name in BUNDLE_INPUTS]
    for path in paths:
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"Required bundle input is missing or not a regular file: {path.name}")
        if (path.name == "MacHiDPI" or path.suffix == ".command") and not path.stat().st_mode & 0o100:
            raise ValueError(f"Required executable lacks owner execute permission: {path.name}")
    for name in ("LICENSE", "THIRD_PARTY_NOTICES.md"):
        if (BUNDLE / name).read_bytes() != (ROOT / name).read_bytes():
            raise ValueError(f"Bundle notice differs from project notice: {name}")
    return sorted(paths)


def project_files():
    return [path for path in public_files() if path != PROJECT_SUMS]


def manifest(base, paths):
    lines = []
    for path in paths:
        relative = path.relative_to(base).as_posix()
        if path.is_symlink() or "\n" in relative or "\r" in relative:
            raise ValueError(f"Unsupported file in manifest: {relative}")
        lines.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {relative}\n")
    return "".join(lines).encode("utf-8")


def write_if_changed(path, data):
    if not path.exists() or path.read_bytes() != data:
        path.write_bytes(data)


def check():
    check_privacy()
    check_build()
    if BUNDLE_SUMS.read_bytes() != manifest(BUNDLE, bundle_files()):
        raise ValueError("Bundle manifest is stale; run python3 scripts/package.py")
    if PROJECT_SUMS.read_bytes() != manifest(ROOT, project_files()):
        raise ValueError("Project manifest is stale; run python3 scripts/package.py")
    files = {"MacHiDPI/" + path.relative_to(BUNDLE).as_posix(): path
             for path in bundle_files() + [BUNDLE_SUMS]}
    with zipfile.ZipFile(ARCHIVE) as archive:
        if len(archive.namelist()) != len(files) or set(archive.namelist()) != set(files):
            raise ValueError("ZIP file list differs from the bundle")
        for name, path in files.items():
            if archive.read(name) != path.read_bytes():
                raise ValueError(f"ZIP content differs: {name}")
            permissions = (archive.getinfo(name).external_attr >> 16) & 0o777
            if permissions != path.stat().st_mode & 0o777:
                raise ValueError(f"ZIP permissions differ: {name}")
    print(f"PASS: both manifests and {len(files)} ZIP files match the project")


def package():
    check_privacy(include_archives=False)
    check_build()
    bundle_files()
    ARCHIVE.parent.mkdir(exist_ok=True)
    write_if_changed(BUNDLE_SUMS, manifest(BUNDLE, bundle_files()))
    with tempfile.TemporaryDirectory(prefix="open-hidpi-package-") as folder:
        temporary = Path(folder) / "MacHiDPI.zip"
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(bundle_files() + [BUNDLE_SUMS]):
                archive.write(path, "MacHiDPI/" + path.relative_to(BUNDLE).as_posix())
        shutil.copyfile(temporary, ARCHIVE)
    write_if_changed(PROJECT_SUMS, manifest(ROOT, project_files()))
    check()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Verify without writing files")
    arguments = parser.parse_args()
    try:
        check() if arguments.check else package()
    except (OSError, ValueError, subprocess.CalledProcessError, zipfile.BadZipFile) as error:
        parser.exit(1, f"Error: {error}\n")
