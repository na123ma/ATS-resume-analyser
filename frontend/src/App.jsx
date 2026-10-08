import { Component, useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import { api } from './api';
import Layout from './components/Layout';
import { Alert, Loading, Button } from './components/UI';
import Auth from './pages/Auth';
import Analyzer from './pages/Analyzer';
import Builder from './pages/Builder';
import Interview from './pages/Interview';
import Assessments from './pages/Assessments';
import Coding from './pages/Coding';
import Leaderboard from './pages/Leaderboard';
import Progress from './pages/Progress';
class ErrorBoundary extends Component {
 state = { error: false };
 static getDerivedStateFromError() { return { error: true }; }
 render() { return this.state.error ? <div className="loading"><h2>Something didn’t load correctly.</h2><p>Your saved work stays in your account.</p><Button onClick={() => window.location.reload()}>Reload the page</Button></div> : this.props.children; }
}
function Workspace() {
 const [user, setUser] = useState(null), [catalog, setCatalog] = useState(null), [ready, setReady] = useState(false), [error, setError] = useState('');
 const navigate = useNavigate();
 useEffect(() => { api('/auth/me').then(d => setUser(d.user)).catch(e => { if (e.status !== 401) setError(e.message); }).finally(() => setReady(true)); }, []);
 useEffect(() => { if (user) api('/catalog').then(setCatalog).catch(e => setError(e.message)); }, [user?.id]);
 async function logout() { try { await api('/auth/logout', { method: 'POST' }); setUser(null); setCatalog(null); navigate('/'); } catch (e) { setError(e.message); } }
 if (!ready) return <Loading />;
 if (!user) return <><Alert>{error}</Alert><Auth onLogin={u => { setUser(u); setError(''); navigate('/analyzer'); }} /></>;
 return <><Alert>{error}</Alert><Routes><Route element={<Layout user={user} logout={logout} />}>
 <Route path="/analyzer/:id?" element={<Analyzer catalog={catalog} />} />
 <Route path="/builder/:id?" element={<Builder user={user} />} />
 <Route path="/interview/:id?" element={<Interview catalog={catalog} />} />
 <Route path="/assessments/:id?" element={<Assessments catalog={catalog} />} />
 <Route path="/coding/:id?" element={<Coding catalog={catalog} />} />
 <Route path="/leaderboard" element={<Leaderboard user={user} setUser={setUser} />} />
 <Route path="/progress" element={<Progress onDeleted={() => { setUser(null); navigate('/'); }} />} />
 <Route path="*" element={<Navigate to="/analyzer" replace />} />
 </Route></Routes></>;
}
export default function App() { return <ErrorBoundary><BrowserRouter><Workspace /></BrowserRouter></ErrorBoundary>; }
