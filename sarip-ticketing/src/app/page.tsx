'use client';

import { useState, useEffect } from 'react';
import ReportCaseModal from '@/components/ReportCaseModal';
import Link from 'next/link';

interface Case {
  id: string;
  title: string;
  description: string;
  severity: 'low' | 'medium' | 'high';
  status: string;
  agent?: string;
}

export default function Home() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [cases, setCases] = useState<Case[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'pending' | 'resolved' | 'documented'>('pending');

  const fetchCases = async () => {
    try {
      const res = await fetch('/api/cases');
      if (res.ok) {
        const data = await res.json();
        setCases(data);
      }
    } catch (error) {
      console.error('Failed to fetch cases:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCases();
  }, []);

  return (
    <div className="flex flex-col gap-10 max-w-7xl animate-in fade-in duration-700">

      {/* Main Grid */}
      <div className="flex flex-col gap-6">
        
        {/* Header Options */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          {/* Tab Navigation */}
          <div className="flex bg-secondary/50 p-1 rounded-xl border border-border w-full sm:w-auto">
            <button
              onClick={() => setActiveTab('pending')}
              className={`flex-1 sm:flex-none px-6 py-2.5 rounded-lg font-bold text-sm transition-all ${
                activeTab === 'pending' ? 'bg-background shadow-md text-primary' : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              <div className="flex items-center gap-2 justify-center">
                <span className={`w-2 h-2 rounded-full ${activeTab === 'pending' ? 'bg-blue-500 animate-pulse' : 'bg-muted'}`}></span>
                Pending
                <span className="ml-1 bg-muted px-2 py-0.5 rounded-full text-xs">{cases.filter(c => c.status !== 'resolved' && c.status !== 'closed' && c.status !== 'documented').length}</span>
              </div>
            </button>
            <button
              onClick={() => setActiveTab('resolved')}
              className={`flex-1 sm:flex-none px-6 py-2.5 rounded-lg font-bold text-sm transition-all ${
                activeTab === 'resolved' ? 'bg-background shadow-md text-primary' : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              <div className="flex items-center gap-2 justify-center">
                <span className={`w-2 h-2 rounded-full ${activeTab === 'resolved' ? 'bg-green-500' : 'bg-muted'}`}></span>
                Resolved
                <span className="ml-1 bg-muted px-2 py-0.5 rounded-full text-xs">{cases.filter(c => c.status === 'resolved' || c.status === 'closed').length}</span>
              </div>
            </button>
            <button
              onClick={() => setActiveTab('documented')}
              className={`flex-1 sm:flex-none px-6 py-2.5 rounded-lg font-bold text-sm transition-all ${
                activeTab === 'documented' ? 'bg-background shadow-md text-primary' : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              <div className="flex items-center gap-2 justify-center">
                <span className={`w-2 h-2 rounded-full ${activeTab === 'documented' ? 'bg-purple-500' : 'bg-muted'}`}></span>
                Playbooks
                <span className="ml-1 bg-muted px-2 py-0.5 rounded-full text-xs">{cases.filter(c => c.status === 'documented').length}</span>
              </div>
            </button>
          </div>

          <button 
            onClick={() => setIsModalOpen(true)}
            className="w-full sm:w-auto text-sm px-6 py-2.5 rounded-xl bg-primary text-white font-bold shadow-lg shadow-primary/20 hover:scale-[1.02] transition-all flex items-center justify-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M12 4v16m8-8H4" />
            </svg>
            Report Case
          </button>
        </div>

        {/* TAB CONTENTS */}
        <div className="grid grid-cols-1 lg:grid-cols-1 gap-8 mt-2">
          
          {/* PENDING TICKETS */}
          {activeTab === 'pending' && (
            <div className="flex flex-col gap-3 animate-in fade-in duration-300 slide-in-from-bottom-2">
              {loading ? (
                <p className="text-muted-foreground animate-pulse text-center py-10">Loading cases...</p>
              ) : cases.filter(c => c.status !== 'resolved' && c.status !== 'closed' && c.status !== 'documented').length > 0 ? (
                cases.filter(c => c.status !== 'resolved' && c.status !== 'closed' && c.status !== 'documented').map((c) => (
                  <IncidentItem key={c.id} id={c.id} title={c.title} status={c.status} agent="User Reported" severity={c.severity} />
                ))
              ) : (
                <div className="p-12 border border-dashed border-border rounded-3xl text-center glass-morphism flex flex-col items-center gap-3">
                  <div className="w-12 h-12 rounded-full bg-secondary flex items-center justify-center">
                    <svg className="w-6 h-6 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                  </div>
                  <p className="text-muted-foreground font-medium">All caught up. No pending incidents.</p>
                </div>
              )}
            </div>
          )}

          {/* RESOLVED / CLOSED TICKETS */}
          {activeTab === 'resolved' && (
            <div className="flex flex-col gap-3 animate-in fade-in duration-300 slide-in-from-bottom-2">
              {loading ? (
                <p className="text-muted-foreground animate-pulse text-center py-10">Loading cases...</p>
              ) : cases.filter(c => c.status === 'resolved' || c.status === 'closed').length > 0 ? (
                cases.filter(c => c.status === 'resolved' || c.status === 'closed').map((c) => (
                  <IncidentItem key={c.id} id={c.id} title={c.title} status={c.status} agent="AI Agent" severity={c.severity} />
                ))
              ) : (
                <div className="p-12 border border-dashed border-border rounded-3xl text-center glass-morphism flex flex-col items-center gap-3">
                  <div className="w-12 h-12 rounded-full bg-secondary flex items-center justify-center">
                    <svg className="w-6 h-6 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                  </div>
                  <p className="text-muted-foreground font-medium">No resolved incidents yet.</p>
                </div>
              )}
            </div>
          )}

          {/* DOCUMENTED TICKETS */}
          {activeTab === 'documented' && (
            <div className="flex flex-col gap-3 animate-in fade-in duration-300 slide-in-from-bottom-2">
              {loading ? (
                <p className="text-muted-foreground animate-pulse text-center py-10">Loading cases...</p>
              ) : cases.filter(c => c.status === 'documented').length > 0 ? (
                cases.filter(c => c.status === 'documented').map((c) => (
                  <IncidentItem key={c.id} id={c.id} title={c.title} status={c.status} agent="AI Agent" severity={c.severity} />
                ))
              ) : (
                <div className="p-12 border border-dashed border-border rounded-3xl text-center glass-morphism flex flex-col items-center gap-3">
                  <div className="w-12 h-12 rounded-full bg-secondary flex items-center justify-center">
                    <svg className="w-6 h-6 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"></path></svg>
                  </div>
                  <p className="text-muted-foreground font-medium">No playbooks generated yet.</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      <ReportCaseModal 
        isOpen={isModalOpen} 
        onClose={() => setIsModalOpen(false)} 
        onSuccess={fetchCases}
      />
    </div>
  );
}

function IncidentItem({ id, title, status, agent, severity }: { id: string; title: string; status: string; agent: string; severity: 'low' | 'medium' | 'high' }) {
  const severityColors = {
    low: "bg-green-500/10 text-green-500 border-green-500/20",
    medium: "bg-amber-500/10 text-amber-500 border-amber-500/20",
    high: "bg-red-500/10 text-red-500 border-red-500/20",
  };

  return (
    <Link href={`/cases/${id}`} className="p-5 rounded-2xl border border-border glass-morphism flex items-center justify-between card-hover group cursor-pointer block">
      <div className="flex flex-col gap-1">
        <div className="flex items-center gap-3">
          <span className="text-xs font-mono font-bold text-muted-foreground">{id}</span>
          <span className={`px-2 py-0.5 rounded-full text-[10px] uppercase font-bold border ${severityColors[severity]}`}>
            {severity}
          </span>
        </div>
        <h4 className="font-bold text-foreground group-hover:text-primary transition-colors">{title}</h4>
      </div>
      
      <div className="flex items-center gap-6 text-right">
        <div className="hidden sm:flex flex-col gap-0.5">
          <p className="text-xs text-muted-foreground font-medium">{agent}</p>
          <div className="text-sm font-semibold flex items-center gap-2 justify-end capitalize">
            <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse" />
            {status}
          </div>
        </div>
        <div className="w-8 h-8 rounded-full bg-secondary flex items-center justify-center border border-border group-hover:bg-primary/10 group-hover:border-primary/30 transition-all">
          <svg className="w-4 h-4 text-muted-foreground group-hover:text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M9 5l7 7-7 7" />
          </svg>
        </div>
      </div>
    </Link>
  );
}
