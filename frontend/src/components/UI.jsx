import { LoaderCircle, AlertCircle, Check, Sparkles } from 'lucide-react';
export const technologies = ['Python', 'JavaScript', 'React', 'Django', 'SQL', 'Java'];
export const languages = ['Python', 'JavaScript', 'Java', 'C++'];
export const levels = [{ value: 'easy', label: 'Simple' }, { value: 'medium', label: 'Medium' }, { value: 'hard', label: 'Hard' }];
export function Button({ children, busy, variant = 'primary', className = '', ...props }) {
  return <button className={`button ${variant} ${className}`} {...props} disabled={props.disabled || busy}>{busy && <LoaderCircle size={18} className="spin" />}{children}</button>;
}
export function Alert({ children, type = 'error' }) { return children ? <div className={`alert ${type}`} role={type === 'error' ? 'alert' : 'status'}><AlertCircle size={18} /><span>{children}</span></div> : null; }
export function Field({ label, children, ...props }) { return <label className="field"><span>{label}</span>{children || <input {...props} />}</label>; }
export function Select({ label, options, ...props }) { return <Field label={label}><select {...props}>{options.map(o => <option key={typeof o === 'string' ? o : o.value} value={typeof o === 'string' ? o : o.value}>{typeof o === 'string' ? o : o.label}</option>)}</select></Field>; }
export function Heading({ eyebrow, title, children, action }) { return <div className="page-heading"><div><p className="eyebrow">{eyebrow}</p><h1>{title}</h1>{children && <p className="lede">{children}</p>}</div>{action}</div>; }
export function Loading({ children = 'Loading your workspace…' }) { return <div className="loading"><LoaderCircle className="spin" /><p>{children}</p></div>; }
export function Empty({ children }) { return <div className="empty">{children}</div>; }
export function Badge({ children, tone = '' }) { return <span className={`badge ${tone}`}>{children}</span>; }
export function Checkbox({ children, ...props }) { return <label className="checkbox"><input type="checkbox" {...props} /><span>{children}</span></label>; }
export function AIConsent({ checked, onChange, context = 'your input', provider }) {
  return <div className="consent"><Checkbox checked={checked} onChange={e => onChange(e.target.checked)}><Sparkles size={15} /> Use AI for this session</Checkbox><p>If enabled, {context} is sent to the configured AI provider{provider ? ` (${provider})` : ''}. Built-in practice remains available when AI is off.</p></div>;
}
export function Score({ value, label = 'Resume readiness' }) { return <div className="score-ring" style={{ '--score': `${value || 0}%` }}><div><strong>{value ?? '—'}</strong><span>{label}</span></div></div>; }
export function Stats({ items }) { return <div className="stats">{items.map(x => <div className="stat" key={x.label}><span>{x.label}</span><strong>{x.value ?? '—'}</strong>{x.detail && <small>{x.detail}</small>}</div>)}</div>; }
export function date(value) { return new Date(value).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' }); }
export function clock(seconds) { const s = Math.max(0, Math.ceil(seconds)); return `${Math.floor(s / 60).toString().padStart(2, '0')}:${(s % 60).toString().padStart(2, '0')}`; }
