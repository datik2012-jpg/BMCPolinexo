# Insurer logos

Reviewed 2026-09-24. The UI bundles 26 insurer and insurance-brand logos locally, independently of the imported workbook. This is a maintained display catalog, not a certified regulatory register of every licensed entity. Unknown names remain visible without a guessed logo.

`frontend/src/insurers.ts` holds Hebrew/English aliases and legal-name matching. Matching affects only the image, never source values, policy grouping, or totals. Assets are in `frontend/public/insurers`. No client information is sent to logo providers. Trademarks belong to their respective owners and are used for identification.

## Sources

- Menora: https://cdn.menoramivt.co.il/public/images/20230831/1nyh0dllyub0z6-menora_logo_square.png
- Harel: https://media.harel-group.co.il/media/4jmkigev/harel_logo.svg
- Migdal: header SVG extracted from https://www.migdal.co.il/
- Clal: https://www.clalbit.co.il/AngularClient/dist/assets/images/header/logo-eng-heb.svg
- Phoenix: https://www.fnx.co.il/_nuxt/img/header-logo.564c209.png
- Ayalon: https://www.hova.org.il/hovanet-images/logos/ayaR.png (comparison-site mirror)
- Hachshara: https://umbraco-api.hcsra.co.il/media/vi4dtoux/logo.png
- AIG: https://commons.wikimedia.org/wiki/File:AIG_new_logo.svg (public-domain text-logo mirror; trademark retained)
- Direct Insurance: https://www.555.co.il/sites/default/files/logo1.svg
- 9: https://www.9000000.co.il/sites/default/files/9_logo_-01_0_0.png
- Libra: https://www.lbr.co.il/media/1076/libra.svg
- weSure: https://b2b.wesuregroup.com/assets/images/logo.png
- Shlomo: https://www.shlomo-bit.co.il/images/logo_icon.svg
- Shomera: https://www.shomera.co.il/media/rvdgaf0i/logo.png
- Agricultural Insurance: https://www.bth.co.il/wp-content/uploads/2026/05/logo.svg
- DavidShield: https://www.davidshield.co.il/wp-content/uploads/2025/03/logo-95.07_66-Hebrew.svg
- PassportCard: https://www.passportcard.co.il/wp-content/uploads/2023/07/logo.svg
- Shirbit: https://www.shirbit.co.il/Static/new/dist/images/img-logo.png
- Ankor: https://www.nkr.co.il/wp-content/uploads/2024/01/Group-4122.png
- EMI: extracted logo image from page 1 of the 2025 annual report linked at https://www.harel-group.co.il/emi — https://media.harel-group.co.il/media/a3qafgml/דוח-תקופתי-2025.pdf
- BSSCH/ICIC: https://www.icic.co.il/assets/images/logo.svg
- Ashra: https://www.ashra.gov.il/_Pics/logo.png
- Inbal: https://www.fatfish.co.il/sites/default/files/styles/max_325x325/public/2025-10/Inbal_logo%20%281%29.png (website supplier portfolio mirror)
- Kanat: https://www.kanat.co.il/wp-content/uploads/2022/03/logo.svg (nonvisual Adobe foreignObject metadata removed)
- Coface: https://www.coface.co.il/build/default/images/logo/logo_coface.png
- The Pool: https://static.wixstatic.com/media/431371_2bb8150a72654f6ca9a410f7bf3767a9~mv2.png (supplier client portfolio at https://www.sysolve.co.il/)

## Maintenance

Add a verified local image, catalog entry and unambiguous aliases when another name appears. Do not automatically replace historical company names with a successor company. Check `npm test` and `npm run build` in `frontend`, then run `.venv\Scripts\python.exe tests/insurer_logos_check.py` against the running pilot. Browser checks use synthetic data only.
