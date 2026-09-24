// Display-only catalog: never use brand aliases to merge source policy groups.
// Asset provenance and maintenance notes: docs/INSURER_LOGOS.md.
export type InsurerBrand = {
  id: string;
  name: string;
  logo: string;
  aliases: string[];
};

function brand(id: string, name: string, file: string, aliases: string[]): InsurerBrand {
  return { id, name, logo: `/insurers/${file}`, aliases: [name, ...aliases] };
}

export const insurerBrands: InsurerBrand[] = [
  brand("menora", "מנורה מבטחים", "menora.png", ["מנורה", "Menora", "Menora Mivtachim"]),
  brand("harel", "הראל", "harel.svg", ["Harel"]),
  brand("migdal", "מגדל", "migdal.svg", ["Migdal"]),
  brand("clal", "כלל ביטוח", "clal.svg", ["כלל", "Clal", "Clal Insurance"]),
  brand("phoenix", "הפניקס", "phoenix.png", ["פניקס", "Phoenix", "The Phoenix"]),
  brand("ayalon", "איילון", "ayalon.png", ["אילון", "Ayalon"]),
  brand("hachshara", "הכשרה", "hachshara.png", ["הכשרת הישוב", "הכשרת היישוב", "Hachshara"]),
  brand("aig", "AIG", "aig.svg", ["איי אי ג'י", "אי אי ג'י", "איי איי ג'י"]),
  brand("direct", "ביטוח ישיר", "direct.svg", ["ישיר", "איי.די.איי", "אי.די.אי", "IDI", "Direct Insurance"]),
  brand("nine", "ביטוח 9", "nine.png", ["9", "9 ביטוח", "9 מיליון", "תשעה מיליון", "9000000", "9,000,000"]),
  brand("libra", "ליברה", "libra.svg", ["Libra"]),
  brand("wesure", "ווישור", "wesure.png", ["וישור", "ווי שור", "וי שור", "weSure", "we-sure"]),
  brand("shlomo", "שלמה ביטוח", "shlomo.svg", ["שלמה", "ש. שלמה", "ש שלמה ביטוח", "Shlomo", "Shlomo Insurance"]),
  brand("shomera", "שומרה", "shomera.png", ["Shomera"]),
  brand("haklai", "ביטוח חקלאי", "haklai.svg", ["Bituach Haklai", "Agricultural Insurance"]),
  brand("davidshield", "דיוידשילד", "davidshield.svg", ["דיויד שילד", "דיוויד שילד", "דיווידשילד", "דיויד שילד חברה לביטוח", "DavidShield", "David Shield"]),
  brand("passportcard", "פספורטכארד", "passportcard.svg", ["פספורט כארד", "פספורט קארד", "פספורטקארד", "PassportCard", "Passport Card"]),
  brand("shirbit", "שירביט", "shirbit.png", ["שירביט מבית הראל", "Shirbit"]),
  brand("ankor", "אנקור", "ankor.png", ["Ankor", "NKR"]),
  brand("emi", "EMI", "emi.png", ["אי.אם.איי", "אי.אמ.איי", "אי.אם.איי עזר", "אי.אמ.איי עזר", "אי.אם.אי עזר", "עזר", "EMI עזר"]),
  brand("bss", "בססח", "bss.svg", ["בסס״ח", "ב.ס.ס.ח", "בססח החברה הישראלית לביטוח אשראי", "החברה הישראלית לביטוח אשראי", "ICIC", "BSSCH"]),
  brand("ashra", "אשרא", "ashra.png", ["אשרא החברה הישראלית לביטוח סיכוני סחר חוץ", "החברה הישראלית לביטוח סיכוני סחר חוץ", "Ashra"]),
  brand("inbal", "ענבל", "inbal.png", ["Inbal"]),
  brand("kanat", "קנט", "kanat.svg", ["קנ״ט", "קנט קרן לביטוח נזקי טבע בחקלאות", "קרן לביטוח נזקי טבע בחקלאות", "Kanat"]),
  brand("coface", "קופאס", "coface.png", ["Coface", "קומפני פרנסייז דאסורנס פור לה קומרס אקסטריור"]),
  brand("pool", "הפול", "pool.png", ["המאגר הישראלי לביטוח רכב", "המאגר הישראלי לביטוח רכב הפול", "המאגר הישראלי לביטוחי רכב הפול", "התאגיד המנהל של המאגר לביטוח רכב חובה הפול", "The Pool"]),
];

function normalized(name: string): string {
  return name.normalize("NFKC").toLowerCase().replace(/[^a-z0-9א-ת]/g, "");
}

// Only recognized legal suffixes may follow an alias. Arbitrary substring
// matching could incorrectly label an agency or an unknown insurer.
const legalSuffix = /^(?:(?:חברה|חברת)?ל?ביטוח(?:משכנתאות)?|ופיננסים|ופיננסיים|ישראל|בעמ|אגודהשיתופיתמרכזית|insurance|company|limited|ltd)*$/;
const aliases = insurerBrands.flatMap((entry) =>
  entry.aliases.map((alias) => ({ entry, alias: normalized(alias) })),
).sort((a, b) => b.alias.length - a.alias.length);

export function findInsurerBrand(name: string): InsurerBrand | undefined {
  const value = normalized(name);
  if (!value) return undefined;
  return aliases.find(({ alias }) =>
    value.startsWith(alias) && legalSuffix.test(value.slice(alias.length)),
  )?.entry;
}
