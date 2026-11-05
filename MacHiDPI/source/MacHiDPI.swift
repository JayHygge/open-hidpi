import Foundation
import CoreGraphics
import ColorSync
import CryptoKit
import Darwin

struct ToolError: Error, CustomStringConvertible { let description: String; init(_ s: String) { description = s } }
func require(_ condition: Bool, _ message: String) throws { if !condition { throw ToolError(message) } }
func digest(_ data: Data) -> String { SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined() }
func quote(_ s: String) -> String { "'" + s.replacingOccurrences(of: "'", with: "'\\''") + "'" }
func run(_ path: String, _ arguments: [String]) throws -> (Int32, Data, Data) {
    let process = Process(); process.executableURL = URL(fileURLWithPath: path); process.arguments = arguments
    let output = Pipe(), error = Pipe(); process.standardOutput = output; process.standardError = error
    try process.run()
    // Commands here return small diagnostics, not streaming output.
    let data = output.fileHandleForReading.readDataToEndOfFile()
    let errors = error.fileHandleForReading.readDataToEndOfFile()
    process.waitUntilExit(); return (process.terminationStatus, data, errors)
}
func text(_ data: Data) -> String { String(decoding: data, as: UTF8.self).trimmingCharacters(in: .whitespacesAndNewlines) }
func onlineDisplays() throws -> [CGDirectDisplayID] {
    var count: UInt32 = 0
    try require(CGGetOnlineDisplayList(0, nil, &count) == .success, "无法读取显示器数量。")
    var ids = [CGDirectDisplayID](repeating: 0, count: Int(count))
    try require(CGGetOnlineDisplayList(count, &ids, &count) == .success, "无法读取显示器列表。")
    return Array(ids.prefix(Int(count)))
}
struct Display {
    let id: CGDirectDisplayID
    let vendor: UInt32
    let product: UInt32
    let nativeWidth: Int
    let nativeHeight: Int
    let refresh: Int
    let uuid: String
    var model: String { String(format: "%x:%x", vendor, product) }
    var target: String { "/Library/Displays/Contents/Resources/Overrides/DisplayVendorID-\(String(vendor, radix: 16))/DisplayProductID-\(String(product, radix: 16))" }
    init(_ id: CGDirectDisplayID, preferredRefresh: Int? = nil) throws {
        self.id = id; vendor = CGDisplayVendorNumber(id); product = CGDisplayModelNumber(id)
        uuid = displayUUID(id)
        try require(CGDisplayIsBuiltin(id) == 0, "不能修改内置屏幕。")
        try require(vendor != 0 && product != 0, "显示器缺少可靠的厂商或产品标识，停止修改。")
        let options = [kCGDisplayShowDuplicateLowResolutionModes: true] as CFDictionary
        let modes = (CGDisplayCopyAllDisplayModes(id, options) as? [CGDisplayMode]) ?? []
        let native = modes.filter { ($0.ioFlags & 0x02000000) != 0 }
        let sizes = Set(native.map { "\($0.pixelWidth)x\($0.pixelHeight)" })
        try require(sizes.count == 1, "无法唯一确认原生面板尺寸，停止修改。")
        guard let m = native.first else { throw ToolError("未找到原生显示模式。") }
        nativeWidth = m.pixelWidth; nativeHeight = m.pixelHeight
        try require(nativeWidth > 0 && nativeHeight > 0 && nativeWidth <= 16384 && nativeHeight <= 16384, "原生尺寸不在支持范围。")
        guard let current = CGDisplayCopyDisplayMode(id) else { throw ToolError("无法读取当前模式。") }
        refresh = preferredRefresh ?? (current.refreshRate > 0 ? Int(current.refreshRate.rounded()) : 60)
    }
}
func displayUUID(_ id: UInt32) -> String {
    guard let uuid = CGDisplayCreateUUIDFromDisplayID(id)?.takeRetainedValue() else { return "" }
    return CFUUIDCreateString(nil, uuid) as String
}
func matchingDisplayID(ids: [UInt32], oldID: UInt32, uuid: String, uuidForID: (UInt32) -> String) throws -> UInt32 {
    let matches = ids.filter { !uuid.isEmpty && uuidForID($0) == uuid }
    if matches.count == 1 { return matches[0] }
    if !uuid.isEmpty && ids.contains(oldID) && uuidForID(oldID) == uuid { return oldID }
    throw ToolError("无法唯一识别原屏幕；保留内屏，请重新检查连接，不按同型号任意选屏。")
}
func modelDisplays(_ display: Display) throws -> [Display] {
    let matches = try onlineDisplays().filter { CGDisplayIsBuiltin($0) == 0 && CGDisplayVendorNumber($0) == display.vendor && CGDisplayModelNumber($0) == display.product }
    let displays = try matches.map { try Display($0) }
    try require(!displays.isEmpty && displays.allSatisfy { $0.nativeWidth == display.nativeWidth && $0.nativeHeight == display.nativeHeight }, "同型号屏幕的原生尺寸不一致，停止修改。")
    try require(displays.allSatisfy { !$0.uuid.isEmpty }, "无法读取同型号屏幕的系统 UUID，停止修改。")
    return displays
}
func selectedDisplay(_ arguments: [String], interactive: Bool) throws -> Display {
    let ids = try onlineDisplays().filter { CGDisplayIsBuiltin($0) == 0 }
    if let index = arguments.firstIndex(of: "--display") {
        try require(index + 1 < arguments.count, "--display 后需要当前显示器 ID。")
        guard let value = UInt32(arguments[index + 1]), ids.contains(value) else { throw ToolError("指定的外接显示器 ID 不存在。") }
        return try Display(value)
    }
    let displays = ids.compactMap { try? Display($0) }
    try require(!displays.isEmpty, "没有发现受支持的原生外接显示器。DisplayLink 不在本工具支持范围。")
    if displays.count != ids.count { print("部分外接连接无法可靠识别，已跳过；list 可查看详情。") }
    if displays.count == 1 { return displays[0] }
    for (index, d) in displays.enumerated() { print("\(index + 1). ID \(d.id) · \(d.model) · \(d.nativeWidth)×\(d.nativeHeight)") }
    try require(interactive, "有多台外接显示器，请使用 --display ID 明确指定。")
    print("选择显示器序号：", terminator: ""); fflush(stdout)
    guard let s = readLine(), let number = Int(s), (1...displays.count).contains(number) else { throw ToolError("未选择有效显示器。") }
    return displays[number - 1]
}
func desktopSizes(width: Int, height: Int) throws -> [(width: Int, height: Int)] {
    try require(width > 0 && height > 0 && width <= 16384 && height <= 16384, "分辨率参数无效。")
    // Eleven choices, from native desktop size to twice the apparent UI size.
    return stride(from: 100, through: 50, by: -5).map { percentage in
        (Int((Double(width) * Double(percentage) / 100).rounded()), Int((Double(height) * Double(percentage) / 100).rounded()))
    }
}
func makeConfiguration(width: Int, height: Int, sizes: [(width: Int, height: Int)]? = nil) throws -> Data {
    let targets = try sizes ?? desktopSizes(width: width, height: height)
    try require(!targets.isEmpty && targets.allSatisfy { $0.width > 0 && $0.height > 0 && $0.width <= width && $0.height <= height } && width > 0 && height > 0 && width <= 16384 && height <= 16384, "分辨率参数无效。")
    var entries = Set<Data>()
    func add(_ words: [UInt32]) { var data = Data(); for var word in words.map({ $0.bigEndian }) { withUnsafeBytes(of: &word) { data.append(contentsOf: $0) } }; entries.insert(data) }
    func addSize(_ w: Int, _ h: Int) { add([UInt32(w), UInt32(h)]); add([UInt32(w * 2), UInt32(h * 2)]); add([UInt32(w * 2), UInt32(h * 2), 9, 0x00200000]) }
    for size in targets { addSize(size.width, size.height) }
    let sorted = entries.sorted { $0.lexicographicallyPrecedes($1) }
    return try PropertyListSerialization.data(fromPropertyList: ["scale-resolutions": sorted], format: .xml, options: 0)
}
func configurationSizes(for display: Display, arguments: [String]) throws -> [(width: Int, height: Int)] {
    if !arguments.contains("--all-resolutions") { return try desktopSizes(width: display.nativeWidth, height: display.nativeHeight) }
    let modes = CGDisplayCopyAllDisplayModes(display.id, [kCGDisplayShowDuplicateLowResolutionModes: true] as CFDictionary) as? [CGDisplayMode] ?? []
    let sizes = modes.filter { $0.width > 1024 && $0.width <= display.nativeWidth && $0.height <= display.nativeHeight && $0.pixelWidth == $0.width && $0.pixelHeight == $0.height }
    let unique = Dictionary(grouping: sizes, by: { "\($0.width)x\($0.height)" }).values.compactMap { $0.first }
    try require(!unique.isEmpty, "没有找到宽度大于 1024 的普通分辨率，停止生成。")
    return unique.sorted { $0.width == $1.width ? $0.height > $1.height : $0.width > $1.width }.map { ($0.width, $0.height) }
}
func configuration(for display: Display, arguments: [String] = []) throws -> Data {
    let raw = try makeConfiguration(width: display.nativeWidth, height: display.nativeHeight, sizes: configurationSizes(for: display, arguments: arguments))
    var object = try PropertyListSerialization.propertyList(from: raw, format: nil) as! [String: Any]
    object["DisplayVendorID"] = display.vendor; object["DisplayProductID"] = display.product
    return try PropertyListSerialization.data(fromPropertyList: object, format: .xml, options: 0)
}
struct Mode { let number: Int32; let width: UInt32; let height: UInt32; let hz: UInt16; let density: Float }
final class Native {
    typealias Count = @convention(c) (UInt32, UnsafeMutablePointer<Int32>) -> Void
    typealias Description = @convention(c) (UInt32, Int32, UnsafeMutableRawPointer, Int32) -> Void
    typealias Configure = @convention(c) (CGDisplayConfigRef, UInt32, Int32) -> Void
    typealias Enabled = @convention(c) (CGDisplayConfigRef, UInt32, Bool) -> Int32
    let count: Count; let description: Description; let configure: Configure; let enabled: Enabled
    init() throws {
        guard let handle = dlopen("/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics", RTLD_LAZY),
              let a = dlsym(handle, "CGSGetNumberOfDisplayModes"), let b = dlsym(handle, "CGSGetDisplayModeDescriptionOfLength"),
              let c = dlsym(handle, "CGSConfigureDisplayMode"), let d = dlsym(handle, "CGSConfigureDisplayEnabled") else { throw ToolError("当前 macOS 缺少所需显示接口。") }
        count = unsafeBitCast(a, to: Count.self); description = unsafeBitCast(b, to: Description.self)
        configure = unsafeBitCast(c, to: Configure.self); enabled = unsafeBitCast(d, to: Enabled.self)
    }
    func modes(_ id: UInt32) throws -> [Mode] {
        var total: Int32 = 0; count(id, &total)
        try require(total > 0 && total <= 100000, "底层模式数量异常。")
        return (0..<total).map { index in
            var bytes = [UInt8](repeating: 0, count: 0xDC)
            return bytes.withUnsafeMutableBytes { buffer in
                description(id, index, buffer.baseAddress!, 0xD4)
                return Mode(number: Int32(bitPattern: buffer.loadUnaligned(fromByteOffset: 0, as: UInt32.self)), width: buffer.loadUnaligned(fromByteOffset: 8, as: UInt32.self), height: buffer.loadUnaligned(fromByteOffset: 12, as: UInt32.self), hz: buffer.loadUnaligned(fromByteOffset: 0xBE, as: UInt16.self), density: buffer.loadUnaligned(fromByteOffset: 0xD0, as: Float.self))
            }
        }
    }
    func findAgain(_ old: Display) throws -> Display {
        let matches = try onlineDisplays().filter { CGDisplayIsBuiltin($0) == 0 && CGDisplayVendorNumber($0) == old.vendor && CGDisplayModelNumber($0) == old.product }
        let id = try matchingDisplayID(ids: matches, oldID: old.id, uuid: old.uuid, uuidForID: displayUUID)
        return try Display(id, preferredRefresh: old.refresh)
    }
    func setEnabled(_ id: UInt32, _ value: Bool) -> Int32 {
        var config: CGDisplayConfigRef?
        let start = CGBeginDisplayConfiguration(&config)
        guard start == .success, let config else { return Int32(start.rawValue) }
        let result = enabled(config, id, value)
        if result != 0 { CGCancelDisplayConfiguration(config); return result }
        return Int32(CGCompleteDisplayConfiguration(config, .forSession).rawValue)
    }
    func reconnect(_ display: Display) throws -> Display {
        try require(try onlineDisplays().contains { CGDisplayIsBuiltin($0) != 0 && CGDisplayIsActive($0) != 0 }, "软件重连需要 MacBook 内屏开启，请打开屏幕再执行。")
        let off = setEnabled(display.id, false); print("断开返回值：\(off)")
        usleep(1_000_000)
        var on = setEnabled(display.id, true); print("重连返回值：\(on)")
        for attempt in 0..<40 {
            if let result = try? findAgain(display), CGDisplayIsActive(result.id) != 0 { return result }
            if attempt == 10 || attempt == 20 { on = setEnabled(display.id, true); print("重连重试返回值：\(on)") }
            usleep(100_000)
        }
        throw ToolError("未确认外屏恢复。内屏保持开启；请拔插外屏连接线。")
    }
    func applyMode(_ display: Display, saved: SavedMode, scope: CGConfigureOption = .forSession) throws {
        let density = Float(saved.pixelWidth) / Float(saved.width)
        try require(density == 1 || density == 2, "原模式渲染比例不受支持，未切换模式。")
        let matches = try modes(display.id).filter { $0.width == saved.width && $0.height == saved.height && $0.hz == Int(saved.hz.rounded()) && $0.density == density }
        try require(matches.count == 1, "找不到唯一目标模式（\(saved.width)×\(saved.height)、\(Int(saved.hz.rounded())) Hz、\(density)×）。")
        guard let original = CGDisplayCopyDisplayMode(display.id) else { throw ToolError("无法读取当前模式。") }
        var config: CGDisplayConfigRef?
        try require(CGBeginDisplayConfiguration(&config) == .success, "无法开始切换。")
        guard let config else { throw ToolError("未取得显示配置。") }
        configure(config, display.id, matches[0].number)
        let result = CGCompleteDisplayConfiguration(config, scope)
        for _ in 0..<20 {
            if let current = CGDisplayCopyDisplayMode(display.id), result == .success && saved.matches(current) { return }
            usleep(100_000)
        }
        let restored = CGDisplaySetDisplayMode(display.id, original, nil)
        throw ToolError("模式未通过核验，切换返回 \(result.rawValue)，恢复原模式返回 \(restored.rawValue)。")
    }
    func enable(_ display: Display) throws {
        try applyMode(display, saved: SavedMode(width: display.nativeWidth, height: display.nativeHeight, pixelWidth: display.nativeWidth * 2, pixelHeight: display.nativeHeight * 2, hz: Double(display.refresh)))
    }
    func persist(_ display: Display, arguments: [String]) throws {
        let saved = try SavedMode.current(display.id)
        try require(saved.pixelWidth == saved.width * 2 && saved.pixelHeight == saved.height * 2, "当前不是 2× HiDPI，请先选择需要的 HiDPI 档位，再保存。")
        try confirm(arguments, "将请求 macOS 永久保存当前外屏模式：\(saved.width)×\(saved.height)，渲染 \(saved.pixelWidth)×\(saved.pixelHeight)，\(saved.hz) Hz。可能短暂黑屏；系统会更新显示偏好。")
        guard let current = CGDisplayCopyDisplayMode(display.id), saved.matches(current) else { throw ToolError("确认期间显示模式已变化，停止保存；请重新运行。") }
        try applyMode(display, saved: saved, scope: .permanently)
        print("永久保存请求已成功提交，当前像素核验通过。macOS 仍可能将不支持的永久配置降为会话配置；请拔插后再检查状态，不能据此保证保持成功。")
    }
}
func verified(_ display: Display) -> Bool {
    guard let m = CGDisplayCopyDisplayMode(display.id) else { return false }
    return m.width == display.nativeWidth && m.height == display.nativeHeight && m.pixelWidth == display.nativeWidth * 2 && m.pixelHeight == display.nativeHeight * 2 && abs(m.refreshRate - Double(display.refresh)) < 1
}
func status(_ display: Display, native: Native) throws {
    guard let current = CGDisplayCopyDisplayMode(display.id) else { throw ToolError("无法读取当前模式。") }
    let modes = try native.modes(display.id)
    print("外接显示器：ID \(display.id)，型号 \(display.model)，原生 \(display.nativeWidth)×\(display.nativeHeight)")
    print("当前桌面：\(current.width)×\(current.height)；实际渲染：\(current.pixelWidth)×\(current.pixelHeight)；\(current.refreshRate) Hz")
    let currentHiDPI = current.pixelWidth == current.width * 2 && current.pixelHeight == current.height * 2
    print("当前 2× HiDPI：\(currentHiDPI ? "已启用" : "未启用")；原生尺寸目标：\(verified(display) ? "已达到" : "未达到")；底层模式数：\(modes.count)")
}
struct SavedMode: Codable {
    let width: Int; let height: Int; let pixelWidth: Int; let pixelHeight: Int; let hz: Double
    func matches(_ mode: CGDisplayMode) -> Bool { mode.width == width && mode.height == height && mode.pixelWidth == pixelWidth && mode.pixelHeight == pixelHeight && abs(mode.refreshRate - hz) < 1 }
    static func current(_ id: UInt32) throws -> SavedMode {
        guard let mode = CGDisplayCopyDisplayMode(id) else { throw ToolError("无法保存当前模式。") }
        return SavedMode(width: mode.width, height: mode.height, pixelWidth: mode.pixelWidth, pixelHeight: mode.pixelHeight, hz: mode.refreshRate)
    }
}
struct Backup: Codable {
    let vendor: UInt32; let product: UInt32; let target: String
    let originalExists: Bool; let originalHash: String?; var originalFlag: String?
    var installedHash: String
    let originalMode: SavedMode?
    var managed: Bool?
    var originalScreens: [ScreenBackup]?
}
struct ScreenBackup: Codable {
    let id: UInt32; let uuid: String; let mode: SavedMode
}
func recoveryModes(_ displays: [Display], backup: Backup) throws -> [(Display, SavedMode)] {
    let result: [(Display, SavedMode)]
    if let screens = backup.originalScreens {
        try require(!screens.isEmpty && Set(screens.map(\.id)).count == screens.count, "双屏恢复快照为空或标识重复。")
        let assignments = try displays.map { screen -> (Display, SavedMode, UInt32) in
            let id = try matchingDisplayID(ids: screens.map(\.id), oldID: screen.id, uuid: screen.uuid, uuidForID: { id in screens.first { $0.id == id }?.uuid ?? "" })
            guard let saved = screens.first(where: { $0.id == id }) else { throw ToolError("缺少屏幕恢复模式。") }
            return (screen, saved.mode, id)
        }
        try require(Set(assignments.map { $0.2 }).count == assignments.count, "恢复屏幕匹配重复，停止。")
        result = assignments.map { ($0.0, $0.1) }
    } else {
        try require(displays.count == 1, "旧记录仅保存单屏模式，请只连接一块该型号屏幕后恢复。")
        result = backup.originalMode.map { [(displays[0], $0)] } ?? []
    }
    try require(result.allSatisfy {
        let m = $0.1
        return m.width > 0 && m.height > 0 && m.width <= 16384 && m.height <= 16384 && m.hz.isFinite && m.hz > 0 &&
            ((m.pixelWidth == m.width && m.pixelHeight == m.height) || (m.pixelWidth == 2*m.width && m.pixelHeight == 2*m.height))
    }, "恢复模式数据无效，停止修改。")
    return result
}
func otherManagedBackups(_ display: Display) throws -> [Backup] {
    let root = stateDirectory(display).deletingLastPathComponent()
    if !FileManager.default.fileExists(atPath: root.path) { return [] }
    var records = [Backup]()
    for folder in try FileManager.default.contentsOfDirectory(at: root, includingPropertiesForKeys: nil) where folder != stateDirectory(display) {
        let path = folder.appendingPathComponent("state.json")
        if !FileManager.default.fileExists(atPath: path.path) { continue }
        let record = try JSONDecoder().decode(Backup.self, from: Data(contentsOf: path))
        try require(record.managed != nil, "其他型号的旧恢复记录缺少管理状态，停止修改。")
        if record.managed == true { records.append(record) }
    }
    return records
}
func sharedFlagBaseline(current: String?, others: [String?]) throws -> String? {
    try require((current == nil || current == "0" || current == "1") && others.allSatisfy { $0 == nil || $0 == "0" || $0 == "1" }, "全局开关值或恢复基准无效。")
    guard let first = others.first else { return current }
    try require(current == "1" && others.allSatisfy { $0 == first }, "多型号的全局开关基准不一致或开关已变化，停止修改。")
    return first
}
func restoredFlag(current: String?, baseline: String?, others: [String?]) throws -> String? {
    _ = try sharedFlagBaseline(current: baseline, others: [])
    _ = try sharedFlagBaseline(current: current, others: [])
    if !others.isEmpty {
        let shared = try sharedFlagBaseline(current: current, others: others)
        try require(shared == baseline, "全局开关恢复基准冲突，停止恢复。")
        return current
    }
    try require(current == "1" || current == baseline, "显示开关已被其他操作更改，停止自动恢复。")
    return baseline
}
func flag() throws -> String? {
    let (code, out, _) = try run("/usr/bin/defaults", ["read", "/Library/Preferences/com.apple.windowserver", "DisplayResolutionEnabled"])
    if code != 0 { return nil }
    let value = text(out); try require(value == "0" || value == "1", "DisplayResolutionEnabled 不是布尔值，停止修改。")
    return value
}
func stateDirectory(_ display: Display) -> URL {
    FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent("Library/Application Support/MacHiDPI/\(display.model.replacingOccurrences(of: ":", with: "-"))")
}
func confirm(_ arguments: [String], _ message: String) throws {
    print(message)
    if arguments.contains("--yes") { return }
    print("输入 YES 确认，其他输入取消：", terminator: ""); fflush(stdout)
    try require(readLine() == "YES", "操作已取消，系统配置未修改。")
}
func authorize(_ script: String, directory: URL) throws {
    // Privileged AppleScript cannot read the user's Documents folder on some Macs.
    let path = directory.appendingPathComponent("action.sh")
    try script.write(to: path, atomically: true, encoding: .utf8)
    let command = "/bin/bash " + quote(path.path)
    let literal = command.replacingOccurrences(of: "\\", with: "\\\\").replacingOccurrences(of: "\"", with: "\\\"")
    let (code, out, err) = try run("/usr/bin/osascript", ["-e", "do shell script \"\(literal)\" with administrator privileges"])
    if !out.isEmpty { print(text(out)) }
    try require(code == 0, "管理员操作未完成：\(text(err))")
}
func makeStage() throws -> URL {
    let url = URL(fileURLWithPath: "/private/tmp").appendingPathComponent("MacHiDPI-\(UUID().uuidString)")
    try FileManager.default.createDirectory(at: url, withIntermediateDirectories: false, attributes: [.posixPermissions: 0o700])
    return url
}
func guardHash(_ target: String, expected: String?) -> String {
    if let expected { return "[[ -f \(quote(target)) && \"$(/usr/bin/shasum -a 256 \(quote(target)) | /usr/bin/awk '{print $1}')\" == \(quote(expected)) ]] || { echo '系统配置已变化，停止覆盖。' >&2; exit 1; }" }
    return "[[ ! -e \(quote(target)) ]] || { echo '系统配置已出现，停止覆盖。' >&2; exit 1; }"
}
func installedContent(_ display: Display) throws -> Data? {
    if !FileManager.default.fileExists(atPath: display.target) { return nil }
    let data = try Data(contentsOf: URL(fileURLWithPath: display.target))
    let object = try PropertyListSerialization.propertyList(from: data, format: nil) as? [String: Any]
    try require(object != nil, "现有覆盖文件不是有效 plist，停止修改。")
    return data
}
func install(_ display: Display, arguments: [String], native: Native) throws {
    let displays = try modelDisplays(display)
    let others = try otherManagedBackups(display)
    let initialFlag = try flag()
    let baseline = try sharedFlagBaseline(current: initialFlag, others: others.map(\.originalFlag))
    try require(try onlineDisplays().contains { CGDisplayIsBuiltin($0) != 0 && CGDisplayIsActive($0) != 0 }, "请先打开 MacBook 内屏，以便软件重连时保持可操作。")
    let data = try configuration(for: display, arguments: arguments), hash = digest(data)
    let current = try installedContent(display), currentHash = current.map(digest)
    let folder = stateDirectory(display), metadata = folder.appendingPathComponent("state.json"), original = folder.appendingPathComponent("original.plist")
    var backup: Backup
    if FileManager.default.fileExists(atPath: metadata.path) {
        backup = try JSONDecoder().decode(Backup.self, from: Data(contentsOf: metadata))
        try require(backup.target == display.target && backup.vendor == display.vendor && backup.product == display.product, "恢复记录不匹配。")
        try require(currentHash == backup.installedHash || currentHash == backup.originalHash, "系统覆盖文件被其他工具更改，停止自动覆盖。")
        _ = try sharedFlagBaseline(current: backup.originalFlag, others: [])
        if backup.managed == true {
            try require(initialFlag == "1" || initialFlag == backup.originalFlag, "全局开关已被其他操作更改，停止安装。")
            try require(others.isEmpty || backup.originalFlag == baseline, "全局开关恢复基准冲突，停止安装。")
        } else if backup.managed == false {
            try require(currentHash == backup.originalHash, "已恢复记录与当前覆盖文件不一致，停止建立本轮快照。")
            backup.originalFlag = baseline
            backup.originalScreens = try displays.map { ScreenBackup(id: $0.id, uuid: $0.uuid, mode: try SavedMode.current($0.id)) }
        }
        try require(displays.count == 1 || backup.originalScreens != nil, "旧记录只含单屏恢复基准，请先恢复该型号，再重新安装双屏配置。")
        _ = try recoveryModes(displays, backup: backup)
    } else {
        let screens = try displays.map { ScreenBackup(id: $0.id, uuid: $0.uuid, mode: try SavedMode.current($0.id)) }
        backup = Backup(vendor: display.vendor, product: display.product, target: display.target, originalExists: current != nil, originalHash: currentHash, originalFlag: baseline, installedHash: hash, originalMode: try SavedMode.current(display.id), managed: true, originalScreens: screens)
    }
    try confirm(arguments, "将为 \(display.model) 安装生成的 HiDPI 配置，共影响同型号 \(displays.count) 块屏：\n\(display.target)\n将逐屏断开、重连并切至原生尺寸 HiDPI，窗口可能移到内屏；保存原文件、各屏模式及共享开关基准，可恢复。无需重启。")
    let oldFlag = try flag()
    try require(oldFlag == initialFlag, "确认期间全局开关已变化，停止安装。")
    try FileManager.default.createDirectory(at: folder, withIntermediateDirectories: true, attributes: [.posixPermissions: 0o700])
    if !FileManager.default.fileExists(atPath: metadata.path), let current { try current.write(to: original, options: .atomic) }
    if backup.originalExists { try require(FileManager.default.fileExists(atPath: original.path) && digest(Data(contentsOf: original)) == backup.originalHash, "原配置备份缺失或变化。") }
    backup.installedHash = hash; backup.managed = true
    try JSONEncoder().encode(backup).write(to: metadata, options: .atomic)
    let stage = try makeStage(); let source = stage.appendingPathComponent("override.plist")
    try data.write(to: source, options: .atomic)
    let flagGuard = "value=$(/usr/bin/defaults read /Library/Preferences/com.apple.windowserver DisplayResolutionEnabled 2>/dev/null || true)\n[[ \"$value\" == \(quote(oldFlag ?? "")) ]] || { echo '显示开关已变化，停止。' >&2; exit 1; }"
    let script = """
    set -euo pipefail
    \(guardHash(display.target, expected: currentHash))
    \(flagGuard)
    [[ "$(/usr/bin/shasum -a 256 \(quote(source.path)) | /usr/bin/awk '{print $1}')" == \(quote(hash)) ]] || exit 1
    /usr/bin/plutil -lint \(quote(source.path))
    /usr/bin/install -d -o root -g wheel -m 755 \(quote(URL(fileURLWithPath: display.target).deletingLastPathComponent().path))
    /usr/bin/install -o root -g wheel -m 644 \(quote(source.path)) \(quote(display.target))
    /usr/bin/cmp -s \(quote(source.path)) \(quote(display.target))
    \(oldFlag == "1" ? ":" : "/usr/bin/defaults write /Library/Preferences/com.apple.windowserver DisplayResolutionEnabled -bool YES")
    """
    try authorize(script, directory: stage)
    do {
        for screen in displays {
            let reconnected = try native.reconnect(screen)
            try native.enable(reconnected)
            try status(reconnected, native: native)
            try require(verified(reconnected), "屏幕 \(screen.id) 最终核验失败。")
        }
        print("成功。无需 BetterDisplay 常驻。恢复入口：恢复原配置.command")
    } catch {
        print("配置已安装，但激活未完成：\(error)。可运行本工具 reconnect，或使用恢复原配置.command。")
        throw error
    }
}
func restore(_ display: Display, arguments: [String], native: Native) throws {
    try require(try onlineDisplays().contains { CGDisplayIsBuiltin($0) != 0 && CGDisplayIsActive($0) != 0 }, "恢复前请先打开 MacBook 内屏，系统配置尚未修改。")
    let folder = stateDirectory(display), metadata = folder.appendingPathComponent("state.json"), original = folder.appendingPathComponent("original.plist")
    var backup = try JSONDecoder().decode(Backup.self, from: Data(contentsOf: metadata))
    try require(backup.target == display.target && backup.vendor == display.vendor && backup.product == display.product, "恢复记录与显示器不匹配。")
    if backup.managed == false { print("该型号已经恢复；未修改任何系统设置。"); return }
    let displays = try modelDisplays(display)
    let others = try otherManagedBackups(display)
    let modes = try recoveryModes(displays, backup: backup)
    let current = try installedContent(display)
    let currentHash = current.map(digest)
    try require(currentHash == backup.installedHash || currentHash == backup.originalHash, "系统覆盖文件已被其他工具更改，停止自动恢复。")
    let oldFlag = try flag(), targetFlag = try restoredFlag(current: oldFlag, baseline: backup.originalFlag, others: others.map(\.originalFlag))
    try confirm(arguments, "将恢复型号 \(display.model) 的覆盖文件，并逐屏重连当前 \(displays.count) 块同型号屏幕、恢复各自原模式。HiDPI 可能消失；窗口可能移动。其他型号仍受管理时保留全局开关，最后一个型号恢复时还原共享开关基准。")
    let stage = try makeStage(); var fileAction: String
    if currentHash == backup.originalHash { fileAction = ":" }
    else if backup.originalExists {
        let bytes = try Data(contentsOf: original); try require(digest(bytes) == backup.originalHash, "原文件备份校验失败。")
        let source = stage.appendingPathComponent("original.plist"); try bytes.write(to: source)
        fileAction = "/usr/bin/install -o root -g wheel -m 644 \(quote(source.path)) \(quote(display.target))"
    } else { fileAction = "/bin/rm \(quote(display.target))" }
    let flagAction: String
    switch targetFlag { case let value where value == oldFlag: flagAction = ":"; case "1": flagAction = ":"; case "0": flagAction = "/usr/bin/defaults write /Library/Preferences/com.apple.windowserver DisplayResolutionEnabled -bool NO"; default: flagAction = "/usr/bin/defaults delete /Library/Preferences/com.apple.windowserver DisplayResolutionEnabled" }
    let flagGuard = "value=$(/usr/bin/defaults read /Library/Preferences/com.apple.windowserver DisplayResolutionEnabled 2>/dev/null || true)\n[[ \"$value\" == \(quote(oldFlag ?? "")) ]] || { echo '显示开关已变化，停止。' >&2; exit 1; }"
    let script = "set -euo pipefail\n" + guardHash(display.target, expected: currentHash) + "\n" + flagGuard + "\n" + fileAction + "\n" + flagAction
    try authorize(script, directory: stage)
    for screen in displays {
        let result = try native.reconnect(screen)
        if let saved = modes.first(where: { $0.0.id == screen.id })?.1 { try native.applyMode(result, saved: saved) }
        try status(result, native: native)
    }
    backup.managed = false
    try JSONEncoder().encode(backup).write(to: metadata, options: .atomic)
    // Keep recovery evidence; subsequent installs may reuse the same original baseline.
    print("已恢复该型号覆盖文件及原模式；全局开关按剩余管理记录处理。恢复记录保留在：\(folder.path)")
}
func main() throws {
    let arguments = Array(CommandLine.arguments.dropFirst()), action = arguments.first ?? "status"
    let allowed = ["status", "list", "plan", "install", "enable", "persist", "reconnect", "restore", "export"]
    try require(allowed.contains(action), "用法：MacHiDPI status|list|plan|install|enable|persist|reconnect|restore|export [--display ID] [--all-resolutions] [--yes]")
    var index = 1
    while index < arguments.count {
        switch arguments[index] {
        case "--yes": index += 1
        case "--all-resolutions": try require(["plan", "install", "export"].contains(action), "--all-resolutions 仅用于 plan、install、export。"); index += 1
        case "--display": try require(index + 1 < arguments.count && UInt32(arguments[index + 1]) != nil, "--display 参数无效。"); index += 2
        default: throw ToolError("未知参数：\(arguments[index])")
        }
    }
    let native = try Native()
    if action == "list" {
        for id in try onlineDisplays() where CGDisplayIsBuiltin(id) == 0 {
            do { try status(Display(id), native: native) }
            catch { print("外接 ID \(id) 不受支持：\(error)") }
        }
        return
    }
    let display = try selectedDisplay(arguments, interactive: ["install", "restore", "status", "reconnect", "enable", "persist"].contains(action) && isatty(STDIN_FILENO) != 0)
    if ["install", "reconnect", "enable", "persist"].contains(action) {
        let (code, model, _) = try run("/usr/sbin/sysctl", ["-n", "machdep.cpu.brand_string"])
        try require(code == 0 && text(model) == "Apple M1 Pro", "本工具目前只验证并允许 Apple M1 Pro；其他芯片请勿直接使用。")
    }
    switch action {
    case "status": try status(display, native: native)
    case "plan":
        let data = try configuration(for: display, arguments: arguments), object = try PropertyListSerialization.propertyList(from: data, format: nil) as! [String: Any]
        let sizes = try configurationSizes(for: display, arguments: arguments)
        let affected = try modelDisplays(display)
        print("型号级配置将影响当前 \(affected.count) 块同型号屏幕；install、restore 逐屏处理，其他模式操作仅处理选中的屏幕。")
        print("拟新增的 HiDPI 桌面档位（\(sizes.count) 档）：\(sizes.map { "\($0.width)×\($0.height)" }.joined(separator: "、"))\n实际可选档位以安装后系统枚举为准；系统原有档位仍可能保留。")
        print("目标：\(display.target)\n原生桌面：\(display.nativeWidth)×\(display.nativeHeight)，渲染：\(display.nativeWidth * 2)×\(display.nativeHeight * 2)，约 \(display.refresh) Hz\n生成条目：\((object["scale-resolutions"] as! [Data]).count)\nSHA256：\(digest(data))\n现有覆盖文件：\(FileManager.default.fileExists(atPath: display.target) ? "有，将保留备份" : "无，将新建")\n只读计划，未修改。")
    case "export": FileHandle.standardOutput.write(try configuration(for: display, arguments: arguments))
    case "install": try install(display, arguments: arguments, native: native)
    case "enable": try confirm(arguments, "将切换外屏到原生尺寸 HiDPI，可能短暂黑屏。"); try native.enable(display); try status(display, native: native)
    case "persist": try native.persist(display, arguments: arguments); try status(display, native: native)
    case "reconnect": try confirm(arguments, "将软件断开并重连外屏，再启用 HiDPI。短暂黑屏，窗口可能移动。"); let result = try native.reconnect(display); try native.enable(result); try status(result, native: native)
    case "restore": try restore(display, arguments: arguments, native: native)
    default: break
    }
}
do { try main() } catch { FileHandle.standardError.write(Data(("错误：\(error)\n").utf8)); exit(1) }
