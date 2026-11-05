"""Exercise the real mode-save methods with fake display APIs; no screen changes."""
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
source = (root / "MacHiDPI/source/MacHiDPI.swift").read_text()
methods = source[source.index("    func applyMode("):source.index("\nfunc verified(")]
saved = source[source.index("struct SavedMode:"):source.index("struct Backup:")]
support = "\n".join(line for line in source.splitlines()
                    if line.startswith(("struct ToolError:", "func require(")))
stubs = r'''
struct CGConfigureOption: Equatable {
    let value: Int
    static let forSession = Self(value: 1), permanently = Self(value: 2)
}
struct CGError: Equatable {
    let rawValue: Int32
    static let success = Self(rawValue: 0)
}
typealias CGDisplayConfigRef = Int
struct CGDisplayMode {
    let width: Int, height: Int, pixelWidth: Int, pixelHeight: Int
    let refreshRate: Double
}
let hidpi = CGDisplayMode(width: 2924, height: 1224, pixelWidth: 5848, pixelHeight: 2448, refreshRate: 60)
let plain = CGDisplayMode(width: 2924, height: 1224, pixelWidth: 2924, pixelHeight: 1224, refreshRate: 60)
var current = hidpi, commitResult = CGError.success
var commits = [CGConfigureOption](), rollbacks = 0, confirmations = 0
var changeAtConfirmation = false
func CGDisplayCopyDisplayMode(_ id: UInt32) -> CGDisplayMode? { current }
func CGBeginDisplayConfiguration(_ config: inout CGDisplayConfigRef?) -> CGError { config = 1; return .success }
func CGCompleteDisplayConfiguration(_ config: CGDisplayConfigRef, _ scope: CGConfigureOption) -> CGError {
    commits.append(scope); return commitResult
}
func CGDisplaySetDisplayMode(_ id: UInt32, _ mode: CGDisplayMode, _ options: Int?) -> CGError {
    rollbacks += 1; current = mode; return .success
}
func usleep(_ interval: Int) { }
func confirm(_ arguments: [String], _ message: String) throws {
    confirmations += 1
    if changeAtConfirmation { current = plain }
}
struct Display { let id: UInt32 = 3, nativeWidth = 3440, nativeHeight = 1440, refresh = 60 }
struct Mode { let number: Int32, width: UInt32, height: UInt32, hz: UInt16, density: Float }
final class Native {
    func modes(_ id: UInt32) throws -> [Mode] {
        [Mode(number: 7, width: 2924, height: 1224, hz: 60, density: 2)]
    }
    func configure(_ config: CGDisplayConfigRef, _ id: UInt32, _ mode: Int32) { }
'''
checks = r'''
func expectFailure(_ operation: () throws -> Void) {
    do { try operation(); fatalError("expected rejection") } catch is ToolError { } catch { fatalError("unexpected error") }
}
let native = Native(), display = Display()
try native.persist(display, arguments: [])
assert(commits == [.permanently] && confirmations == 1 && rollbacks == 0)
assert(current.width == 2924 && current.pixelWidth == 5848)
commits = []
try native.applyMode(display, saved: SavedMode.current(display.id))
assert(commits == [.forSession])
commits = []; current = plain
expectFailure { try native.persist(display, arguments: []) }
assert(commits.isEmpty && confirmations == 1)
current = hidpi; changeAtConfirmation = true
expectFailure { try native.persist(display, arguments: []) }
assert(commits.isEmpty)
current = hidpi; changeAtConfirmation = false; commitResult = CGError(rawValue: 1000)
expectFailure { try native.persist(display, arguments: []) }
assert(commits == [.permanently] && rollbacks == 1)
print("PASS: current preset retained; permanent request; session default unchanged; non-HiDPI, confirmation race and commit failure rejected")
'''
with tempfile.TemporaryDirectory(prefix="open-hidpi-persistence-") as folder:
    folder = Path(folder)
    swift = folder / "main.swift"
    swift.write_text("import Foundation\n" + support + "\n" + stubs + methods + "\n" + saved + checks)
    binary = folder / "check"
    subprocess.run(["swiftc", "-warnings-as-errors", "-module-cache-path",
                    str(folder / "module-cache"), str(swift), "-o", str(binary)], check=True)
    subprocess.run([str(binary)], check=True)
