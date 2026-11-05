"""Check actual Swift group matching, shared-flag policy and mode selection without display access."""
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
source = (root / "MacHiDPI/source/MacHiDPI.swift").read_text()
support = "\n".join(line for line in source.splitlines()
                    if line.startswith(("struct ToolError:", "func require(")))
matching = source[source.index("func matchingDisplayID("):source.index("func modelDisplays(")]
group_selection = source[source.index("func modelDisplays("):source.index("func selectedDisplay(")]
flags = source[source.index("func sharedFlagBaseline("):source.index("func flag()")]
saved = source[source.index("struct SavedMode:"):source.index("func otherManagedBackups(")]
sizes = source[source.index("func configurationSizes(for"):source.index("func configuration(for")]
presets = source[source.index("func desktopSizes("):source.index("func makeConfiguration(")]
record_update = source[source.index("        _ = try sharedFlagBaseline(current: backup.originalFlag"):source.index("    } else {\n        let screens = try displays.map")]
stubs = r'''
struct CGDisplayMode {
    let width: Int, height: Int, pixelWidth: Int, pixelHeight: Int
    let refreshRate: Double = 60
}
struct Display { let id: UInt32; let uuid: String; let refresh: Int
    let nativeWidth = 1920, nativeHeight = 1200, vendor: UInt32 = 1715, product: UInt32 = 43598
    init(id: UInt32 = 2, uuid: String = "same", refresh: Int = 60) { self.id = id; self.uuid = uuid; self.refresh = refresh }
    init(_ id: UInt32, preferredRefresh: Int? = nil) throws { self.init(id:id,refresh:preferredRefresh ?? (id == 2 ? 60 : 75)) }
}
func onlineDisplays() throws -> [UInt32] { [2,3] }
func CGDisplayIsBuiltin(_ id: UInt32) -> UInt32 { 0 }
func CGDisplayVendorNumber(_ id: UInt32) -> UInt32 { 1715 }
func CGDisplayModelNumber(_ id: UInt32) -> UInt32 { 43598 }
let kCGDisplayShowDuplicateLowResolutionModes = "duplicates"
var fakeModes = [CGDisplayMode]()
func CGDisplayCopyAllDisplayModes(_ id: UInt32, _ options: CFDictionary) -> Any? { fakeModes }
func CGDisplayCopyDisplayMode(_ id: UInt32) -> CGDisplayMode? { fakeModes.first }
'''
checks = r'''
func rejects(_ operation: () throws -> Void) {
    do { try operation(); fatalError("expected rejection") } catch is ToolError { } catch { fatalError("unexpected error") }
}
assert(try matchingDisplayID(ids:[2,3],oldID:2,uuid:"same",uuidForID:{_ in "same"}) == 2)
assert(try matchingDisplayID(ids:[8,9],oldID:2,uuid:"left",uuidForID:{$0 == 8 ? "left" : "right"}) == 8)
rejects { _ = try matchingDisplayID(ids:[8,9],oldID:2,uuid:"same",uuidForID:{_ in "same"}) }
rejects { _ = try matchingDisplayID(ids:[2,3],oldID:2,uuid:"old",uuidForID:{_ in "different"}) }
rejects { _ = try matchingDisplayID(ids:[2,3],oldID:2,uuid:"",uuidForID:{_ in ""}) }
rejects { _ = try matchingDisplayID(ids:[2,3],oldID:2,uuid:"known",uuidForID:{_ in ""}) }
check(try modelDisplays(Display(id:2)).map(\.refresh) == [60,75])
let firstBaseline = try sharedFlagBaseline(current:nil,others:[])
let secondBaseline = try sharedFlagBaseline(current:"1",others:[firstBaseline])
assert(firstBaseline == nil && secondBaseline == nil)
assert(try restoredFlag(current:"1",baseline:firstBaseline,others:[secondBaseline]) == "1")
assert(try restoredFlag(current:"1",baseline:secondBaseline,others:[]) == nil)
assert(try restoredFlag(current:"1",baseline:"0",others:[]) == "0")
assert(try restoredFlag(current:"1",baseline:"1",others:[]) == "1")
rejects { _ = try sharedFlagBaseline(current:"0",others:[nil]) }
rejects { _ = try sharedFlagBaseline(current:"1",others:[nil,"1"]) }
rejects { _ = try restoredFlag(current:"1",baseline:"1",others:[nil]) }
rejects { _ = try restoredFlag(current:"0",baseline:nil,others:[]) }
rejects { _ = try restoredFlag(current:"1",baseline:"bad",others:[]) }
rejects { _ = try restoredFlag(current:"1",baseline:nil,others:["bad"]) }
rejects { _ = try sharedFlagBaseline(current:"1",others:["bad"]) }
let legacy = Data(#"{"vendor":1,"product":2,"target":"legacy","originalExists":false,"installedHash":"hash","managed":true}"#.utf8)
let decoded = try JSONDecoder().decode(Backup.self,from:legacy)
assert(decoded.originalScreens == nil && decoded.originalFlag == nil)
let original = SavedMode(width:1920,height:1200,pixelWidth:1920,pixelHeight:1200,hz:60)
let secondOriginal = SavedMode(width:1600,height:1000,pixelWidth:3200,pixelHeight:2000,hz:60)
let group = Backup(vendor:1,product:2,target:"group",originalExists:false,originalHash:nil,originalFlag:nil,installedHash:"hash",originalMode:original,managed:true,
    originalScreens:[ScreenBackup(id:2,uuid:"same",mode:original),ScreenBackup(id:3,uuid:"same",mode:secondOriginal)])
assert(try JSONDecoder().decode(Backup.self,from:JSONEncoder().encode(group)).originalScreens?.count == 2)
check(try recoveryModes([Display(id:2),Display(id:3)],backup:group).count == 2)
let mapped = try recoveryModes([Display(id:3),Display(id:2)],backup:group)
assert(mapped[0].1.width == 1600 && mapped[1].1.width == 1920)
rejects { _ = try recoveryModes([Display(id:8),Display(id:9)],backup:group) }
rejects { _ = try recoveryModes([Display(id:2),Display(id:3)],backup:decoded) }
let one = Backup(vendor:1,product:2,target:"group",originalExists:false,originalHash:nil,originalFlag:nil,installedHash:"hash",originalMode:original,managed:true,
    originalScreens:[ScreenBackup(id:2,uuid:"same",mode:original)])
rejects { _ = try recoveryModes([Display(id:2),Display(id:3)],backup:one) }
fakeModes = [CGDisplayMode(width:1920,height:1200,pixelWidth:1920,pixelHeight:1200),
             CGDisplayMode(width:1920,height:1200,pixelWidth:1920,pixelHeight:1200),
             CGDisplayMode(width:1600,height:1200,pixelWidth:1600,pixelHeight:1200),
             CGDisplayMode(width:1280,height:720,pixelWidth:1280,pixelHeight:720),
             CGDisplayMode(width:1024,height:640,pixelWidth:1024,pixelHeight:640),
             CGDisplayMode(width:3840,height:2400,pixelWidth:3840,pixelHeight:2400),
             CGDisplayMode(width:1280,height:800,pixelWidth:2560,pixelHeight:1600)]
let selected = try configurationSizes(for:Display(),arguments:["--all-resolutions"])
assert(selected.map { "\($0.width)x\($0.height)" } == ["1920x1200","1600x1200","1280x720"])
assert(try configurationSizes(for:Display(),arguments:[]).count == 11)
fakeModes = []
rejects { _ = try configurationSizes(for:Display(),arguments:["--all-resolutions"]) }
fakeModes = [CGDisplayMode(width:1920,height:1200,pixelWidth:1920,pixelHeight:1200)]
var migrated = decoded
rejects { try updateRecord(&migrated,displays:[Display(id:2),Display(id:3)],currentHash:nil) }
migrated.managed = false
try updateRecord(&migrated,displays:[Display(id:2),Display(id:3)],currentHash:nil)
assert(migrated.originalScreens?.count == 2 && migrated.originalHash == nil && !migrated.originalExists)
check(try recoveryModes([Display(id:2),Display(id:3)],backup:migrated).count == 2)
rejects { try updateRecord(&migrated,displays:[Display(id:2),Display(id:3)],currentHash:"external-change") }
let existingFile = Data(#"{"vendor":1,"product":2,"target":"legacy","originalExists":true,"originalHash":"first-file","installedHash":"installed","managed":false}"#.utf8)
var withFile = try JSONDecoder().decode(Backup.self,from:existingFile)
try updateRecord(&withFile,displays:[Display(id:2),Display(id:3)],currentHash:"first-file")
assert(withFile.originalHash == "first-file" && withFile.originalExists && withFile.originalScreens?.count == 2)
print("PASS: duplicate-model identity; ambiguous IDs rejected; multi-model flag lifecycle; legacy/group backups; existing-resolution filtering")
'''
# assert() autoclosures cannot throw; evaluate throwing expressions with a rethrowing check.
checks = checks.replace("assert(try ", "check(try ")
checks = "func check(_ value: Bool) { assert(value) }\n" + checks
with tempfile.TemporaryDirectory(prefix="open-hidpi-groups-") as folder:
    folder = Path(folder)
    swift = folder / "main.swift"
    update = "func updateRecord(_ backup: inout Backup, displays: [Display], currentHash: String?) throws {\nlet initialFlag: String? = \"1\", baseline: String? = nil\nlet others = [Backup]()\n" + record_update + "\n}\n"
    swift.write_text("import Foundation\nimport CoreFoundation\n" + support + "\n" + stubs + matching + group_selection + flags + saved + presets + sizes + update + checks)
    binary = folder / "check"
    subprocess.run(["swiftc", "-warnings-as-errors", "-module-cache-path",
                    str(folder / "module-cache"), str(swift), "-o", str(binary)], check=True)
    subprocess.run([str(binary)], check=True)
