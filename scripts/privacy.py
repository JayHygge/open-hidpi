"""Check public project files and ZIP contents; report locations, never matched values."""
import argparse
from pathlib import Path
import re
import subprocess
import zipfile


ROOT = Path(__file__).resolve().parents[1]
PATTERNS = (
    ("personal home path", rb"/Users/[A-Za-z0-9_.-]+(?:/|\b)"),
    ("user-specific temporary path", rb"/(?:private/)?var/folders/[A-Za-z0-9_-]+/[A-Za-z0-9_-]{8,}/"),
    ("literal unique identifier", rb"\b[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}\b"),
    ("private key", rb"-----BEGIN " + rb"(?:[A-Z0-9]+ )?PRIVATE KEY-----"),
    ("AWS access key", rb"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    ("GitHub token", rb"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})"),
    ("API token", rb"\bsk-[A-Za-z0-9_-]{20,}"),
    ("bearer credential", rb"\bBearer [A-Za-z0-9_.-]{20,}"),
    ("URL credential", rb"https?://[^\s/:'\"]+:[^\s/@'\"]+@"),
    ("credential assignment", rb"(?i)\b(?:api[_-]?key|access[_-]?token|secret|password)\s*[:=]\s*['\"][A-Za-z0-9_+/=.-]{8,}['\"]"),
)


def public_files():
    result = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
                            cwd=ROOT, check=True, capture_output=True)
    paths = {ROOT / name.decode("utf-8") for name in result.stdout.split(b"\0") if name}
    return sorted(path for path in paths if path.is_file() and path.name != ".DS_Store")


def rules():
    patterns = list(PATTERNS)
    home = Path.home()
    for label, value in [("current home directory", str(home)), ("current project directory", str(ROOT))]:
        patterns.append((label, re.escape(value.encode())))
    if len(home.name) >= 4 and home.name.lower() not in {"root", "user", "runner", "admin", "administrator", "ubuntu", "codex"}:
        patterns.append(("local account name", re.escape(home.name.encode())))
    return patterns


def scan(data, location):
    patterns = rules()
    safe_location = location.encode()
    for _, pattern in patterns:
        safe_location = re.sub(pattern, b"<REDACTED>", safe_location)
    location = safe_location.decode("utf-8", errors="replace")
    findings = []
    for label, pattern in patterns:
        for match in re.finditer(pattern, data):
            findings.append((location, data.count(b"\n", 0, match.start()) + 1, label))
    return findings


def check_privacy(include_archives=True):
    findings = []
    for path in public_files():
        relative = path.relative_to(ROOT).as_posix()
        findings.extend(scan(relative.encode(), relative))
        if path.suffix.lower() == ".zip":
            if include_archives:
                with zipfile.ZipFile(path) as archive:
                    for name in archive.namelist():
                        findings.extend(scan(name.encode(), relative + "!" + name))
                        findings.extend(scan(archive.read(name), relative + "!" + name))
        else:
            findings.extend(scan(path.read_bytes(), relative))
    if findings:
        locations = "\n".join(f"{path}:{line}: {kind}" for path, line, kind in sorted(set(findings)))
        raise ValueError("Sensitive information candidates; no matched values printed:\n" + locations)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    try:
        check_privacy()
        print("PASS: no configured privacy or credential patterns found in public files or ZIP contents")
    except (OSError, ValueError, subprocess.CalledProcessError, zipfile.BadZipFile) as error:
        parser.exit(1, f"Error: {error}\n")
