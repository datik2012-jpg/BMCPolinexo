# Windows package

## Release 1.2.1 — 2026-10-05

One installer supports both Windows 10 and Windows 11 x64. This release merges
`main` at `5d0140a` into `feature/windows-installer`; its tag is `v1.2.1-windows`.
It includes the compact shared-customer selector, existing/proposed coverage
workflow and compact Excel export with coverage/person dropdowns and logos.
The Windows localhost launcher and connection-loss clearing remain enabled.


## Employee installation

Target: Windows 10/11 x64 (Intel/AMD), one local employee session per Windows
user. Each PC is independent. No administrator rights, Docker, Python, Node.js,
database or runtime network connection is required. A browser must be installed.

1. Run the supplied `BMCPolinexo-Setup.exe` as your normal Windows user.
2. Keep the default installation folder under your user profile. The installer
   creates Start Menu and desktop shortcuts and a normal Windows uninstall entry.
3. Open the shortcut. The Hebrew launcher starts the local server and opens the
   interface in your default browser after it is ready.
4. Use **פתיחת היישום** to reopen the browser and **יציאה** to stop the app.
   Closing the launcher also stops it. Closing a browser tab does not stop it.

Customer details, imports and corrections exist only in memory. Refresh clears
them. An open desktop tab also clears them when it loses its launcher connection
(normally within the three-second poll plus request timeout; background browser
tabs may be throttled until focused). A restart can choose a different port:
open the new address from the launcher. The application writes no workbook,
customer settings, request logs, browser storage or port coordination files.
Only explicit Excel exports are downloaded by the browser. Windows/browser
system behavior such as paging or download history is outside the app's control.

Before updating, export anything you need and close the launcher. Run the newer
installer under the same user; it replaces the installed version. Automatic
updates and startup at login are not enabled. Uninstall through Windows Settings.
The installer does not remove Excel files you imported or exported elsewhere.

Pilot builds are unsigned. Organization-managed Windows policy may require a
trusted publisher signature before distribution. A signing certificate is not
included in this repository.

## Build on Windows

Install Python 3.12 x64 (including Tcl/Tk), Node.js 22, Git, and Inno Setup
**6.5.4** on the build machine. These tools are not employee prerequisites.
Build from a full Git clone; release builds should use a clean reviewed checkout.

```powershell
./packaging/windows/build.ps1 -Version 1.2.1
# If Inno Setup is installed elsewhere:
./packaging/windows/build.ps1 -Version 1.2.1 -Iscc 'C:/path/to/ISCC.exe'
```

The script creates `.build-venv`, installs pinned runtime/build dependencies,
runs `npm ci` and builds React, audits the public assets, builds the PyInstaller
folder and compiles the installer. Inno Setup's exact version is checked by the
installer preprocessor. Outputs:

- `dist/windows/BMCPolinexo/`: runnable folder including Python and Tcl/Tk.
- `dist/windows/bundle-manifest.json`: relative file paths and SHA-256 hashes.
- `dist/releases/1.2.1/BMCPolinexo-Setup.exe`: employee installer; the build prints
  its SHA-256 hash. Distribute it through the organization's approved channel.

No repository-wide data glob is used. The backend is collected as Python
modules; Excel export logos and the insurer catalog are explicitly listed in
`packaging/windows/backend-assets.txt` and verified byte-for-byte in the frozen
bundle. Frontend files are limited to generated HTML/JS/CSS and the approved
logo paths in `packaging/windows/public-assets.txt`. Changes to that manifest
require review. Tests, screenshots, workbooks, prompts and build tools are not
included. The folder audit rejects Excel and common source/private artifacts.
The installer includes only that audited folder.

`requirements-build.txt` pins the complete resolved Python environment. Update
it deliberately alongside `backend/requirements.txt` and retest packaging.
Do not use an environment containing unrelated dependencies to make releases.

## Excel audit

```powershell
python packaging/windows/audit_excel.py --remote
```

This checks the Git index, every locally reachable historical filename, current
GitHub branch/tag histories, and ignore coverage for Excel files in source
folders. It does not read workbook contents or delete local files. Missing
remote objects cause failure: fetch the relevant branches/tags, then repeat.
It cannot prove deletion from old GitHub caches, previously deleted remote refs,
forks or someone else's clone. If an Excel path is ever detected, stop release
work and review history cleanup before pushing.

## Acceptance gate

Use only in-memory synthetic workbooks from the existing test fixtures.

```powershell
# Backend and Windows runtime checks (from backend/):
../.venv/Scripts/python -m pytest -q
# Frontend checks (from frontend/):
npm test
```

Against a running packaged app, set `BMC_URL` to its localhost URL and set
`BMC_TEST_DESKTOP=1`, then run the seven browser suites listed in `tests/windows_package_check.py` with the
existing test environment. Those cover imports, grouping, decimal totals,
corrections, exclusions, exports, family/shared views, all logos, RTL/mobile,
refresh, offline clearing and instance changes. Runtime unit tests exercise
actual loopback startup/shutdown and Windows named-object coordination.

The Windows packaged acceptance harness discovers the executable's assigned
port, runs all seven browser suites, tests repeated launches and actual
close/restart/crash clearing, and compares application files before/after:

```powershell
./.venv/Scripts/python tests/windows_package_check.py --exe dist/windows/BMCPolinexo/BMCPolinexo.exe
```

It opens the default browser as a normal launch does, uses a separate Playwright
browser for assertions, and stops only the launcher it created. Do not run it
while working with real customer data in another instance.

`tests/windows_installer_check.py --baseline <older-setup.exe> --installer
<newer-setup.exe> --version <new-version>` additionally tests non-admin setup,
Hebrew paths, both shortcuts, refusal to update/uninstall while running, version
upgrade, removal of obsolete runtime files, installed-file hashes, all packaged
workflows and uninstall cleanup. It refuses to run if the app is already
installed. Run it with the same Python test environment from the repository root.

Before employee rollout, repeat on clean Windows 10 x64 and Windows 11 x64 VMs
with a standard user and no development tools:

1. Install with the network disconnected. Verify both shortcuts, Hebrew setup,
   launcher and browser behavior; confirm no elevation prompt is required.
2. Use a user/install path containing Hebrew and spaces. Run the browser suite
   from a separate test harness or perform its synthetic workflows manually.
3. Launch twice and confirm one server and the same URL. Close the browser and
   reopen it from the launcher. Verify independent Windows users are isolated.
4. Close the launcher with a portfolio open: its browser tab clears, its process
   ends and its port closes. Relaunch: the new session is empty. Repeat after
   terminating the process to simulate a crash.
5. Verify a readable Hebrew error when the packaged web folder is missing and
   successful recovery after restoring it. Test a failed default-browser launch.
6. Try updating/uninstalling while running: the installer must request closure.
   Close the app, update, run the synthetic workflows, then uninstall. Confirm
   shortcuts and installed runtime are removed and unrelated exports remain.
7. Inspect installed files against the bundle manifest. Confirm no private data
   or unexpected runtime files appear after import/edit/export.

Record OS build, user privilege, installer hash and pass/fail results. A build
on a development machine alone does not satisfy this clean-machine gate.

## Verification recorded on 2026-10-05

Installer: **1.2.1**, 19,303,902 bytes, Windows 10/11 x64. SHA-256:
`70448a91fc9800a7199f3a0b6db281c44de84bdc3cb52c4e02d2e2d5de8552f3`.

Passed on Windows 10 build 19045 under a non-elevated user:

- All 32 backend/Windows runtime tests and all 33 frontend tests.
- Node.js 22.23.3 production build, Python 3.12.10/PyInstaller 6.22.0 bundle,
  Inno Setup 6.5.4 installer, and an audit of 1,066 bundled files. All 30 web
  files and 28 explicitly listed Excel export assets are present and verified.
- All seven browser suites against the installed executable: imports/decimal
  totals/corrections, family, shared view, real Excel download, proposal state,
  category filters and 26 insurer logos. Every suite respects the packaged URL.
- Non-admin install into a Hebrew/space path, both shortcuts, repeated launch,
  running-app upgrade/uninstall refusal, actual upgrade from 1.1.0 to 1.2.1,
  obsolete runtime removal, and installed payload hashes matching the manifest.
- Real close/restart/crash clearing, closed listening port, no external app
  requests, unchanged runtime files, and operation without development tools
  on the child process PATH. Uninstall removes the app/shortcuts/registry entry
  while preserving an unrelated file outside the application directory.
- Local and remote Git history/Excel ignore audit. Rebuilt API/web Docker
  services; API healthy and `http://127.0.0.1:8080` returned HTTP 200.

The installer remains unsigned. Clean Windows 10/11 machines without developer
tools, high-DPI launcher appearance and multiple Windows users still require
separate-PC acceptance using [the checklist](WINDOWS-PC-CHECKLIST.md). These
results do not claim Windows 11 execution. The detailed log is ignored at
`test-results/windows-installer-1.2.1-validation.log`.

## Verification recorded on 2026-09-27

Final installer: `1.1.0`, 15,615,228 bytes. SHA-256:
`1b2f2cf6bfecd15ad2577c60ec80bab32ea65700c61f5ea9585f1aea385309b0`.

Passed on Windows 10 build 19045, under a non-elevated user:

- 27 backend/runtime tests and 26 frontend tests.
- Source launcher failure checks using the real Tk event loop and local server:
  generic Hebrew startup errors without exception details, release of the
  single-instance lock after failure, and a ready localhost URL offered when
  browser launch returns false or raises. Server shutdown is checked afterward.
- All six browser suites against the installed executable using synthetic data.
- Hebrew/space installation path, desktop/Start Menu shortcuts, repeated launch,
  running-app upgrade/uninstall guards, upgrade from test version 1.0.99 to 1.1.0,
  removal of obsolete runtime files, and uninstall cleanup.
- Real launcher close/restart/crash clearing, localhost-only binding, closed
  listening port after shutdown, unchanged application files after workflows,
  and successful startup with development tools removed from the child PATH.
- A synthetic import with all non-local browser requests blocked, with no
  external application requests observed.
- 1,029 bundled files audited; installed payload hashes match the manifest.
- No Excel filenames in the index or reachable history, including current
  GitHub branches/tag; all four existing source-area Excel files are ignored.

Still pending: clean Windows 10/11 PCs without installed developer tools,
visually checking the launcher at normal/high DPI, multiple Windows users,
and packaged startup-error/browser-failure recovery. The desktop inspection
helper was unavailable, so automated launcher lifecycle checks do not imply a
visual inspection. The user will run separate-PC tests using
[this checklist](WINDOWS-PC-CHECKLIST.md). Local detailed output is in ignored
`test-results/windows-installer-validation.log`.
