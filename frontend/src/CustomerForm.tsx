import { Customer, CustomerDetails, customerReady, insuranceAge } from './customers';

export function CustomerForm({ customer, disabled, duplicate, onChange, onRemove, onUpload }: {
  customer: Customer; disabled: boolean; duplicate: boolean;
  onChange: (details: CustomerDetails) => void;
  onRemove: () => void; onUpload: (file?: File) => void;
}) {
  const d = customer.details;
  const ready = customerReady(d) && !duplicate;
  function field(key: keyof CustomerDetails, label: string, type = 'text') {
    return <label>{label}{key === 'birthDate' ? ' (רשות)' : ' *'}<input aria-label={label} type={type} value={d[key]} required={key !== 'birthDate'}
      autoComplete="off" maxLength={key === 'identity' ? 9 : 100}
      inputMode={key === 'identity' ? 'numeric' : undefined}
      readOnly={key === 'identity' && Boolean(customer.report)}
      onChange={e => onChange({ ...d, [key]: e.target.value })} /></label>;
  }
  function select(key: keyof CustomerDetails, label: string, options: string[]) {
    return <label>{label}{key === 'gender' ? ' *' : ' (רשות)'}<select aria-label={label} value={d[key]} required={key === 'gender'} onChange={e => onChange({ ...d, [key]: e.target.value })}>
      <option value="">בחירה</option>{options.map(v => <option key={v}>{v}</option>)}
    </select></label>;
  }
  return <section className="customer-card" aria-label="פרטי לקוח">
    <fieldset disabled={disabled}>
      <div className="customer-heading">
        <h2>{d.firstName.trim() ? `${d.firstName} ${d.lastName}` : 'לקוח חדש'}</h2>
        <button type="button" onClick={onRemove}>הסרת לקוח</button>
      </div>
      <div className="customer-fields">
        {select('relationship', 'קרבה משפחתית', ['לקוח ראשי', 'בן/בת זוג', 'ילד/ה', 'בן משפחה אחר'])}
        {field('firstName', 'שם פרטי')}
        {field('lastName', 'שם משפחה')}
        {field('identity', 'תעודת זהות')}
        {field('birthDate', 'תאריך לידה', 'date')}
        <label>גיל ביטוחי<input aria-label="גיל ביטוחי" readOnly value={insuranceAge(d.birthDate) ?? ''} placeholder="—" /><small>לפי יום ההולדת האחרון</small></label>
        {select('gender', 'מין', ['זכר', 'נקבה', 'אחר'])}
        {select('smoking', 'עישון', ['לא מעשן/ת', 'מעשן/ת'])}
      </div>
      {duplicate && <p className="warning">כבר קיים לקוח עם תעודת זהות זו.</p>}
      {customer.report && <p className="muted">הדוח נטען · {customer.report.entries.length} כיסויים. העלאה חדשה תחליף רק את הדוח והתיקונים של לקוח זה.</p>}
      <div className="customer-upload">
        <label className={'button primary upload-button' + (!ready ? ' upload-disabled' : '')}>
          <svg className="upload-mountain" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round" aria-hidden="true"><path d="M2 20 10 4l5 10 3-5 4 11H2Z" /><path d="m7 10 3 2 3-2" /></svg>
          {customer.report ? 'העלאת קובץ Excel הר ביטוח' : 'העלאת קובץ Excel הר ביטוח'}
          <input aria-label="העלאת קובץ Excel הר ביטוח" type="file" accept=".xlsx" disabled={!ready}
            onChange={e => { onUpload(e.target.files?.[0]); e.target.value = ''; }} />
        </label>
        <small>{ready ? 'קובץ אחד למבוטח · עד 5 מגה־בייט' : 'חובה למלא שם פרטי, שם משפחה, תעודת זהות בת 9 ספרות ומין. תאריך לידה, אם הוזן, חייב להיות תקין.'}</small>
      </div>
    </fieldset>
  </section>;
}
