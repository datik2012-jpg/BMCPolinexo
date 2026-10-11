import { ExportAgentContext, ExportWorkspaceContext } from "./ExportButton";
import { useEffect, useRef, useState } from "react";
import { CustomerForm } from './CustomerForm';
import { CustomerPortfolio } from './CustomerPortfolio';
import { SharedPortfolio } from './SharedPortfolio';
import { Customer, customerReady, newCustomer, orderedCustomers, sameIdentity } from './customers';
import { Report } from './domain';

function newAgent() {
  const today = new Date();
  const date = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
  return { firstName: '', lastName: '', date };
}

export default function App() {
  const [agent, setAgent] = useState(newAgent);
  const agentDisclosure = useRef<HTMLDetailsElement>(null);
  const [customers, setCustomers] = useState<Customer[]>(() => [newCustomer('לקוח ראשי')]);
  const [selectedCustomers, setSelectedCustomers] = useState<string[]>([]);
  const [sharedCustomers, setSharedCustomers] = useState<string[]>([]);
  const displayedCustomers = orderedCustomers(customers);
  const eligible = displayedCustomers.filter(c => c.report);
  const selected = eligible.filter(c => selectedCustomers.includes(c.id));
  const shared = eligible.filter(c => sharedCustomers.includes(c.id));
  const showShared = shared.length >= 2;
  const selectionIsShown = showShared && selected.length === shared.length && selected.every(c => sharedCustomers.includes(c.id));
  function clearCustomers() {
    setAgent(newAgent());
    setCustomers([newCustomer('לקוח ראשי')]);
    setSelectedCustomers([]);
    setSharedCustomers([]);
    setError('');
  }
  const [available, setAvailable] = useState(false),
    [busy, setBusy] = useState(false),
    [message, setMessage] = useState(""),
    [error, setError] = useState("");
  useEffect(() => {
    const restored = (event: PageTransitionEvent) => {
      if (event.persisted) {
        uploadVersion.current++;
        clearCustomers();
        setBusy(false);
        setAvailable(false);
      }
    };
    window.addEventListener("pageshow", restored);
    return () => window.removeEventListener("pageshow", restored);
  }, []);
  const instance = useRef<string | null>(null),
    desktopMode = useRef(false),
    uploadVersion = useRef(0),
    checking = useRef(false);

  useEffect(() => {
    let active = true;
    async function check() {
      if (checking.current) return;
      checking.current = true;
      try {
        const response = await fetch("/api/instance", {
          cache: "no-store",
          signal: AbortSignal.timeout(2500),
        });
        if (!response.ok) throw Error();
        const data = await response.json();
        if (typeof data.instance_id !== "string") throw Error();
        if (!active) return;
        desktopMode.current = data.desktop_mode === true;
        if (instance.current && instance.current !== data.instance_id) {
          uploadVersion.current++;
          clearCustomers();
          setBusy(false);
          setMessage("השרת הופעל מחדש. הנתונים נוקו; אפשר להעלות קובץ מחדש.");
        }
        instance.current = data.instance_id;
        setAvailable(true);
      } catch {
        if (active) {
          setAvailable(false);
          // A desktop restart gets a new port: the old tab cannot reconnect
          // to learn the new instance ID. Clear it when its launcher goes away.
          if (desktopMode.current && instance.current !== null) {
            uploadVersion.current++;
            clearCustomers();
            setBusy(false);
            instance.current = null;
            setMessage("החיבור ליישום נותק והנתונים נוקו. יש לפתוח את היישום מחלון ההפעלה.");
          }
        }
      } finally {
        checking.current = false;
      }
    }
    void check();
    const timer = setInterval(check, 3000);
    window.addEventListener("focus", check);
    return () => {
      active = false;
      clearInterval(timer);
      window.removeEventListener("focus", check);
    };
  }, []);
  async function upload(customer: Customer, file?: File) {
    if (!file || !available || busy || !customerReady(customer.details) ||
      customers.some(c => c.id !== customer.id && sameIdentity(c.details.identity, customer.details.identity))) return;
    setMessage("");
    setError("");
    if (!file.name.toLowerCase().endsWith(".xlsx")) {
      setError("אפשר להעלות קובץ Excel בסיומת ‎.xlsx בלבד.");
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      setError("הקובץ גדול מדי. גודל הקובץ המרבי הוא 5 מגה־בייט.");
      return;
    }
    const version = ++uploadVersion.current;
    const expected = instance.current;
    setBusy(true);
    try {
      const body = new FormData();
      body.append("file", file);
      const response = await fetch("/api/import", {
        method: "POST",
        body,
        cache: "no-store",
        signal: AbortSignal.timeout(30000),
      });
      const data = await response.json();
      if (!response.ok)
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : "לא ניתן לקרוא את הקובץ.",
        );
      if (
        version !== uploadVersion.current ||
        expected !== instance.current ||
        data.instance_id !== instance.current
      ) {
        setError("השרת השתנה במהלך הייבוא. יש להעלות את הקובץ מחדש.");
        return;
      }
      const imported = data as Report;
      imported.entries = imported.entries.map(entry => ({ ...entry, baseline: { ...entry.values }, copied: false }));
      const identities = imported.entries.map(e => e.values.insured_id).filter(Boolean);
      if (!identities.length || identities.some(id => !sameIdentity(id, customer.details.identity))) {
        setError('תעודת הזהות בקובץ אינה תואמת ללקוח. הדוח הקודם נשמר; יש לבחור קובץ מתאים.');
        return;
      }
      setCustomers(all => all.map(c => c.id === customer.id ? { ...c, report: imported, revision: (c.revision || 0) + 1 } : c));
      setMessage("הקובץ נטען. מומלץ לבדוק את הסכומים מול המקור.");
    } catch (e) {
      if (version === uploadVersion.current)
        setError(
          e instanceof Error && e.name === "Error"
            ? e.message
            : "הייבוא לא הושלם. בדקו את החיבור ואת הקובץ ונסו שוב.",
        );
    } finally {
      if (version === uploadVersion.current) setBusy(false);
    }
  }
  return (
    <ExportAgentContext.Provider value={agent}>
    <ExportWorkspaceContext.Provider value={displayedCustomers}>
      <header className="topbar">
        <a href="#" className="brand" aria-label="BMSelect Insurance">
          <img className="brand-logo" src="/bmc-select.jpg" alt="BMSelect Insurance" />
        </a>
        <span className="session">
          <i className={available ? "online" : ""} />
          {available ? "סביבת עבודה מקומית" : "החיבור לשרת אינו זמין"}
        </span>
      </header>
      <main>
        <div className="page-heading">
          <div>
            <p className="eyebrow">תמונת הביטוח של הלקוח</p>
            <h1>כל הפוליסות. תמונה אחת.</h1>
            <p className="muted">
              מעלים את הדוח מהר הביטוח, בודקים את הכיסויים ומוודאים את הסכומים.
            </p>
          </div>
          <span className="privacy">◈ הנתונים זמניים בלבד</span>
        </div>
        <div className="notice workspace-notice">
          <span>המידע נשמר בזיכרון בלבד. רענון העמוד או הפעלה מחדש של השרת ימחקו את התיק ואת התיקונים.</span>
          {message && <><span className="notice-separator" aria-hidden="true"> · </span><span role="status" className="notice-status">{message}</span></>}
        </div>
        {error && (
          <p role="alert" className="error">
            {error}
          </p>
        )}
        {!available && (
          <p role="alert" className="error">
            לא ניתן לאמת את החיבור לשרת. העבודה נעולה עד לחידוש החיבור.
          </p>
        )}
        <fieldset disabled={!available || busy} className="workspace">
          <section className="customers" aria-label="לקוחות המשפחה">
            <details className="agent-disclosure" ref={agentDisclosure}>
              <summary>
                פרטי סוכן
                {(agent.firstName.trim() || agent.lastName.trim()) && <span className="agent-summary"> · {`${agent.firstName} ${agent.lastName}`.trim()}</span>}
                {agent.date && <span className="agent-summary"> · <bdi>{agent.date.split('-').reverse().join('/')}</bdi></span>}
                <span className="agent-edit-hint"> · עריכה</span>
              </summary>
              <section className="customer-card" aria-labelledby="agent-heading">
              <div className="customer-heading">
                <h2 id="agent-heading">פרטי סוכן הביטוח</h2>
              </div>
              <div className="customer-fields">
                <label>שם פרטי<input aria-label="שם פרטי של הסוכן" type="text" autoComplete="off" maxLength={100}
                  value={agent.firstName} onChange={event => setAgent(current => ({ ...current, firstName: event.target.value }))} /></label>
                <label>שם משפחה<input aria-label="שם משפחה של הסוכן" type="text" autoComplete="off" maxLength={100}
                  value={agent.lastName} onChange={event => setAgent(current => ({ ...current, lastName: event.target.value }))} /></label>
                <label>תאריך<input aria-label="תאריך הסוכן" type="date" dir="ltr" autoComplete="off"
                  value={agent.date} onChange={event => setAgent(current => ({ ...current, date: event.target.value }))} /></label>
              </div>
              <button type="button" className="primary customer-done" onClick={() => {
                if (agentDisclosure.current) {
                  agentDisclosure.current.open = false;
                  agentDisclosure.current.querySelector('summary')?.focus();
                }
              }}>סיום עריכה</button>
            </section>
            </details>
            {displayedCustomers.map(customer => <div key={customer.id}>
              <CustomerForm customer={customer} disabled={!available || busy}
                duplicate={customers.some(c => c.id !== customer.id && sameIdentity(c.details.identity, customer.details.identity))}
                onChange={details => setCustomers(all => all.map(c => c.id === customer.id ? { ...c, details } : c))}
                onRemove={() => {
                  if (customer.report && !window.confirm('להסיר את הלקוח ואת הדוח והתיקונים שלו?')) return;
                  setSelectedCustomers(ids => ids.filter(id => id !== customer.id));
                  setSharedCustomers(ids => ids.filter(id => id !== customer.id));
                  setCustomers(all => {
                    const remaining = all.filter(c => c.id !== customer.id);
                    return remaining.length ? remaining : [newCustomer('לקוח ראשי')];
                  });
                }}
                onUpload={file => void upload(customer, file)} />
              {customer.id === customers[customers.length - 1].id && <>
                <div className="add-customer-row">
                  <button type="button" onClick={() => setCustomers(all => [...all, newCustomer()])}>+ הוסף לקוח נוסף</button>
                  <small className="muted">בן/בת זוג, ילדים ובני משפחה נוספים · תיק נפרד לכל לקוח</small>
                </div>
                {customers.length > 1 && <section className="shared-selection" aria-label="בחירת לקוחות לתצוגה משותפת">
                  <div className="shared-selection-controls">
                    <h2>הצגת לקוחות יחד</h2>
                    <div className="shared-customer-options">
                      {displayedCustomers.map((c, index) => <label key={c.id}>
                        <input type="checkbox" disabled={!c.report} checked={selectedCustomers.includes(c.id)}
                          onChange={event => setSelectedCustomers(ids => event.target.checked ? [...ids, c.id] : ids.filter(id => id !== c.id))} />
                        <span>{[c.details.firstName, c.details.lastName].filter(Boolean).join(' ') || `לקוח ${index + 1}`}{!c.report && ' · יש להעלות דוח'}</span>
                      </label>)}
                    </div>
                    <div className="shared-selection-actions">
                      <button type="button" className={selectionIsShown ? 'shared-view-active' : ''} aria-pressed={selectionIsShown} disabled={selected.length < 2} onClick={() => setSharedCustomers(selected.map(c => c.id))}>הצגת הלקוחות יחד · {selected.length}</button>
                      {showShared && <button type="button" onClick={() => setSharedCustomers([])}>חזרה לתצוגה נפרדת</button>}
                    </div>
                  </div>
                  <p className="muted">בחרו לפחות שני לקוחות עם דוח · פוליסות תואמות יוצגו יחד; הסכומים נשארים נפרדים לכל לקוח.</p>
                  {showShared && <p role="status" className="shared-active-indicator">
                    <strong>✓ תצוגה משותפת פעילה · {shared.length} לקוחות</strong>
                    <span>{shared.map(c => `${c.details.firstName} ${c.details.lastName}`.trim()).join(' · ')}</span>
                    {!selectionIsShown && <small>הבחירה השתנתה. לחצו על הצגת הלקוחות יחד כדי לעדכן את התצוגה.</small>}
                  </p>}
                </section>}
              </>}
            </div>)}
            {showShared && <section className="shared-portfolio" aria-label="תיקי הביטוח בתצוגה משותפת">
              <SharedPortfolio key={shared.map(c => `${c.id}-${c.revision || 0}`).join('|')}
                customers={shared} available={available && !busy} setCustomers={setCustomers} />
            </section>}
            {displayedCustomers.map(customer => <section hidden={showShared} className="customer-section" key={customer.id} aria-label={`תיק לקוח ${customer.details.firstName || 'חדש'} ${customer.details.lastName}`}>
              <CustomerPortfolio customer={customer} available={available && !busy}
                key={`${customer.id}-${customer.revision || 0}`}
                setReport={value => setCustomers(all => all.map(c => c.id === customer.id ? {
                  ...c, report: typeof value === 'function' ? value(c.report) : value,
                } : c))} />
            </section>)}
          </section>
          {busy && <p role="status">הקובץ בעיבוד…</p>}
        </fieldset>
        <footer>
          BMCPolinexo · סביבת בדיקה מקומית · הסכומים השנתיים אינם תשלומים
          חודשיים
        </footer>
      </main>
    </ExportWorkspaceContext.Provider>
    </ExportAgentContext.Provider>
  );
}
