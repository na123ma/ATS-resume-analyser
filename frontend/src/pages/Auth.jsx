import { useState } from 'react';
import { Sparkles, FileCheck2, Mic, CodeXml, Check } from 'lucide-react';
import { api } from '../api';
import { Logo } from '../components/Layout';
import { Field, Button, Alert, Checkbox } from '../components/UI';
export default function Auth({ onLogin }) {
 const [mode, setMode] = useState('register');
 const [values, setValues] = useState({ full_name: '', email: '', password: '', confirm_password: '', leaderboard_opt_in: false });
 const [busy, setBusy] = useState(false), [error, setError] = useState('');
 const update = key => e => setValues(v => ({ ...v, [key]: e.target.value }));
 async function submit(e) {
   e.preventDefault(); setError(''); setBusy(true);
   try { const data = await api(`/auth/${mode}`, { method: 'POST', body: mode === 'register' ? values : { email: values.email, password: values.password } }); onLogin(data.user); }
   catch (e) { setError(e.message); } finally { setBusy(false); }
 }
 return <div className="auth-page"><div className="auth-story"><Logo /><div className="auth-copy"><p className="eyebrow">YOUR NEXT CHAPTER STARTS HERE</p><h1>Build confidence.<br /><em>Then build your career.</em></h1><p>A space to improve your resume, practise your answers, and put your skills to work.</p><div className="auth-features">{[[FileCheck2, 'A resume with a clearer direction', 'Understand the checks. Make the improvements.'], [Mic, 'Practice that feels like a conversation', 'Talk through your ideas with an AI interviewer.'], [CodeXml, 'Skills you can put to the test', 'Technology assessments and focused coding challenges.']].map(([Icon, title, desc]) => <div key={title}><span><Icon /></span><div><strong>{title}</strong><p>{desc}</p></div></div>)}</div></div><span className="auth-foot">Made for your first opportunity. And your next one.</span></div>
 <div className="auth-form-wrap"><form className="auth-form" onSubmit={submit}><div className="auth-switch"><button type="button" className={mode === 'register' ? 'active' : ''} onClick={() => { setMode('register'); setError(''); }}>Create account</button><button type="button" className={mode === 'login' ? 'active' : ''} onClick={() => { setMode('login'); setError(''); }}>Sign in</button></div><p className="eyebrow">WELCOME TO SKILLENTRA</p><h2>{mode === 'register' ? 'Your potential. A little more prepared.' : 'Welcome back.'}</h2><p className="muted">{mode === 'register' ? 'Create your account, then take a closer look at your resume.' : 'Pick up where you left off.'}</p><Alert>{error}</Alert>
 {mode === 'register' && <Field label="Full name" value={values.full_name} onChange={update('full_name')} autoComplete="name" minLength={2} maxLength={80} required />}
 <Field label="Email address" type="email" value={values.email} onChange={update('email')} autoComplete="email" required />
 <Field label="Password" type="password" value={values.password} onChange={update('password')} autoComplete={mode === 'login' ? 'current-password' : 'new-password'} minLength={mode === 'register' ? 10 : 1} maxLength={128} required />
 {mode === 'register' && <><small className="muted">Use at least 10 characters and avoid common passwords.</small><Field label="Confirm password" type="password" value={values.confirm_password} onChange={update('confirm_password')} autoComplete="new-password" required /><Checkbox checked={values.leaderboard_opt_in} onChange={e => setValues(v => ({ ...v, leaderboard_opt_in: e.target.checked }))}>Show my name and ranked test score on the community leaderboard.</Checkbox></>}
 <Button busy={busy} className="full">{mode === 'register' ? 'Create my account' : 'Sign in'}</Button><p className="form-note">Your resumes and interview history stay in your account. You control AI sharing for each session.</p></form></div></div>;
}
