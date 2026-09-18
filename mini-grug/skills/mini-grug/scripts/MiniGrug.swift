// MiniGrug.swift — a small always-on-top pixel grug that shows what Claude Code sessions are doing.
//
// Build:   swiftc -O -framework Cocoa MiniGrug.swift -o MiniGrug
// Run:     MiniGrug                      (reads ~/.mini-grug/state/*.json twice a second)
//          MiniGrug --preview out.png    (renders every frame to a PNG and exits)
//
// State files are written by mini-grug.sh, one per Claude Code session:
//   {"state":"working|waiting|done","message":"...","cwd":"/path","term":"iTerm.app","updated":1700000000}
// The window shows the most urgent state across all sessions: waiting > working > done > (none: asleep).
// Click the grug to bring the terminal forward. Drag to move. Right-click for a menu.

import Cocoa

// MARK: - sprite art (single source of truth; the palette letters are stable, the art can change)

let PX: CGFloat = 6                      // screen pixels per sprite pixel
let palette: [Character: NSColor] = [
    "s": NSColor(srgbRed: 0.93, green: 0.78, blue: 0.62, alpha: 1),   // skin
    "h": NSColor(srgbRed: 0.31, green: 0.19, blue: 0.10, alpha: 1),   // hair
    "e": NSColor(srgbRed: 0.10, green: 0.08, blue: 0.08, alpha: 1),   // eye / brow
    "m": NSColor(srgbRed: 0.55, green: 0.25, blue: 0.22, alpha: 1),   // mouth
    "f": NSColor(srgbRed: 0.82, green: 0.52, blue: 0.20, alpha: 1),   // fur tunic
    "d": NSColor(srgbRed: 0.45, green: 0.26, blue: 0.10, alpha: 1),   // tunic spots
    "c": NSColor(srgbRed: 0.55, green: 0.38, blue: 0.20, alpha: 1),   // club
    "k": NSColor(srgbRed: 0.12, green: 0.10, blue: 0.10, alpha: 1),   // feet
    "z": NSColor(srgbRed: 0.55, green: 0.60, blue: 0.75, alpha: 1),   // zzz
    "b": NSColor(srgbRed: 0.92, green: 0.60, blue: 0.62, alpha: 1),   // blush
]
let outlineColor = NSColor(srgbRed: 0.09, green: 0.07, blue: 0.07, alpha: 1)

// 18 columns x 22 rows. '.' is transparent.
let idleA = [
    "..................",
    ".....hhhhhhhh.....",
    "...hhhhhhhhhhhh...",
    "..hhhhhhhhhhhhhh..",
    "..hhsssssssssshh..",
    "..hsssssssssssssh.",
    "..hsseesssssees...",
    "..hsseesssssees...",
    "..hbbsssssssssbb..",
    "..hsssssmmmsssss..",
    "...ssssssssssss...",
    ".....ffffffff.....",
    "...ssffdffffdffss.",
    "...sfffffffffffs..",
    ".....ffdffffdff...",
    ".....ffffffffff...",
    ".....ffffffffff...",
    "......ss....ss....",
    "......ss....ss....",
    ".....kkk....kkk...",
    "..................",
    "..................",
]
// idle B: small bob — same body one row lower (breathing)
let idleB = [
    "..................",
    "..................",
    ".....hhhhhhhh.....",
    "...hhhhhhhhhhhh...",
    "..hhhhhhhhhhhhhh..",
    "..hhsssssssssshh..",
    "..hsssssssssssssh.",
    "..hsseesssssees...",
    "..hsseesssssees...",
    "..hbbsssssssssbb..",
    "..hsssssmmmsssss..",
    "...ssssssssssss...",
    ".....ffffffff.....",
    "...ssffdffffdffss.",
    "...sfffffffffffs..",
    ".....ffdffffdff...",
    ".....ffffffffff...",
    "......ss....ss....",
    "......ss....ss....",
    ".....kkk....kkk...",
    "..................",
    "..................",
]
// wave A/B: right arm up holding the club
let waveA = [
    "...............ccc",
    "...............ccc",
    ".....hhhhhhhh...c.",
    "...hhhhhhhhhhhh.c.",
    "..hhhhhhhhhhhhhhc.",
    "..hhsssssssssshhc.",
    "..hsssssssssssshc.",
    "..hsseesssssees.c.",
    "..hsseesssssees.s.",
    "..hbbsssssssssbbs.",
    "..hsssssmmmmssss.s",
    "...ssssssssssss.ss",
    ".....ffffffff.ss..",
    "...ssffdffffdfffs.",
    "...sfffffffffff...",
    ".....ffdffffdff...",
    ".....ffffffffff...",
    ".....ffffffffff...",
    "......ss....ss....",
    "......ss....ss....",
    ".....kkk....kkk...",
    "..................",
]
let waveB = [
    "..................",
    "..................",
    ".....hhhhhhhh.....",
    "...hhhhhhhhhhhh...",
    "..hhhhhhhhhhhhhh..",
    "..hhsssssssssshh..",
    "..hsssssssssssssh.",
    "..hsseesssssees...",
    "..hsseesssssees...",
    "..hbbsssssssssbb..",
    "..hsssssmmmmssss..",
    "...ssssssssssss...",
    ".....ffffffff..ccc",
    "...ssffdffffdfsscc",
    "...sfffffffffff.c.",
    ".....ffdffffdff...",
    ".....ffffffffff...",
    ".....ffffffffff...",
    "......ss....ss....",
    "......ss....ss....",
    ".....kkk....kkk...",
    "..................",
]
// asleep: eyes closed, zzz
let sleep = [
    "..............z...",
    ".....hhhhhhhh..zz.",
    "...hhhhhhhhhhhh.z.",
    "..hhhhhhhhhhhhhh..",
    "..hhsssssssssshh..",
    "..hsssssssssssssh.",
    "..hsssssssssssssh.",
    "..hsseesssssees...",
    "..hbbsssssssssbb..",
    "..hssssssmmssssss.",
    "...ssssssssssss...",
    ".....ffffffff.....",
    "...ssffdffffdffss.",
    "...sfffffffffffs..",
    ".....ffdffffdff...",
    ".....ffffffffff...",
    ".....ffffffffff...",
    "......ss....ss....",
    "......ss....ss....",
    ".....kkk....kkk...",
    "..................",
    "..................",
]
// done: happy, wide mouth
let done = [
    "..................",
    ".....hhhhhhhh.....",
    "...hhhhhhhhhhhh...",
    "..hhhhhhhhhhhhhh..",
    "..hhsssssssssshh..",
    "..hsssssssssssssh.",
    "..hsseesssssees...",
    "..hsesssesssesse..",
    "..hbbsssssssssbb..",
    "..hssssmmmmmsssss.",
    "...sssssmmmssssss.",
    ".....ffffffff.....",
    "...ssffdffffdffss.",
    "...sfffffffffffs..",
    ".....ffdffffdff...",
    ".....ffffffffff...",
    ".....ffffffffff...",
    "......ss....ss....",
    "......ss....ss....",
    ".....kkk....kkk...",
    "..................",
    "..................",
]

enum Mood { case asleep, working, waiting, done }

func frames(for mood: Mood) -> [[String]] {
    switch mood {
    case .asleep: return [sleep]
    case .working: return [idleA, idleB]
    case .waiting: return [waveA, waveB]
    case .done: return [done, idleA]
    }
}
func frameInterval(for mood: Mood) -> TimeInterval {
    switch mood {
    case .waiting: return 0.35
    case .done: return 0.6
    default: return 1.1
    }
}

let COLS = 18, ROWS = 22
let spriteSize = NSSize(width: CGFloat(COLS) * PX, height: CGFloat(ROWS) * PX)

/// Every frame must be exactly ROWS x COLS. Exits with a clear message instead of drawing garbage after an art edit.
func checkFrames() {
    for (name, grid) in [("idleA", idleA), ("idleB", idleB), ("waveA", waveA), ("waveB", waveB), ("done", done), ("sleep", sleep)] {
        if grid.count != ROWS { FileHandle.standardError.write("frame \(name): \(grid.count) rows, want \(ROWS)\n".data(using: .utf8)!); exit(3) }
        for (i, row) in grid.enumerated() where row.count != COLS {
            FileHandle.standardError.write("frame \(name) row \(i): \(row.count) cols, want \(COLS)\n".data(using: .utf8)!); exit(3)
        }
    }
}

func drawSprite(_ grid: [String], at origin: NSPoint) {
    func at(_ r: Int, _ c: Int) -> Character? {
        guard r >= 0, r < ROWS, c >= 0, c < COLS else { return nil }
        let row = Array(grid[r]); return c < row.count ? row[c] : nil
    }
    func solid(_ r: Int, _ c: Int) -> Bool { if let ch = at(r, c) { return ch != "." } else { return false } }
    // outline: any transparent pixel that touches a solid one (4-neighbour) becomes outline
    for r in 0..<ROWS { for c in 0..<COLS {
        let ch = at(r, c) ?? "."
        var color: NSColor? = palette[ch]
        if ch == "." && (solid(r-1,c) || solid(r+1,c) || solid(r,c-1) || solid(r,c+1)) { color = outlineColor }
        guard let col = color else { continue }
        col.setFill()
        // row 0 is the top of the art; AppKit y grows upward
        let y = origin.y + CGFloat(ROWS - 1 - r) * PX
        NSBezierPath(rect: NSRect(x: origin.x + CGFloat(c) * PX, y: y, width: PX, height: PX)).fill()
    }}
}

// MARK: - state files

struct SessionState {
    let id: String; let state: String; let message: String; let cwd: String; let term: String; let updated: TimeInterval
}

let stateDir: URL = {
    if let env = ProcessInfo.processInfo.environment["MINI_GRUG_DIR"], !env.isEmpty { return URL(fileURLWithPath: env).appendingPathComponent("state") }
    return FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent(".mini-grug/state")
}()

func readSessions() -> [SessionState] {
    guard let files = try? FileManager.default.contentsOfDirectory(at: stateDir, includingPropertiesForKeys: nil) else { return [] }
    let cutoff = Date().timeIntervalSince1970 - 12 * 3600
    var out: [SessionState] = []
    for f in files where f.pathExtension == "json" {
        guard let data = try? Data(contentsOf: f),
              let obj = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else { continue }
        let updated = (obj["updated"] as? Double) ?? 0
        if updated < cutoff { continue }
        out.append(SessionState(id: f.deletingPathExtension().lastPathComponent,
                                state: (obj["state"] as? String) ?? "working",
                                message: (obj["message"] as? String) ?? "",
                                cwd: (obj["cwd"] as? String) ?? "",
                                term: (obj["term"] as? String) ?? "",
                                updated: updated))
    }
    return out
}

struct Summary { let mood: Mood; let bubble: String?; let count: Int; let term: String; let stamp: String }

func summarize(_ sessions: [SessionState]) -> Summary {
    let waiting = sessions.filter { $0.state == "waiting" }.sorted { $0.updated > $1.updated }
    let working = sessions.filter { $0.state == "working" }
    let done = sessions.filter { $0.state == "done" }.sorted { $0.updated > $1.updated }
    let stamp = sessions.map { "\($0.id):\($0.state):\(Int($0.updated))" }.sorted().joined(separator: "|")
    func place(_ s: SessionState) -> String { s.cwd.isEmpty ? "" : " · " + URL(fileURLWithPath: s.cwd).lastPathComponent }
    if let w = waiting.first {
        let more = waiting.count > 1 ? " (+\(waiting.count - 1) more)" : ""
        let msg = w.message.isEmpty ? "grug need chief" : w.message
        return Summary(mood: .waiting, bubble: msg + place(w) + more, count: waiting.count, term: w.term, stamp: stamp)
    }
    if !working.isEmpty {
        return Summary(mood: .working, bubble: nil, count: working.count, term: working.first!.term, stamp: stamp)
    }
    if let d = done.first, Date().timeIntervalSince1970 - d.updated < 45 {
        let msg = d.message.isEmpty ? "grug done" : d.message
        return Summary(mood: .done, bubble: msg + place(d), count: done.count, term: d.term, stamp: stamp)
    }
    return Summary(mood: .asleep, bubble: nil, count: 0, term: done.first?.term ?? "", stamp: stamp)
}

// MARK: - views

func log(_ msg: String) {
    let ts = ISO8601DateFormatter().string(from: Date())
    FileHandle.standardError.write("\(ts) \(msg)\n".data(using: .utf8)!)
}

final class GrugView: NSView {
    var mood: Mood = .asleep { didSet { if mood != oldValue { frameIndex = 0; restartTimer() } } }
    var bubble: String? { didSet { if bubble != oldValue { needsDisplay = true } } }
    var count = 0
    var onClick: (() -> Void)?
    private var frameIndex = 0
    private var timer: Timer?

    override init(frame: NSRect) { super.init(frame: frame); restartTimer() }
    required init?(coder: NSCoder) { fatalError() }

    func restartTimer() {
        timer?.invalidate()
        timer = Timer.scheduledTimer(withTimeInterval: frameInterval(for: mood), repeats: true) { [weak self] _ in
            guard let self = self else { return }
            self.frameIndex = (self.frameIndex + 1) % frames(for: self.mood).count
            self.needsDisplay = true
        }
        needsDisplay = true
    }

    override func draw(_ dirtyRect: NSRect) {
        let f = frames(for: mood)[min(frameIndex, frames(for: mood).count - 1)]
        let spriteOrigin = NSPoint(x: (bounds.width - spriteSize.width) / 2, y: 6)
        drawSprite(f, at: spriteOrigin)
        if count > 1 {
            let badge = NSRect(x: spriteOrigin.x + spriteSize.width - 26, y: spriteOrigin.y + spriteSize.height - 40, width: 22, height: 18)
            NSColor(srgbRed: 0.85, green: 0.30, blue: 0.20, alpha: 1).setFill()
            NSBezierPath(roundedRect: badge, xRadius: 9, yRadius: 9).fill()
            draw(text: "\(count)", in: badge, size: 11, color: .white, bold: true)
        }
        guard let text = bubble, !text.isEmpty else { return }
        let attrs: [NSAttributedString.Key: Any] = [.font: NSFont.systemFont(ofSize: 12, weight: .medium)]
        let maxW = bounds.width - 16
        let measured = (text as NSString).boundingRect(with: NSSize(width: maxW - 20, height: 200), options: [.usesLineFragmentOrigin], attributes: attrs)
        let w = min(maxW, ceil(measured.width) + 20), h = ceil(measured.height) + 14
        let rect = NSRect(x: (bounds.width - w) / 2, y: spriteOrigin.y + spriteSize.height - 4, width: w, height: h)
        NSColor(srgbRed: 0.12, green: 0.11, blue: 0.11, alpha: 0.96).setFill()
        let path = NSBezierPath(roundedRect: rect, xRadius: 8, yRadius: 8)
        path.move(to: NSPoint(x: rect.midX - 6, y: rect.minY))
        path.line(to: NSPoint(x: rect.midX, y: rect.minY - 7))
        path.line(to: NSPoint(x: rect.midX + 6, y: rect.minY))
        path.close()
        path.fill()
        let textRect = rect.insetBy(dx: 10, dy: 7)
        (text as NSString).draw(with: textRect, options: [.usesLineFragmentOrigin], attributes: attrs.merging([.foregroundColor: NSColor.white]) { $1 })
    }

    private func draw(text: String, in rect: NSRect, size: CGFloat, color: NSColor, bold: Bool) {
        let p = NSMutableParagraphStyle(); p.alignment = .center
        let a: [NSAttributedString.Key: Any] = [.font: bold ? NSFont.boldSystemFont(ofSize: size) : NSFont.systemFont(ofSize: size), .foregroundColor: color, .paragraphStyle: p]
        let h = (text as NSString).size(withAttributes: a).height
        (text as NSString).draw(in: NSRect(x: rect.minX, y: rect.midY - h / 2, width: rect.width, height: h), withAttributes: a)
    }

    // click = activate terminal; a drag must still move the window.
    // The app is an accessory that is never active, so the first click must reach the view directly.
    override func acceptsFirstMouse(for event: NSEvent?) -> Bool { true }
    private var downAt = NSPoint.zero
    private var dragged = false
    override func mouseDown(with event: NSEvent) { downAt = event.locationInWindow; dragged = false }
    override func mouseDragged(with event: NSEvent) {
        let d = hypot(event.locationInWindow.x - downAt.x, event.locationInWindow.y - downAt.y)
        if d >= 4 { dragged = true; window?.performDrag(with: event) }
    }
    override func mouseUp(with event: NSEvent) {
        if !dragged { onClick?() }
    }
    override func rightMouseDown(with event: NSEvent) {
        let menu = NSMenu()
        menu.addItem(withTitle: "Mini grug · \(stateDir.deletingLastPathComponent().path)", action: nil, keyEquivalent: "")
        menu.addItem(.separator())
        menu.addItem(withTitle: "Reset position", action: #selector(AppDelegate.resetPosition), keyEquivalent: "")
        menu.addItem(withTitle: "Quit mini grug", action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q")
        NSMenu.popUpContextMenu(menu, with: event, for: self)
    }
}

final class AppDelegate: NSObject, NSApplicationDelegate {
    var window: NSWindow!
    var view: GrugView!
    var lastStamp = ""
    var lastTerm = ""
    /// Waiting sessions the user clicked away: id -> the `updated` stamp that was acknowledged.
    /// A new hook event writes a new stamp, so the same session waves again the next time it waits.
    var acked: [String: TimeInterval] = [:]
    let posKey = "miniGrugOrigin"

    func applicationDidFinishLaunching(_ notification: Notification) {
        let size = NSSize(width: 240, height: spriteSize.height + 70)
        view = GrugView(frame: NSRect(origin: .zero, size: size))
        view.onClick = { [weak self] in self?.clicked() }
        window = NSWindow(contentRect: NSRect(origin: .zero, size: size), styleMask: [.borderless], backing: .buffered, defer: false)
        window.isOpaque = false
        window.backgroundColor = .clear
        window.hasShadow = false
        window.level = .floating
        window.collectionBehavior = [.canJoinAllSpaces, .stationary, .fullScreenAuxiliary]
        window.isMovableByWindowBackground = false  // GrugView drags by hand so a click is not eaten by the drag loop
        window.contentView = view
        window.ignoresMouseEvents = false
        restorePosition()
        window.orderFrontRegardless()
        Timer.scheduledTimer(withTimeInterval: 0.5, repeats: true) { [weak self] _ in self?.tick() }
        NotificationCenter.default.addObserver(forName: NSWindow.didMoveNotification, object: window, queue: nil) { [weak self] _ in
            guard let self = self else { return }
            UserDefaults.standard.set(NSStringFromPoint(self.window.frame.origin), forKey: self.posKey)
        }
        tick()
    }

    func visibleSessions() -> [SessionState] {
        readSessions().filter { !($0.state == "waiting" && acked[$0.id] == $0.updated) }
    }

    func tick() {
        let s = summarize(visibleSessions())
        view.mood = s.mood
        view.bubble = s.bubble
        view.count = s.count
        if !s.term.isEmpty { lastTerm = s.term }
        if s.stamp != lastStamp { lastStamp = s.stamp; view.needsDisplay = true }
    }

    /// Click = acknowledge every current wait (bubble and badge clear) and bring the terminal forward.
    func clicked() {
        let waiting = readSessions().filter { $0.state == "waiting" }
        for w in waiting { acked[w.id] = w.updated }
        if !waiting.isEmpty { log("click: acknowledged \(waiting.count) waiting session(s)") }
        acked = acked.filter { pair in readSessions().contains { $0.id == pair.key } }  // forget sessions that ended
        activateTerminal()
        tick()
    }

    func activateTerminal() {
        // TERM_PROGRAM values seen in the wild → app names `open -a` understands
        let map = ["iTerm.app": "iTerm", "Apple_Terminal": "Terminal", "ghostty": "Ghostty", "WarpTerminal": "Warp",
                   "vscode": "Visual Studio Code", "WezTerm": "WezTerm", "kitty": "kitty", "Alacritty": "Alacritty", "Hyper": "Hyper", "tmux": "Terminal"]
        // Hooks often run without TERM_PROGRAM; then take whichever known terminal is running.
        let bundles = ["com.googlecode.iterm2", "com.apple.Terminal", "com.mitchellh.ghostty", "dev.warp.Warp-Stable",
                       "com.microsoft.VSCode", "com.github.wez.wezterm", "net.kovidgoyal.kitty", "org.alacritty", "co.zeit.hyper"]
        if lastTerm.isEmpty, let running = NSWorkspace.shared.runningApplications.first(where: { bundles.contains($0.bundleIdentifier ?? "") }) {
            log("click: term unknown, activating running \(running.bundleIdentifier ?? "?")")
            running.activate()
            return
        }
        let app = map[lastTerm] ?? (lastTerm.isEmpty ? "Terminal" : lastTerm)
        log("click: open -a \(app) (term=\(lastTerm))")
        let p = Process(); p.executableURL = URL(fileURLWithPath: "/usr/bin/open"); p.arguments = ["-a", app]
        try? p.run()
    }

    @objc func resetPosition() {
        UserDefaults.standard.removeObject(forKey: posKey)
        restorePosition()
    }

    func restorePosition() {
        if let s = UserDefaults.standard.string(forKey: posKey) {
            let o = NSPointFromString(s)
            if NSScreen.screens.contains(where: { $0.frame.insetBy(dx: -50, dy: -50).contains(o) }) { window.setFrameOrigin(o); return }
        }
        guard let screen = NSScreen.main else { return }
        let vf = screen.visibleFrame
        window.setFrameOrigin(NSPoint(x: vf.maxX - window.frame.width - 16, y: vf.minY + 16))
    }
}

// MARK: - preview (renders all frames to one PNG; used by `mini-grug.sh preview`)

func renderPreview(to path: String) {
    let all: [(String, [String])] = [("idleA", idleA), ("idleB", idleB), ("waveA", waveA), ("waveB", waveB), ("done", done), ("sleep", sleep)]
    let pad: CGFloat = 12
    let w = CGFloat(all.count) * (spriteSize.width + pad) + pad, h = spriteSize.height + pad * 2 + 16
    let img = NSImage(size: NSSize(width: w, height: h))
    img.lockFocus()
    NSColor(srgbRed: 0.13, green: 0.13, blue: 0.14, alpha: 1).setFill(); NSBezierPath(rect: NSRect(x: 0, y: 0, width: w, height: h)).fill()
    for (i, (name, grid)) in all.enumerated() {
        let x = pad + CGFloat(i) * (spriteSize.width + pad)
        drawSprite(grid, at: NSPoint(x: x, y: pad + 16))
        (name as NSString).draw(at: NSPoint(x: x, y: 2), withAttributes: [.font: NSFont.monospacedSystemFont(ofSize: 10, weight: .regular), .foregroundColor: NSColor.lightGray])
    }
    img.unlockFocus()
    guard let tiff = img.tiffRepresentation, let rep = NSBitmapImageRep(data: tiff), let png = rep.representation(using: .png, properties: [:]) else { exit(2) }
    try? png.write(to: URL(fileURLWithPath: path))
    print("wrote \(path)")
}

// MARK: - main

let args = CommandLine.arguments
checkFrames()
if args.count >= 3 && args[1] == "--preview" { renderPreview(to: args[2]); exit(0) }
if args.contains("--help") {
    print("MiniGrug [--preview out.png]\n  state dir: \(stateDir.path)"); exit(0)
}
let app = NSApplication.shared
app.setActivationPolicy(.accessory)
let delegate = AppDelegate()
app.delegate = delegate
app.run()
