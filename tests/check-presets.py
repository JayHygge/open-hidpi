"""Check the actual Swift generator without accessing or changing displays."""
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
source = (root / "MacHiDPI/source/MacHiDPI.swift").read_text()
generator = source[source.index("func desktopSizes("):source.index("func configurationSizes(for")]
support = "\n".join(line for line in source.splitlines()
                    if line.startswith(("struct ToolError:", "func require(")))
checks = r'''
let expected = [(3440,1440), (3268,1368), (3096,1296), (2924,1224),
                (2752,1152), (2580,1080), (2408,1008), (2236,936),
                (2064,864), (1892,792), (1720,720)]
let sizes = try desktopSizes(width: 3440, height: 1440)
assert(sizes.count == expected.count)
for (size, target) in zip(sizes, expected) {
    assert(size.width == target.0 && size.height == target.1)
    assert(size.width * 1440 == size.height * 3440)
}
func entry(_ words: [UInt32]) -> Data {
    var result = Data()
    for var word in words.map({ $0.bigEndian }) {
        withUnsafeBytes(of: &word) { result.append(contentsOf: $0) }
    }
    return result
}
let data = try makeConfiguration(width: 3440, height: 1440)
let plist = try PropertyListSerialization.propertyList(from: data, format: nil) as! [String: Any]
let records = plist["scale-resolutions"] as! [Data]
assert(records.count == 32 && Set(records).count == 32)
assert(records.allSatisfy { $0.count == 8 || $0.count == 16 })
for size in sizes {
    assert(records.contains(entry([UInt32(size.width), UInt32(size.height)])))
    assert(records.contains(entry([UInt32(size.width * 2), UInt32(size.height * 2)])))
    assert(records.contains(entry([UInt32(size.width * 2), UInt32(size.height * 2), 9, 0x00200000])))
}
for (width, height) in [(0,1440), (-1,1440), (3440,0), (3440,-1), (16385,1440), (3440,16385)] {
    do { _ = try makeConfiguration(width: width, height: height); fatalError("accepted invalid size") }
    catch is ToolError { }
}
let other = try desktopSizes(width: 3840, height: 2160)
assert(other.count == 11 && other.first!.width == 3840 && other.last!.height == 1080)
let duo: [(width:Int,height:Int)] = [(1920,1200),(1920,1080),(1600,1200),(1600,1000),(1344,1008),
           (1344,840),(1280,1024),(1280,960),(1280,800),(1280,720)]
let duoData = try makeConfiguration(width: 1920, height: 1200, sizes: duo)
let duoPlist = try PropertyListSerialization.propertyList(from: duoData, format: nil) as! [String: Any]
let duoRecords = duoPlist["scale-resolutions"] as! [Data]
assert(duoRecords.count == 30)
for size in duo {
    assert(duoRecords.contains(entry([UInt32(size.width*2),UInt32(size.height*2),9,0x00200000])))
}
for invalid in [[(width:0,height:1200)],[(1921,1200)],[(1920,1201)],[]] {
    do { _ = try makeConfiguration(width:1920,height:1200,sizes:invalid); fatalError("accepted invalid custom size") }
    catch is ToolError { }
}
print("PASS: 11 default presets; Duo 10 targets and 30 records; 2x encodings; invalid inputs")
'''
with tempfile.TemporaryDirectory(prefix="open-hidpi-presets-") as folder:
    folder = Path(folder)
    swift = folder / "main.swift"
    swift.write_text("import Foundation\n" + support + "\n" + generator + checks)
    binary = folder / "check"
    subprocess.run(["swiftc", "-warnings-as-errors", "-module-cache-path",
                    str(folder / "module-cache"), str(swift), "-o", str(binary)], check=True)
    subprocess.run([str(binary)], check=True)
