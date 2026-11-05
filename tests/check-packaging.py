"""Exercise packaging and failure checks in a temporary repository; no display APIs."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile


ROOT = Path(__file__).resolve().parents[1]


with tempfile.TemporaryDirectory(prefix="open-hidpi-package-check-") as folder:
    project = Path(folder)
    subprocess.run(["git", "init", "-q", str(project)], check=True)
    (project / "scripts").mkdir()
    for name in ["package.py", "build.py", "privacy.py"]:
        shutil.copyfile(ROOT / "scripts" / name, project / "scripts" / name)
    bundle = project / "MacHiDPI"
    bundle.mkdir()
    inputs = ["MacHiDPI", "source/MacHiDPI.swift", "使用说明.md", "验证记录.md",
              "LICENSE", "THIRD_PARTY_NOTICES.md",
              "安装并开启.command", "恢复原配置.command", "检查状态.command",
              "直接开启HiDPI.command", "重新连接并开启.command"]
    for name in inputs:
        path = bundle / name
        path.parent.mkdir(exist_ok=True)
        path.write_text("Fixture input\n")
        if name == "MacHiDPI" or name.endswith(".command"):
            path.chmod(0o755)
    for name in ("LICENSE", "THIRD_PARTY_NOTICES.md"):
        shutil.copyfile(bundle / name, project / name)
    binary = bundle / "MacHiDPI"
    source = bundle / "source/MacHiDPI.swift"
    executable = bundle / "检查状态.command"
    record = {"schema": 1, "target": "arm64-apple-macos14.0",
              "sourceSHA256": hashlib.sha256(source.read_bytes()).hexdigest(),
              "binarySHA256": hashlib.sha256(binary.read_bytes()).hexdigest()}
    (bundle / "build.json").write_text(json.dumps(record))
    (project / "README.md").write_text("Fixture\n")
    (project / ".gitignore").write_text("private/\n__pycache__/\nMacHiDPI/local-note.txt\n")
    (project / "private").mkdir()
    (project / "private/evidence.txt").write_text("Bearer " + "x" * 32)
    (bundle / "local-note.txt").write_text("Ignored local input\n")
    (bundle / "temporary.bak").write_text("Non-release input\n")

    def run(*arguments, success=True):
        result = subprocess.run([sys.executable, "scripts/package.py", *arguments],
                                cwd=project, capture_output=True, text=True)
        assert (result.returncode == 0) == success, result.stdout + result.stderr
        return result

    run()
    assert not (project / "scripts/__pycache__").exists()
    archive_path = project / "release/MacHiDPI.zip"
    project_sums = project / "release/SHA256SUMS.project"
    original_zip = archive_path.read_bytes()
    original_sums = project_sums.read_bytes()
    assert b"private/evidence.txt" not in original_sums
    assert b"MacHiDPI/local-note.txt" not in original_sums
    with zipfile.ZipFile(archive_path) as archive:
        assert set(archive.namelist()) == {"MacHiDPI/" + name for name in inputs + ["build.json", "SHA256SUMS"]}
        assert (archive.getinfo("MacHiDPI/检查状态.command").external_attr >> 16) & 0o777 == 0o755
    run("--check")
    assert not (project / "scripts/__pycache__").exists()
    run()
    assert archive_path.read_bytes() == original_zip
    assert project_sums.read_bytes() == original_sums

    # Source and binary distributions must retain identical license notices.
    notice = bundle / "THIRD_PARTY_NOTICES.md"
    saved_notice = notice.read_bytes()
    notice.write_text("Changed notice\n")
    assert "Bundle notice differs" in run(success=False).stderr
    assert archive_path.read_bytes() == original_zip
    notice.write_bytes(saved_notice)

    secret = "Bearer " + "x" * 32
    original_readme = (project / "README.md").read_bytes()
    (project / "README.md").write_text(secret)
    rejected = run(success=False)
    assert "Sensitive information candidates" in rejected.stderr
    assert secret not in rejected.stderr
    assert archive_path.read_bytes() == original_zip
    (project / "README.md").write_bytes(original_readme)

    with zipfile.ZipFile(archive_path) as archive:
        old_entries = [(info, archive.read(info.filename)) for info in archive.infolist()]
    with zipfile.ZipFile(archive_path, "w") as archive:
        for info, data in old_entries:
            archive.writestr(info, secret.encode() if info.filename.endswith("使用说明.md") else data)
    rejected = run("--check", success=False)
    assert "Sensitive information candidates" in rejected.stderr and secret not in rejected.stderr
    archive_path.write_bytes(original_zip)
    run("--check")

    # Refuse incomplete inputs before rewriting any existing release artifacts.
    missing = project / "saved-command"
    executable.rename(missing)
    assert "Required bundle input" in run(success=False).stderr
    assert archive_path.read_bytes() == original_zip
    missing.rename(executable)
    binary.rename(project / "saved-program")
    run(success=False)
    (project / "saved-program").rename(binary)
    executable.chmod(0o644)
    assert "Required executable" in run(success=False).stderr
    assert archive_path.read_bytes() == original_zip
    executable.chmod(0o755)
    original_source = source.read_bytes()
    source.write_text("Changed source, existing binary\n")
    assert "Build record" in run(success=False).stderr
    run("--check", success=False)
    assert archive_path.read_bytes() == original_zip
    source.write_bytes(original_source)
    original_binary = binary.read_bytes()
    binary.write_text("Changed binary\n")
    assert "Build record" in run(success=False).stderr
    binary.write_bytes(original_binary)
    run("--check")

    # A failed compiler must retain the previously built program and record.
    failing_tools = project / "failing-tools"
    failing_tools.mkdir()
    compiler = failing_tools / "swiftc"
    compiler.write_text("#!/bin/sh\nexit 1\n")
    compiler.chmod(0o755)
    saved_record = (bundle / "build.json").read_bytes()
    result = subprocess.run([sys.executable, "scripts/build.py"], cwd=project,
                            env={**os.environ, "PATH": str(failing_tools)}, capture_output=True)
    assert result.returncode != 0
    assert binary.read_bytes() == original_binary
    assert (bundle / "build.json").read_bytes() == saved_record

    (project / "README.md").write_text("Changed\n")
    run("--check", success=False)
    assert project_sums.read_bytes() == original_sums
    assert archive_path.read_bytes() == original_zip
    run()
    (project / "new-document.md").write_text("New input\n")
    run("--check", success=False)
    run()

    # Bypass the outer ZIP hash to exercise content and permissions checks directly.
    original_zip = archive_path.read_bytes()
    with zipfile.ZipFile(archive_path) as archive:
        entries = [(info, archive.read(info.filename)) for info in archive.infolist()]
    with zipfile.ZipFile(archive_path, "w") as archive:
        for info, data in entries:
            archive.writestr(info, b"Unexpected content" if info.filename.endswith(".command") else data)
    # Check failure without regenerating the archive.
    current_sums = project_sums.read_text()
    old_hash = hashlib.sha256(original_zip).hexdigest()
    new_hash = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    project_sums.write_text(current_sums.replace(old_hash, new_hash))
    assert "ZIP content differs" in run("--check", success=False).stderr
    run()
    executable.chmod(0o644)
    assert "Required executable" in run("--check", success=False).stderr
    executable.chmod(0o755)
    run("--check")

print("PASS: explicit release list, required executable inputs, build hash binding, ignored evidence, repeatable ZIP, stale inputs and corrupt ZIP rejection")
