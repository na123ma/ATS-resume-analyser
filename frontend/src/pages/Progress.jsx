import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { FileSearch, MessagesSquare, ClipboardCheck, CodeXml, FilePenLine } from 'lucide-react';
import { api } from '../api';
import { Heading, Alert, Loading, Stats, Badge, Button, Field, date, Empty } from '../components/UI';
const sections = [
 ['reports', 'Resume analyses', '/analyzer/', FileSearch, x => x.filename],
 ['drafts', 'Saved resumes', '/builder/', FilePenLine, x => x.title],
 ['interviews', 'Interview practice', '/interview/', MessagesSquare, x => `${x.technology} · ${x.difficulty}`],
 ['exams', 'Skill assessments', '/assessments/', ClipboardCheck, x => `${x.technology} · ${x.mode}`],
 ['coding', 'Coding sessions', '/coding/', CodeXml, x => `${x.language} · ${x.difficulty}`],
];
export default function Progress({ onDeleted }) {
 const [data, setData] = useState(null), [error, setError] = useState(''), [password, setPassword] = useState(''), [busy, setBusy] = useState(false);
 useEffect(() => { api('/progress').then(setData).catch(e => setError(e.message)); }, []);
 async function deleteAccount(e) { e.preventDefault(); if (!confirm('Permanently delete your account and all resume, interview, assessment and coding records?')) return; setBusy(true); setError(''); try { await api('/auth/me', { method: 'DELETE', body: { password } }); onDeleted(); } catch (e) { setError(e.message); } finally { setBusy(false); } }
 return <><Heading eyebrow="ONE SESSION AT A TIME" title="See how far you’ve come.">Revisit your feedback, continue a draft, or pick up your next practice session.</Heading><Alert>{error}</Alert>{!data ? !error && <Loading /> : <><Stats items={[{ label: 'Resumes analyzed', value: data.totals.reports }, { label: 'Interview sessions', value: data.totals.interviews }, { label: 'Assessments taken', value: data.totals.exams }, { label: 'Coding sessions', value: data.totals.coding }]} /><div className="progress-grid">{sections.map(([key, title, path, Icon, label]) => <section className="card" key={key}><div className="card-heading"><div className="inline"><Icon size={21} className="blue" /><h2>{title}</h2></div><Badge>{data.totals[key]}</Badge></div>{data[key].length ? <div className="history-list">{data[key].map(x => <Link key={x.id} to={path + x.id}><div><strong>{label(x)}</strong><small>{date(x.created_at)}{x.status && ` · ${x.status}`}</small></div>{x.score != null ? <Badge tone={x.score >= 75 ? 'success' : ''}>{x.score}%</Badge> : <Badge>{key === 'drafts' ? 'Edit' : x.status === 'completed' ? 'Review' : 'Open'}</Badge>}</Link>)}</div> : <Empty>No sessions yet. <Link to={path.slice(0, -1)}>Start here</Link>.</Empty>}</section>)}</div></>}
 <details className="account-settings"><summary>Account & data</summary><p>Your PDFs are processed without retaining the original file. Reports, saved resumes, interview transcripts and coding records remain in your account until deleted. Provider-side retention follows the chosen AI, speech or execution provider’s settings.</p><form onSubmit={deleteAccount}><Field label="Password to confirm account deletion" type="password" autoComplete="current-password" value={password} onChange={e => setPassword(e.target.value)} required /><Button variant="danger" busy={busy}>Delete my account and data</Button></form></details></>;
}
