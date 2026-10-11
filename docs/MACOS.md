# macOS installer

Verified build: [download the installer ZIP](https://github.com/datik2012-jpg/BMCPolinexo/actions/runs/38155400652/artifacts/11708487085)
(GitHub sign-in may be required; available through 2026-11-10). Extract the ZIP to
get the DMG. A permanent local copy is in `dist/releases/1.2.2-macos-arm64/`.
The build passed on macOS 15.7.9 arm64; checksums and details are in
[STATUS.md](../STATUS.md).

## Target and installation

BMCPolinexo 1.2.2 targets **Apple silicon (arm64), macOS 15 or newer**. This includes
MacBook Pro M4 with 16 GB RAM. The application does not require Rosetta, Docker,
Python, Node.js or an Apple Developer account on the employee's Mac.
Intel Macs are not included in this package.

1. Download `BMCPolinexo-1.2.2-macos-arm64.dmg` onto the Mac. It can be sent as a
   WhatsApp **document** and downloaded using WhatsApp on the Mac.
2. Open the DMG and drag **BMCPolinexo.app** onto **Applications**.
3. Eject the mounted disk, then open BMCPolinexo from Applications.
4. The native Hebrew launcher opens the app in the default browser. Leave the
   launcher open while working. **פתיחת היישום** reopens the browser.
5. **סגירת היישום**, the window close button, or Command-Q exits the launcher and
   stops its local API. Open portfolios clear when their next health check fails.
   Browser refresh also clears the workspace. Downloaded Excel files remain.

This pilot uses **ad-hoc code signing**, without Developer ID or notarization.
If macOS blocks it, first attempt opening it, then use **System Settings → Privacy
& Security → Open Anyway** and confirm **Open**, only for the expected trusted
build. An organization-managed Mac may restrict this override. Do not disable
Gatekeeper. [Apple's explanation](https://support.apple.com/en-us/102445).
An App Store listing is not required for direct distribution. Developer ID signing
and Apple notarization can be added later with the owner's Apple account.

To upgrade, quit the app, copy the newer app into Applications and choose Replace.
To uninstall, quit and move BMCPolinexo.app to Trash. Exported spreadsheets are
independent files and are not removed by either action.

## Local-only behavior

The frozen backend binds only `127.0.0.1` on a dynamically allocated port and
serves both the built UI and API. The native launcher receives a short readiness
message over an anonymous pipe, never a port file. A per-login macOS Mach port
activates the existing launcher on repeated starts. No customer content crosses
that activation channel. The backend watches stdin: normal quit or unexpected
launcher death closes the pipe and stops the backend, including during startup.
Normal termination gives the child a bounded shutdown interval before forcing
termination; it does not depend on a nested AppKit event loop to finish quitting.

No uploaded workbook, customer data, application log, or coordination state is
persisted. No database, browser storage or service worker is added. The installed
bundle stays unchanged during use. Operating-system swap/crash handling remains
outside the memory-only application guarantee, as with the Docker pilot.

## Building

Build on an Apple-silicon Mac with macOS 15+, Python 3.12, Node.js 22 and Xcode
Command Line Tools. PyInstaller builds for the host OS; Windows cannot build this
Mac runtime. From a full Git checkout:

```sh
python3.12 packaging/macos/build.py
```

The script creates an isolated `.build-venv-macos`, installs pinned build/runtime
dependencies, builds the frontend, audits explicit frontend/backend asset manifests,
freezes the backend, compiles the native Swift launcher, signs the complete app
ad-hoc, verifies both executable architectures and the signature, and builds a DMG.
Only the explicit owned output directories `build/macos`, `dist/macos`, and
`dist/releases/1.2.2-macos-arm64` are replaced on subsequent builds.

Output includes the DMG, `SHA256SUMS.txt`, installation notes and `build-info.json`
(source commit, OS, architecture and checksum). The installer never contains
source workbooks, synthetic fixtures, test screenshots or a repository checkout.
The Git-history audit rejects committed Excel files before packaging.

[The macOS workflow](../.github/workflows/macos-installer.yml) runs on GitHub's
`macos-15` ARM64 runner on relevant pushes to `feature/mac-installer`, or manually
using **Actions → macOS installer → Run workflow**. It uploads the installer only
after all checks pass. Actions artifacts expire after 30 days, so keep a local
copy of a verified release. No release credentials or signing secrets are used.

## Verification

```sh
python3.12 -m venv .test-venv
.test-venv/bin/python -m pip install -r tests/requirements.txt
.test-venv/bin/python -m playwright install chromium
(cd backend && ../.test-venv/bin/python -m pytest -q)
(cd frontend && npm test)
.test-venv/bin/python tests/macos_package_check.py
```

The package test mounts the DMG read-only, copies its app into a temporary folder
with Hebrew and spaces in its name, ejects the DMG and verifies the installed
signature. It starts with a system-only PATH and invalid inherited Python settings
to prove the packaged runtime is self-contained. It checks repeated launches,
all seven synthetic browser workflows (including the merged meeting-summary
export area), normal quit, restart clearing and forced launcher-death cleanup.
It checks that the app files remain unchanged and replacement/removal preserve
an unrelated file. Test output is included in `TEST-RESULTS.txt` for passing builds.

The automated browser checks use Chromium. Physical M4 operation, default-browser
opening in Safari, drag-and-drop Finder interaction and first-launch Gatekeeper
approval still require acceptance on the employee's Mac. No screenshot of client
data is needed. Current build evidence is recorded in [STATUS.md](../STATUS.md).
