import { Customer, CustomerDetails, customerReady, insuranceAge, displayBirthDate, parseBirthDateInput, validBirthDate } from './customers';
import { useId, useRef } from 'react';

export function CustomerForm({ customer, disabled, duplicate, onChange, onRemove, onUpload }: {
  customer: Customer; disabled: boolean; duplicate: boolean;
  onChange: (details: CustomerDetails) => void;
  onRemove: () => void; onUpload: (file?: File) => void;
}) {
  const d = customer.details;
  const birthDateId = useId();
  const calendar = useRef<HTMLInputElement>(null);
  const today = new Date();
  const maxDate = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
  const ready = customerReady(d) && !duplicate;
  function field(key: keyof CustomerDetails, label: string, type = 'text') {
    return <label>{label}{key === 'birthDate' ? ' (רשות)' : ' *'}<input aria-label={label} type={type} value={d[key]} required={key !== 'birthDate'}
      autoComplete="off" maxLength={key === 'identity' ? 9 : 100}
      inputMode={key === 'identity' ? 'numeric' : undefined}
      readOnly={key === 'identity' && Boolean(customer.report)}
      onChange={e => onChange({ ...d, [key]: e.target.value })} /></label>;
  }
  function select(key: keyof CustomerDetails, label: string, options: string[]) {
    const required = key === 'gender' || key === 'maritalStatus';
    return <label>{label}{required ? ' *' : ' (רשות)'}<select aria-label={label} value={d[key]} required={required} onChange={e => onChange({ ...d, [key]: e.target.value })}>
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
        <div className="birth-date-field">
          <label htmlFor={birthDateId}>תאריך לידה (רשות)</label>
          <div className="birth-date-controls">
          <input id={birthDateId} aria-label="תאריך לידה" type="text" dir="ltr"
            placeholder="DD/MM/YYYY" maxLength={10} autoComplete="off"
            value={displayBirthDate(d.birthDate)}
            aria-invalid={Boolean(d.birthDate && !validBirthDate(d.birthDate))}
            onChange={e => onChange({ ...d, birthDate: parseBirthDateInput(e.target.value) })} />
          <div className="birth-date-calendar">
            <button type="button" aria-label="בחירת תאריך לידה בלוח שנה" title="בחירת תאריך בלוח שנה"
              onClick={() => {
                if (calendar.current?.showPicker) calendar.current.showPicker();
                else { calendar.current?.focus(); calendar.current?.click(); }
              }}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M7 3v4M17 3v4M3 11h18M7 15h3M14 15h3" /></svg>
            </button>
            <input ref={calendar} className="birth-date-native" type="date" tabIndex={-1}
              aria-label="תאריך לידה בלוח שנה" min="1900-01-01" max={maxDate}
              value={validBirthDate(d.birthDate) ? d.birthDate : ''}
              onChange={e => onChange({ ...d, birthDate: e.target.value })} />
          </div>
          </div>
          <small>{d.birthDate && !validBirthDate(d.birthDate) ? 'יש להזין תאריך תקין: יום/חודש/שנה' : 'יום/חודש/שנה · לדוגמה 25/09/1990'}</small>
        </div>
        <label>גיל ביטוחי<input aria-label="גיל ביטוחי" readOnly value={insuranceAge(d.birthDate) ?? ''} placeholder="—" /><small>לפי יום ההולדת האחרון</small></label>
        {select('gender', 'מין', ['זכר', 'נקבה', 'אחר'])}
        {select('smoking', 'עישון', ['לא מעשן/ת', 'מעשן/ת'])}
        {select('maritalStatus', 'מצב משפחתי', ['רווק/ה', 'נשוי/אה', 'גרוש/ה', 'אלמן/ה', 'פרוד/ה', 'ידוע/ה בציבור'])}
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
        {customer.report && <span className="upload-success" role="status">
          <span aria-hidden="true">✓</span> קובץ Excel הועלה בהצלחה
        </span>}
        <small>{ready ? 'קובץ אחד למבוטח · עד 5 מגה־בייט' : 'חובה למלא שם פרטי, שם משפחה, תעודת זהות בת 9 ספרות, מין ומצב משפחתי. תאריך לידה, אם הוזן, חייב להיות תקין.'}</small>
      </div>
    </fieldset>
  </section>;
}
