import { NavLink, Link, Outlet, useLocation } from 'react-router-dom';
import { useState } from 'react';
import { Sparkles, FileSearch, FilePenLine, MessagesSquare, ClipboardCheck, CodeXml, ChartNoAxesCombined, Trophy, LogOut, Menu, X, Sprout, Plus } from 'lucide-react';
const groups = [
 ['YOUR RESUME', [['/analyzer', 'Resume analyzer', FileSearch], ['/builder', 'Resume builder', FilePenLine]]],
 ['YOUR PREPARATION', [['/interview', 'Interview practice', MessagesSquare], ['/assessments', 'Skill assessments', ClipboardCheck], ['/coding', 'Coding lab', CodeXml]]],
 ['YOUR GROWTH', [['/leaderboard', 'Leaderboard', Trophy], ['/progress', 'My progress', ChartNoAxesCombined]]],
];
export function Logo() { return <div className="brand"><div className="brand-mark"><Sparkles size={27} /></div><div><strong>Skillentra AI</strong><span>RESUME & SKILL STUDIO</span></div></div>; }
export default function Layout({ user, logout }) {
 const [open, setOpen] = useState(false);
 const location = useLocation();
 const current = groups.flatMap(g => g[1]).find(([path]) => location.pathname.startsWith(path))?.[1] || 'Workspace';
 return <div className="app-shell">
   {open && <button className="sidebar-backdrop" onClick={() => setOpen(false)} aria-label="Close navigation" />}
   <aside className={`sidebar ${open ? 'open' : ''}`}><Logo /><button className="icon-button mobile-close" onClick={() => setOpen(false)} aria-label="Close navigation"><X /></button>
     <nav aria-label="Main navigation">{groups.map(([title, links]) => <div className="nav-group" key={title}><p>{title}</p>{links.map(([path, title, Icon]) => <NavLink to={path} key={path} onClick={() => setOpen(false)}><Icon size={21} /><span>{title}</span></NavLink>)}</div>)}</nav>
     <div className="growth-note"><Sprout size={25} /><strong>Make room for growth.</strong><p>One focused session can move you forward.</p><Link to="/progress" onClick={() => setOpen(false)}>View your progress</Link></div>
     <div className="profile"><span className="initials">{user.full_name.split(' ').slice(0, 2).map(n => n[0]).join('').toUpperCase()}</span><div><strong>{user.full_name}</strong><small>{user.email}</small></div><button className="icon-button" onClick={logout} title="Sign out" aria-label="Sign out"><LogOut size={20} /></button></div>
   </aside>
   <div className="workspace"><header className="topbar"><button className="icon-button mobile-menu" aria-label="Open navigation" onClick={() => setOpen(true)}><Menu /></button><p><span>Workspace</span><span className="crumb">/</span><strong>{current}</strong></p><div><span className="hello">Hello, {user.full_name.split(' ')[0]}</span><Link className="button secondary" to="/builder"><Plus size={18} /> Create resume</Link></div></header><main id="main"><Outlet /></main><footer className="app-footer">Skillentra AI <span>Small steps. Stronger applications.</span></footer></div>
 </div>;
}
