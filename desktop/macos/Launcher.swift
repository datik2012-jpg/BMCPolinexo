import AppKit
import CoreFoundation
import Darwin

// A per-login Mach port provides single-instance activation entirely in memory.
private let portName = "il.co.bmc.polinexo.launcher.\(getuid())" as CFString
private func activateExisting() -> Bool {
    guard let remote = CFMessagePortCreateRemote(nil, portName) else { return false }
    return CFMessagePortSendRequest(remote, 1, nil, 2, 0, nil, nil) == kCFMessagePortSuccess
}

final class AppDelegate: NSObject, NSApplicationDelegate {
    var window: NSWindow!
    var status: NSTextField!
    var openButton: NSButton!
    var child: Process?
    var input: Pipe?
    var output: Pipe?
    var port: CFMessagePort?
    var source: CFRunLoopSource?
    var signals: [DispatchSourceSignal] = []
    var startupTimer: Timer?
    var buffer = Data()
    var url: URL?
    var quitting = false
    var failed = false

    func applicationDidFinishLaunching(_ notification: Notification) {
        var context = CFMessagePortContext(version: 0,
            info: Unmanaged.passUnretained(self).toOpaque(), retain: nil,
            release: nil, copyDescription: nil)
        port = CFMessagePortCreateLocal(nil, portName, { _, id, _, info in
            if id == 1, let info = info {
                let delegate = Unmanaged<AppDelegate>.fromOpaque(info).takeUnretainedValue()
                delegate.activate()
            }
            return nil
        }, &context, nil)
        guard let port = port else {
            _ = activateExisting()
            NSApp.terminate(nil)
            return
        }
        source = CFMessagePortCreateRunLoopSource(nil, port, 0)
        CFRunLoopAddSource(CFRunLoopGetMain(), source, .commonModes)
        createWindow()
        for number in [SIGTERM, SIGINT] {
            signal(number, SIG_IGN)
            let handler = DispatchSource.makeSignalSource(signal: number, queue: .main)
            handler.setEventHandler { NSApp.terminate(nil) }
            handler.resume()
            signals.append(handler)
        }
        startBackend()
    }

    func createWindow() {
        let menu = NSMenu()
        let item = NSMenuItem()
        menu.addItem(item)
        let appMenu = NSMenu()
        appMenu.addItem(withTitle: "יציאה מ־BMCPolinexo",
                        action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q")
        item.submenu = appMenu
        NSApp.mainMenu = menu

        window = NSWindow(contentRect: NSRect(x: 0, y: 0, width: 520, height: 230),
            styleMask: [.titled, .closable, .miniaturizable], backing: .buffered, defer: false)
        window.title = "BMCPolinexo"
        window.isReleasedWhenClosed = false
        window.center()
        let title = NSTextField(labelWithString: "BMCPolinexo")
        title.font = .boldSystemFont(ofSize: 25)
        title.alignment = .center
        title.frame = NSRect(x: 20, y: 175, width: 480, height: 35)
        status = NSTextField(wrappingLabelWithString: "היישום נפתח, נא להמתין…")
        status.alignment = .center
        status.baseWritingDirection = .rightToLeft
        status.frame = NSRect(x: 25, y: 97, width: 470, height: 67)
        status.font = .systemFont(ofSize: 15)
        openButton = NSButton(title: "פתיחת היישום", target: self, action: #selector(openApp))
        openButton.bezelStyle = .rounded
        openButton.frame = NSRect(x: 277, y: 42, width: 190, height: 35)
        openButton.isEnabled = false
        let quit = NSButton(title: "סגירת היישום", target: NSApp,
                            action: #selector(NSApplication.terminate(_:)))
        quit.bezelStyle = .rounded
        quit.frame = NSRect(x: 53, y: 42, width: 190, height: 35)
        for view in [title, status!, openButton!, quit] as [NSView] {
            window.contentView?.addSubview(view)
        }
        window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
    }

    func startBackend() {
        guard let resources = Bundle.main.resourceURL else { showFailure(); return }
        let process = Process()
        let stdinPipe = Pipe(), stdoutPipe = Pipe()
        input = stdinPipe
        output = stdoutPipe
        process.executableURL = resources.appendingPathComponent("backend/BMCPolinexoServer")
        process.standardInput = stdinPipe
        process.standardOutput = stdoutPipe
        process.standardError = FileHandle.nullDevice
        var environment = ProcessInfo.processInfo.environment
        for key in ["PYTHONHOME", "PYTHONPATH", "VIRTUAL_ENV"] { environment.removeValue(forKey: key) }
        process.environment = environment
        stdoutPipe.fileHandleForReading.readabilityHandler = { [weak self] handle in
            let data = handle.availableData
            DispatchQueue.main.async { self?.receive(data) }
        }
        process.terminationHandler = { [weak self] _ in
            DispatchQueue.main.async {
                guard let self = self else { return }
                if self.quitting { NSApp.reply(toApplicationShouldTerminate: true) }
                else { self.showFailure() }
            }
        }
        child = process
        do {
            try process.run()
            // Close the parent's duplicate ends; only its writer keeps the
            // child alive, and only the child's stdout writer owns its output.
            try? stdinPipe.fileHandleForReading.close()
            try? stdoutPipe.fileHandleForWriting.close()
            startupTimer = Timer.scheduledTimer(withTimeInterval: 30, repeats: false) { [weak self] _ in
                self?.showFailure()
            }
        } catch { showFailure() }
    }

    func receive(_ data: Data) {
        guard !quitting, !failed, url == nil else { return }
        if data.isEmpty { showFailure(); return }
        buffer.append(data)
        guard buffer.count <= 4096 else { showFailure(); return }
        guard let newline = buffer.firstIndex(of: 10) else { return }
        guard let record = try? JSONSerialization.jsonObject(with: buffer.prefix(upTo: newline)) as? [String: String],
              let value = record["url"], let candidate = URL(string: value),
              candidate.scheme == "http", candidate.host == "127.0.0.1",
              candidate.user == nil, candidate.password == nil,
              let port = candidate.port, (1...65535).contains(port),
              candidate.path.isEmpty, candidate.query == nil, candidate.fragment == nil,
              record["instance_id"]?.isEmpty == false else { showFailure(); return }
        url = candidate
        buffer.removeAll()
        startupTimer?.invalidate()
        status.stringValue = "היישום פועל בדפדפן.\nיש להשאיר חלון זה פתוח בזמן העבודה.\nסגירת היישום מנקה את הנתונים הזמניים."
        openButton.isEnabled = true
        openApp()
    }

    @objc func openApp() {
        if let url = url, !quitting, !failed,
           ProcessInfo.processInfo.environment["BMC_TEST_NO_BROWSER"] != "1" {
            NSWorkspace.shared.open(url)
        }
    }

    func activate() {
        guard !quitting else { return }
        window?.deminiaturize(nil)
        window?.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
        openApp()
    }

    func showFailure() {
        guard !quitting, !failed else { return }
        failed = true
        startupTimer?.invalidate()
        openButton?.isEnabled = false
        status?.stringValue = "לא ניתן להפעיל את היישום.\nיש לסגור אותו ולפתוח מחדש מתוך Applications."
        try? input?.fileHandleForWriting.close()
        // Keep the native failure message visible, but never an orphan server.
        let process = child
        DispatchQueue.main.asyncAfter(deadline: .now() + 6) {
            if let process = process, process.isRunning { process.terminate() }
        }
    }

    func applicationShouldHandleReopen(_ sender: NSApplication, hasVisibleWindows flag: Bool) -> Bool {
        activate()
        return true
    }

    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool { true }

    func applicationShouldTerminate(_ sender: NSApplication) -> NSApplication.TerminateReply {
        if quitting { return .terminateLater }
        quitting = true
        startupTimer?.invalidate()
        if let port = port { CFMessagePortInvalidate(port) }
        if let source = source { CFRunLoopRemoveSource(CFRunLoopGetMain(), source, .commonModes) }
        output?.fileHandleForReading.readabilityHandler = nil
        try? input?.fileHandleForWriting.close()
        guard let process = child, process.isRunning else { return .terminateNow }
        DispatchQueue.main.asyncAfter(deadline: .now() + 6) {
            if process.isRunning { process.terminate() }
        }
        DispatchQueue.main.asyncAfter(deadline: .now() + 8) {
            if process.isRunning { kill(process.processIdentifier, SIGKILL) }
            NSApp.reply(toApplicationShouldTerminate: true)
        }
        return .terminateLater
    }
}

if activateExisting() { exit(0) }
let application = NSApplication.shared
let delegate = AppDelegate()
application.delegate = delegate
application.setActivationPolicy(.regular)
application.run()
