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
      <div className="grid grid-cols-1 lg:grid-cols-1 gap-8">
        {/* Recent Incidents List - REAL DATA */}
        <div className="flex flex-col gap-4">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-xl font-bold tracking-tight text-foreground">Reported Payment Incidents</h3>
            <button 
              onClick={() => setIsModalOpen(true)}
              className="text-sm px-4 py-2 rounded-lg bg-primary text-white font-bold shadow-lg shadow-primary/10 hover:scale-[1.02] transition-all"
            >
              Report New Case
            </button>
          </div>
          
          <div className="flex flex-col gap-3">
            {loading ? (
              <p className="text-muted-foreground animate-pulse text-center py-10">Loading cases...</p>
            ) : cases.length > 0 ? (
              cases.map((c) => (
                <IncidentItem 
                  key={c.id}
                  id={c.id} 
                  title={c.title} 
                  status={c.status}
                  agent="User Reported"
                  severity={c.severity}
                />
              ))
            ) : (
              <div className="p-10 border border-dashed border-border rounded-3xl text-center">
                <p className="text-muted-foreground">No incidents reported yet.</p>
                <button 
                  onClick={() => setIsModalOpen(true)}
                  className="mt-4 text-primary hover:underline font-bold"
                >
                  Create the first one
                </button>
              </div>
            )}
          </div>
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
