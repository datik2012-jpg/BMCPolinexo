import { useEffect, useRef, useState } from 'react';
import { Customer } from './customers';

export function ExportButton({ customers, available }: { customers: Customer[]; available: boolean }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [done, setDone] = useState(false);
  const controller = useRef<AbortController | null>(null);
  useEffect(() => () => controller.current?.abort(), []);
  useEffect(() => { if (!available) controller.current?.abort(); }, [available]);
  async function download() {
    if (busy || !available) return;
    setBusy(true); setError(''); setDone(false);
    const abort = new AbortController();
    controller.current = abort;
    const timer = window.setTimeout(() => abort.abort(), 30000);
    try {
      const response = await fetch('/api/export', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, cache: 'no-store',
        body: JSON.stringify({ customers }), signal: abort.signal,
      });
      if (!response.ok) {
        const data = await response.json().catch(() => null);
        throw new Error(data?.detail || (response.status === 413 ? 'הנתונים גדולים מדי. נסו לייצא כל לקוח בנפרד.' : 'הייצוא נכשל. נסו שוב.'));
      }
      if (response.headers.get('X-Instance-Id') !== customers[0]?.report?.instance_id) throw new Error('השרת השתנה. יש לטעון את התיקים מחדש.');
      const blob = await response.blob();
      if (abort.signal.aborted) return;
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url; link.download = `insurance-portfolios-${new Date().toISOString().slice(0, 10)}.xlsx`;
      document.body.appendChild(link); link.click(); link.remove();
      window.setTimeout(() => URL.revokeObjectURL(url), 1000);
      setDone(true);
    } catch (e) {
      if (!abort.signal.aborted) setError(e instanceof Error ? e.message : 'הייצוא נכשל. נסו שוב.');
      else setError('הייצוא הופסק. בדקו את החיבור ונסו שוב.');
    } finally {
      window.clearTimeout(timer); setBusy(false); controller.current = null;
    }
  }
  return <div className="export-control">
    <button type="button" disabled={!available || busy} onClick={() => void download()}>{busy ? 'מכין קובץ…' : 'ייצוא ל־Excel'}</button>
    <small>כל הכיסויים{customers.length > 1 ? ` של ${customers.length} הלקוחות המוצגים` : ''}, כולל פרטים נוספים והחרגות</small>
    {error && <small role="alert" className="error">{error}</small>}
    {done && <small role="status">הקובץ הוכן להורדה</small>}
  </div>;
}
