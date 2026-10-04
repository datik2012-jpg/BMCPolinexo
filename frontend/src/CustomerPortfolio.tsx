import { copyCoverage, mergeProposal, removeProposalCoverage, startingEntry } from './workspace';
import { insuranceCategory, insuranceCategories, insuranceCategoryGroups } from './insuranceCategories';
import { useEffect, useId, useRef, useState } from "react";
import { InsurerLogo } from "./InsurerLogo";
import { Customer } from './customers';
import { ExportButton } from './ExportButton';
import {
  Entry,
  Fields,
  Report,
  frequency,
  frequencyLabel,
  groups,
  issues,
  isChanged,
  labels,
  money,
  totals,
} from "./domain";

const fieldNames = Object.keys(labels) as (keyof Fields)[];
function Value({ value }: { value: string }) {
  const direction = /^[\d\s/.,:₪()+\-]+$/.test(value) ? "ltr" : "auto";
  return <bdi dir={direction}>{value || "—"}</bdi>;
}
function Totals({
  entries,
  title,
  original = false,
}: {
  entries: Entry[];
  title: string;
  original?: boolean;
}) {
  const t = totals(entries, original);
  return (
    <section className="totals" aria-label={title}>
      <div>
        <span className="eyebrow">{title}</span>
        <strong>פרמיות הביטוח</strong>
        {t.incomplete && (
          <small className="warning">הסכומים חלקיים — נדרש בירור</small>
        )}
      </div>
      <div>
        <span>פרמיות חודשיות</span>
        <strong dir="ltr">{money(t.monthly)}</strong>
        {t.monthlyIncomplete && <small className="warning">סכום חלקי</small>}
      </div>
      <div>
        <span>פרמיות שנתיות</span>
        <strong dir="ltr">{money(t.annual)}</strong>
        {t.annualIncomplete && <small className="warning">סכום חלקי</small>}
      </div>
    </section>
  );
}
type PortfolioProps = {
  customer: Customer; available: boolean;
  members?: Customer[]; ownerOf?: (entry: Entry) => Customer;
  setReport: (value: Report | null | ((r: Report | null) => Report | null)) => void;
};

export function CustomerPortfolio(props: PortfolioProps) {
  const [view, setView] = useState<'existing' | 'proposed'>('existing');
  const [compare, setCompare] = useState(false);
  const viewId = useId();
  const report = props.customer.report;
  if (!report) return null;
  const baseline = { ...report, entries: report.entries.map(startingEntry) };
  const proposal = { ...report, entries: report.entries.filter(entry => entry.copied) };
  function sectionCustomers(rows: Entry[]) {
    return props.members?.map(member => ({ ...member, report: member.report ? {
      ...member.report, entries: rows.filter(entry => props.ownerOf?.(entry).id === member.id),
    } : null })).filter(member => member.report?.entries.length);
  }
  return <>
    <div className="portfolio-navigation">
      <div role="tablist" aria-label="מצבי תיק הביטוח" onKeyDown={event => {
        if (['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) {
          event.preventDefault();
          const next = event.key === 'Home' ? 'existing' : event.key === 'End' ? 'proposed' : view === 'existing' ? 'proposed' : 'existing';
          setView(next); setCompare(false);
          document.getElementById(`${viewId}-${next}-tab`)?.focus();
        }
      }}>
        {(['existing', 'proposed'] as const).map(tab => <button key={tab} id={`${viewId}-${tab}-tab`}
          role="tab" aria-selected={view === tab} tabIndex={view === tab ? 0 : -1}
          aria-controls={`${viewId}-${tab}`} className={`state-tab ${tab}`}
          onClick={() => { setView(tab); setCompare(false); }}>
          {tab === 'existing' ? 'מצב קיים' : 'מצב חדש'} <span>{tab === 'existing' ? baseline.entries.length : proposal.entries.length}</span>
        </button>)}
      </div>
      <button type="button" className={compare ? 'selected' : ''} aria-pressed={compare} onClick={() => setCompare(!compare)}>השוואה</button>
    </div>
    <div className={compare ? 'portfolio-views comparing' : 'portfolio-views'}>
    <section id={`${viewId}-existing`} role="tabpanel" aria-labelledby={`${viewId}-existing-tab`} hidden={!compare && view !== 'existing'} className="comparison-section existing-section" aria-label="מצב קיים — לפני השינויים">
      <h2>מצב קיים — לפני השינויים</h2>
      <p className="muted">נתוני הייבוא נשארים ללא שינוי. העתיקו כיסוי למצב החדש כדי לערוך אותו.</p>
      <PortfolioView {...props} customer={{ ...props.customer, report: baseline }}
        members={sectionCustomers(baseline.entries)} readOnly
        onCopy={id => props.setReport(current => current ? copyCoverage(current, id) : null)} />
    </section>
    <section id={`${viewId}-proposed`} role="tabpanel" aria-labelledby={`${viewId}-proposed-tab`} hidden={!compare && view !== 'proposed'} className="comparison-section proposed-section" aria-label="מצב חדש, חוסרים והמלצות">
      <h2>מצב חדש, חוסרים והמלצות</h2>
      <p className="muted">הצעה בלבד · הסכומים כוללים רק כיסויים שהועתקו. כיסוי שלא הועתק אינו נחשב כמבוטל.</p>
      {!proposal.entries.length ? <p className="empty">עדיין לא הועתקו כיסויים. לחצו על ״העתקה למצב החדש״ במצב הקיים.</p> :
        <PortfolioView {...props} customer={{ ...props.customer, report: proposal }}
          members={sectionCustomers(proposal.entries)}
          onRemove={id => props.setReport(current => current ? removeProposalCoverage(current, id) : null)}
          setReport={value => props.setReport(current => {
            if (!current) return null;
            const working = { ...current, entries: current.entries.filter(entry => entry.copied) };
            const next = typeof value === 'function' ? value(working) : value;
            return next ? mergeProposal(current, next) : current;
          })} />}
    </section>
    </div>
  </>;
}

function PortfolioView({ customer, available, setReport, members, ownerOf, readOnly = false, onCopy, onRemove }: PortfolioProps & {
  readOnly?: boolean; onCopy?: (id: string) => void; onRemove?: (id: string) => void;
}) {
  const report = customer.report;
  const nameOf = (c: Customer) => [c.details.firstName, c.details.lastName].filter(Boolean).join(' ');
  const entryName = (e: Entry) => nameOf(ownerOf ? ownerOf(e) : customer);
  function portfolioTotals(rows: Entry[], title: string, original = false) {
    return members ? members.map(member => <Totals key={member.id}
      entries={rows.filter(e => ownerOf?.(e).id === member.id)}
      title={`${nameOf(member)} · ${title}`} original={original} />)
      : <Totals entries={rows} title={title} original={original} />;
  }
  const [edit, setEdit] = useState<Entry | null>(null);
  const [draft, setDraft] = useState<Fields | null>(null);
  const [source, setSource] = useState(false);
  const [sourceFocus, setSourceFocus] = useState<string | null>(null);
  const [filters, setFilters] = useState({ insurer: '', frequency: '', review: '' });
  const [categorySelection, setCategorySelection] = useState<Record<string, boolean>>({});
  const editButton = useRef<HTMLElement | null>(null);
  const panel = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!edit) return;
    const previous = document.activeElement as HTMLElement;
    panel.current?.querySelector<HTMLInputElement>("input")?.focus();
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setEdit(null);
        setDraft(null);
      }
      if (event.key === "Tab") {
        const elements = panel.current?.querySelectorAll<HTMLElement>(
          "button:not(:disabled),input:not(:disabled),select:not(:disabled)",
        );
        if (!elements?.length) return;
        const first = elements[0],
          last = elements[elements.length - 1];
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault();
          last.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first.focus();
        }
      }
    };
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("keydown", onKey);
      (editButton.current || previous)?.focus();
    };
  }, [edit]);
  const entries = report?.entries || [];
  const otherCategories = [...new Set(entries.map(e => insuranceCategory(e.values)))].filter(category => !insuranceCategories.includes(category));
  const categories = [...insuranceCategories, ...otherCategories];
  const categoryChecked = (category: string) => categorySelection[category] ??
    !['רכב', 'סיעוד'].includes(category);
  const selectedCategoryCount = categories.filter(categoryChecked).length;
  const filtered = entries.filter(
    (e) =>
      categoryChecked(insuranceCategory(e.values)) &&
      (!filters.insurer || e.values.insurer === filters.insurer) &&
      (!filters.frequency ||
        frequency(e.values.frequency) === filters.frequency) &&
      (!filters.review ||
        (filters.review === "excluded"
          ? e.excluded
          : !e.excluded && issues(e, entries).length > 0)),
  );
  const flagged = entries.filter(
    (e) => !e.excluded && issues(e, entries).length,
  ).length;
  const activeFilters = Object.values(filters).some(Boolean) || selectedCategoryCount < categories.length;
  function update(entry: Entry) {
    if (readOnly || !available) return;
    setReport((r) =>
      r
        ? {
            ...r,
            entries: r.entries.map((e) => (e.id === entry.id ? entry : e)),
          }
        : null,
    );
  }
  function startEdit(e: Entry) {
    if (readOnly || !available) return;
    editButton.current = document.activeElement as HTMLElement;
    setEdit(e);
    setDraft({ ...e.values });
  }
  return <>
          {report && (
            <>
              <div className="section-heading portfolio-heading">
                <div>
                  <h2>{members ? 'תצוגה משותפת' : 'תיק הביטוח'} — {members ? members.map(nameOf).join(' · ') : nameOf(customer)}</h2>
                  <p className="muted">
                    {groups(entries, !!members).length} פוליסות · {entries.length} כיסויים{" "}
                    {report.report_date && (
                      <>
                        · תאריך הדוח <Value value={report.report_date} />
                      </>
                    )}
                  </p>
                </div>
                <div className="portfolio-actions">
                <button
                  className={source ? "selected" : ""}
                  onClick={() => setSource(!source)}
                >
                  {source ? "חזרה לפוליסות" : "השוואה למקור"}
                </button>
                <ExportButton customers={members || [customer]} available={available} />
                </div>
              </div>
              {portfolioTotals(entries, readOnly ? "מצב קיים · כל הכיסויים" : "מצב חדש · כיסויים שהועתקו בלבד")}
              {(flagged > 0 || report.warnings.length > 0) && (
                <details className="review-banner portfolio-review">
                  <summary>
                    {flagged > 0
                      ? `${flagged} כיסויים דורשים בדיקה`
                      : "הערות לייבוא"}
                  </summary>
                  <p>
                    שורות חשודות אינן נמחקות אוטומטית. הפרמיות התקינות נכללות עד
                    להחרגה.
                  </p>
                  {report.warnings.map((w, i) => (
                    <p key={i}>{w}</p>
                  ))}
                </details>
              )}
              <div className="filters">
                <div className="category-filter">
                  <span>ענף ביטוח</span>
                  <details onKeyDown={e => {
                    if (e.key === 'Escape') {
                      e.currentTarget.open = false;
                      e.currentTarget.querySelector('summary')?.focus();
                    }
                  }}>
                    <summary aria-label="ענף ביטוח">
                      {selectedCategoryCount === categories.length ? 'כל הענפים' :
                        selectedCategoryCount === 0 ? 'לא נבחרו ענפים' : `${selectedCategoryCount} מתוך ${categories.length} ענפים`}
                    </summary>
                    <div className="category-options" role="group" aria-label="בחירת ענפי ביטוח">
                      {insuranceCategoryGroups.map(group => <details className="category-group" key={group.label}>
                        <summary>{group.label}</summary>
                        <div role="group" aria-label={group.label}>
                          {group.options.map(category => <label key={category}>
                            <input type="checkbox" checked={categoryChecked(category)}
                              onChange={e => setCategorySelection(previous => ({ ...previous, [category]: e.target.checked }))} />
                            {category}
                          </label>)}
                        </div>
                      </details>)}
                      {otherCategories.length > 0 && <div className="category-unmapped" role="group" aria-label="ענפים נוספים מהקובץ">
                        <span>ענפים נוספים מהקובץ</span>
                        {otherCategories.map(category => <label key={category}>
                          <input type="checkbox" checked={categoryChecked(category)}
                            onChange={e => setCategorySelection(previous => ({ ...previous, [category]: e.target.checked }))} />
                          {category}
                        </label>)}
                      </div>}
                    </div>
                  </details>
                </div>
                <label>
                  חברת ביטוח
                  <select
                    aria-label="חברת ביטוח"
                    value={filters.insurer}
                    onChange={(e) =>
                      setFilters({ ...filters, insurer: e.target.value })
                    }
                  >
                    <option value="">כל החברות</option>
                    {[...new Set(entries.map((e) => e.values.insurer))]
                      .filter(Boolean)
                      .map((v) => (
                        <option key={v}>{v}</option>
                      ))}
                  </select>
                </label>
                <label>
                  תדירות תשלום
                  <select
                    aria-label="תדירות תשלום"
                    value={filters.frequency}
                    onChange={(e) =>
                      setFilters({ ...filters, frequency: e.target.value })
                    }
                  >
                    <option value="">כל התדירויות</option>
                    <option value="monthly">חודשית</option>
                    <option value="annual">שנתית</option>
                    <option value="unknown">לא ידועה</option>
                  </select>
                </label>
                <label>
                  מצב בדיקה
                  <select
                    aria-label="מצב בדיקה"
                    value={filters.review}
                    onChange={(e) =>
                      setFilters({ ...filters, review: e.target.value })
                    }
                  >
                    <option value="">כל הכיסויים</option>
                    <option value="review">דורשים בדיקה</option>
                    <option value="excluded">הוחרגו מחישוב</option>
                  </select>
                </label>
                {activeFilters && (
                  <button
                    onClick={() => {
                      setCategorySelection(Object.fromEntries(categories.map(category => [category, true])));
                      setFilters({
                        insurer: "",
                        frequency: "",
                        review: "",
                      });
                    }}
                  >
                    ניקוי סינון
                  </button>
                )}
              </div>
              {activeFilters && (
                portfolioTotals(filtered, "תוצאות הסינון בלבד")
              )}
              {source ? (
                <>
                  <div className="source-intro">
                    <h2>מהמקור לתיק המעודכן</h2>
                    <button type="button" onClick={() => { setSource(false); setSourceFocus(null); }}>חזרה לפוליסות</button>
                    <p>
                      ערכי המקור אינם משתנים. כאן אפשר לבדוק כל שורה ואת ההשפעה
                      המצטברת של התיקונים וההחרגות.
                    </p>
                  </div>
                  {portfolioTotals(entries, "כל התיק · ערכי המקור", true)}
                  {!members && <div className="delta">
                    שינוי מול המקור (כל התיק): חודשי{" "}
                    <bdi>
                      {money(
                        totals(entries).monthly.minus(
                          totals(entries, true).monthly,
                        ),
                      )}
                    </bdi>{" "}
                    · שנתי{" "}
                    <bdi>
                      {money(
                        totals(entries).annual.minus(
                          totals(entries, true).annual,
                        ),
                      )}
                    </bdi>
                    {(totals(entries).incomplete ||
                      totals(entries, true).incomplete) &&
                      " · ההשוואה חלקית עד להשלמת הפרטים החסרים"}
                  </div>}
                  {filtered.map((e) => (
                    <details
                      className="source-row"
                      key={e.id}
                      open={sourceFocus === e.id || undefined}
                    >
                      <summary>
                        <span>
                          {members && <><bdi>{entryName(e)}</bdi> · </>}
                          שורה <bdi>{e.source_row}</bdi> ·{" "}
                          <Value value={e.source_sheet} /> ·{" "}
                          <Value value={e.values.product_type} />
                        </span>
                        <span>
                          {e.excluded
                            ? "הוחרגה"
                            : isChanged(e)
                              ? "כוללת תיקונים"
                              : "לבדיקה מול המקור"}
                        </span>
                      </summary>
                      <button type="button" onClick={() => { setSource(false); setSourceFocus(null); }}>חזרה לפוליסות</button>
                      <div className="table-scroll">
                        <table>
                          <thead>
                            <tr>
                              <th>שדה</th>
                              <th>מקור Excel</th>
                              <th>ערך נוכחי</th>
                            </tr>
                          </thead>
                          <tbody>
                            {fieldNames.map((k) => (
                              <tr key={k}>
                                <th>{labels[k]}</th>
                                <td>
                                  <Value value={e.original[k]} />
                                </td>
                                <td>
                                  <Value
                                    value={
                                      k === "frequency"
                                        ? frequencyLabel(e.values[k])
                                        : e.values[k]
                                    }
                                  />
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                      {!readOnly && <button onClick={() => startEdit(e)}>עריכת השורה</button>}
                    </details>
                  ))}
                </>
              ) : (
                <div className="policies">
                  {groups(filtered, !!members).map(([key, rows]) => {
                    const first = rows[0].values,
                      t = totals(rows);
                    return (
                      <details className="policy" key={key} open>
                        <summary>
                          <span className="policy-marker">
                            <InsurerLogo insurer={first.insurer} />
                            <span className="chevron" aria-hidden="true">⌄</span>
                          </span>
                          <div className="policy-title">
                            <strong>{first.insurer || "חברה לא ידועה"}</strong>
                            <span>
                              פוליסה <Value value={first.policy_number} />
                            </span>
                          </div>
                          <div className="policy-categories">
                            {[
                              ...new Set(rows.map((e) => e.values.category)),
                            ].join(" · ")}
                            <small>
                              {[
                                ...new Set(
                                  rows.map((e) => e.values.product_type),
                                ),
                              ].join(" · ")}
                            </small>
                            <small>
                              {new Set(rows.map((e) => e.values.period)).size > 1
                                ? "תקופות ביטוח שונות"
                                : <Value value={first.period || "תקופה לא ידועה"} />}
                            </small>
                            <small>
                              כמות כיסויים: {rows.length}
                            </small>
                          </div>
                          {members ? <div className="shared-policy-totals">
                            {members.filter(member => rows.some(e => ownerOf?.(e).id === member.id)).map(member => {
                              const amounts = totals(rows.filter(e => ownerOf?.(e).id === member.id));
                              return <div key={member.id}><strong>{nameOf(member)}</strong>
                                <small>חודשי <bdi>{money(amounts.monthly)}</bdi> · שנתי <bdi>{money(amounts.annual)}</bdi>{amounts.incomplete && ' · חלקי'}</small>
                              </div>;
                            })}
                            <div className="shared-monthly-total">
                              <strong>סה״כ חודשי ללקוחות המוצגים</strong>
                              <bdi>{money(t.monthly)}</bdi>
                              {t.monthlyIncomplete && <small className="warning">סכום חלקי — נדרש בירור</small>}
                            </div>
                          </div> : <><div className="policy-amount">
                            <small>חודשי</small>
                            <bdi>{money(t.monthly)}</bdi>
                          </div>
                          {t.incomplete && <span className="badge">חלקי</span>}</>}
                        </summary>
                        <div className="table-scroll">
                          <table>
                            <thead>
                              <tr>
                                <th>כיסוי</th>
                                <th>שם המבוטח</th>
                                <th>תקופת ביטוח</th>
                                <th>פרמיה</th>
                                <th>בדיקה ומקור</th>
                                <th className="actions">פעולות</th>
                              </tr>
                            </thead>
                            <tbody>
                              {rows.map((e) => (
                                <tr
                                  key={e.id}
                                  className={e.excluded ? "excluded" : ""}
                                >
                                  <td>
                                    <strong>
                                      <Value value={e.values.product_type} />
                                    </strong>
                                    <small>
                                      <Value value={e.values.subcategory} />
                                    </small>
                                  </td>
                                  <td>
                                    <bdi>{entryName(e)}</bdi>
                                  </td>
                                  <td>
                                    <Value value={e.values.period} />
                                  </td>
                                  <td>
                                    <bdi>{e.values.premium || "—"}</bdi> ₪
                                    <small>
                                      {frequencyLabel(e.values.frequency)}
                                    </small>
                                  </td>
                                  <td>
                                    <small>
                                      שורה {e.source_row} ·{" "}
                                      <Value value={e.source_sheet} />
                                    </small>
                                    {e.values.additional_details.trim() && <details className="coverage-details" open>
                                      <summary><strong>הוראות הסוכן</strong></summary>
                                      <div dir="auto">{e.values.additional_details}</div>
                                    </details>}
                                    {e.excluded ? (
                                      <span className="badge">
                                        הוחרג מהחישוב
                                      </span>
                                    ) : (
                                      issues(e, entries).map((i) => (
                                        <small className="warning" key={i}>
                                          {i}
                                        </small>
                                      ))
                                    )}
                                  </td>
                                  <td className="actions">
                                    {readOnly ? <button disabled={!available || e.copied} onClick={() => onCopy?.(e.id)}>
                                      {e.copied ? 'הועתק למצב החדש' : 'העתקה למצב החדש'}
                                    </button> : <>
                                    <button onClick={() => startEdit(e)}>
                                      עריכה
                                    </button>
                                    <button
                                      onClick={() => {
                                        setSource(true);
                                        setSourceFocus(e.id);
                                      }}
                                    >
                                      מקור
                                    </button>
                                    <button
                                      onClick={() =>
                                        update({ ...e, excluded: !e.excluded })
                                      }
                                    >
                                      {e.excluded ? "שחזור" : "החרגה"}
                                    </button>
                                    <button disabled={!available} onClick={() => onRemove?.(e.id)}
                                      title="הסרת העותק והשינויים מהמצב החדש. הכיסוי המקורי נשאר במצב הקיים וניתן להעתיק אותו שוב.">
                                      הסרה מהמצב החדש
                                    </button>
                                    </>}
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </details>
                    );
                  })}
                </div>
              )}
              {filtered.length === 0 && (
                <p className="empty">אין כיסויים המתאימים לסינון שבחרתם.</p>
              )}
            </>
          )}
      {edit && draft && (
        <div className="overlay">
          <div
            ref={panel}
            className="edit-panel"
            role="dialog"
            aria-modal="true"
            aria-labelledby={`edit-heading-${customer.id}`}
          >
            <div className="section-heading">
              <div>
                <p className="eyebrow">תיקון זמני · שורה {edit.source_row}</p>
                <h2 id={`edit-heading-${customer.id}`}>עריכת הכיסוי{members && edit ? ` — ${entryName(edit)}` : ''}</h2>
              </div>
              <button
                aria-label="סגירת העריכה"
                onClick={() => {
                  setEdit(null);
                  setDraft(null);
                }}
              >
                ✕
              </button>
            </div>
            <p className="muted">
              ערכי המקור נשמרים להשוואה. שינוי החברה או מספר הפוליסה יעדכן את
              הקיבוץ.
            </p>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                if (!available) return;
                update({ ...edit, values: draft });
                setEdit(null);
                setDraft(null);
              }}
            >
              <fieldset disabled={!available}>
                <div className="edit-fields">
                  {fieldNames.map((k) => (
                    <label key={k}>
                      {labels[k]}
                      {k === "frequency" ? (
                        <select
                          aria-label={labels[k]}
                          value={draft[k]}
                          onChange={(e) =>
                            setDraft({ ...draft, [k]: e.target.value })
                          }
                        >
                          <option value="monthly">חודשית</option>
                          <option value="annual">שנתית</option>
                          {!["monthly", "annual"].includes(draft[k]) && (
                            <option value={draft[k]}>
                              {draft[k] || "לא ידועה"}
                            </option>
                          )}
                        </select>
                      ) : (
                        <input
                          aria-label={labels[k]}
                          value={draft[k]}
                          readOnly={k === "insured_id"}
                          dir={
                            [
                              "insured_id",
                              "premium",
                              "policy_number",
                              "period",
                            ].includes(k)
                              ? "ltr"
                              : undefined
                          }
                          onChange={(e) =>
                            setDraft({ ...draft, [k]: e.target.value })
                          }
                        />
                      )}
                      <small>
                        מקור: <Value value={edit.original[k]} />
                      </small>
                    </label>
                  ))}
                </div>
                <div className="panel-actions">
                  <button type="submit" className="primary">
                    שמירת תיקונים
                  </button>
                  <button
                    type="button"
                    onClick={() =>
                      setDraft({
                        ...edit.original,
                        frequency:
                          frequency(edit.original.frequency) === "unknown"
                            ? edit.original.frequency
                            : frequency(edit.original.frequency),
                      })
                    }
                  >
                    איפוס לערכי המקור
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setEdit(null);
                      setDraft(null);
                    }}
                  >
                    ביטול
                  </button>
                </div>
              </fieldset>
            </form>
          </div>
        </div>
      )}
  </>;
}
