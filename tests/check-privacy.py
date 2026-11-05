"""Check privacy rules with synthetic data; never print credential or identity values."""
from pathlib import Path
import importlib.util
import sys


sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("project_privacy", ROOT / "scripts/privacy.py")
privacy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(privacy)

samples = [
    b"/Users/" + b"synthetic-person/Library/example",
    b"/var/folders/" + b"aa/" + b"x" * 24 + b"/C/cache",
    b"12345678" + b"-1234" * 3 + b"-" + b"123456789012",
    b"-----BEGIN " + b"PRIVATE KEY-----",
    b"AKIA" + b"A" * 16,
    b"ghp_" + b"x" * 36,
    b"sk-" + b"x" * 32,
    b"Bearer " + b"x" * 32,
    b"https://" + b"example:synthetic-password@example.invalid",
    b"api_key = '" + b"synthetic-credential" + b"'",
    str(Path.home()).encode(),
    str(ROOT).encode(),
]
for sample in samples:
    findings = privacy.scan(sample, "fixture.txt")
    assert findings
    rendered = repr(findings).encode()
    assert sample not in rendered
    assert sample not in repr(privacy.scan(sample, sample.decode())).encode()
assert not privacy.scan(b"/Library/Displays/Contents/Resources/Overrides", "safe.txt")
assert not privacy.scan(b"UUID().uuidString; Path.home(); <UUID_REDACTED>", "safe.txt")
assert not privacy.scan(b"Apple M1 Pro; vendor 10ac; product a22b; 3440x1440", "safe.txt")
print("PASS: synthetic identity/credential patterns detected; findings hide matched values; system paths and runtime identifiers allowed")
