# Test on a separate Windows PC

Use this checklist on **Windows 10 x64** and **Windows 11 x64**, as a normal
non-admin user. The PC should have no Docker, Python or Node.js installed.

Copy version **1.2.1** of `BMCPolinexo-Setup.exe` and the separately supplied `synthetic-test.xlsx` to
the PC. The workbook contains invented data only and is not inside the installer.

1. Disconnect the internet, install, and open the desktop shortcut. No
   administrator prompt should be needed. A small Hebrew window and the browser
   interface should open. Check that all Hebrew text and both launcher buttons
   are readable, including at your usual Windows display scaling.
2. Enter any fictitious first/last name, ID **999999999**, gender and marital status. Import the
   synthetic workbook. Expect **20 coverages**, **8 policy groups**, monthly
   total **₪763.32**, and separate annual total **₪5,642.00**.
3. In **מצב קיים**, copy a coverage using **העתקה למצב החדש**, then switch to
   **מצב חדש** to edit its premium, exclude/restore it and compare the source.
   Verify the existing baseline remains unchanged. Export Excel and verify both
   states, logos, coverage/person dropdowns and separate monthly/annual totals.
   Add a second synthetic customer and check that **הצגת לקוחות יחד** appears
   compactly immediately after **+ הוסף לקוח נוסף**.
4. Open the shortcut again: the same launcher should be reused. Close the
   browser and reopen it using **פתיחת היישום**. The new page starts empty.
5. Import again, then close the launcher while the browser stays open. The open
   page should clear its customer data within a few seconds (focus the tab if it
   was in the background). Open the app again: it should start empty.
6. Try installing again while the app runs: setup should request that you close
   it. Close the launcher and retry. Check the Start Menu shortcut too.
7. Uninstall from Windows Settings. Shortcuts and application files should be
   removed; your separately saved Excel files should remain.

If possible, repeat installation in a folder containing Hebrew letters and
spaces. Send back the Windows version, which steps passed, and the exact text
of any error. Do not send screenshots containing real customer data.

The pilot installer is unsigned. If company policy blocks it, report the message
to the maintainer/IT; do not change Windows security settings for this test.
