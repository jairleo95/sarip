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
      {/* Hero / Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard label="Reported Incidents" value={cases.length.toString()} change="Local Storage Active" />
        <StatCard label="System Status" value="Online" change="Ready for input" />
        <StatCard label="Avg. Resolution" value="N/A" change="Manual Mode" />
        <StatCard label="Savings (Est.)" value="$0.00" change="This Month" highlight />
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Recent Incidents List - REAL DATA */}
        <div className="lg:col-span-2 flex flex-col gap-4">
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

        {/* Sidebar / Assistant */}
        <div className="flex flex-col gap-6">
          <div className="glass-morphism p-6 rounded-2xl flex flex-col gap-4 border border-border shadow-xl">
            <h4 className="font-bold flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-blue-500 shadow-[0_0_8px_rgba(59,130,246,0.6)]" />
              Intelligence Notice
            </h4>
            <div className="bg-secondary/40 p-4 rounded-xl text-sm border border-white/5 space-y-3">
              <p className="text-muted-foreground leading-relaxed">
                Agent integration is currently <span className="text-foreground font-semibold">disabled</span> as per scope. This dashboard only stores and displays manual reports.
              </p>
            </div>
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

function StatCard({ label, value, change, highlight = false }: { label: string; value: string; change: string; highlight?: boolean }) {
  return (
    <div className={`p-6 rounded-2xl border border-border glass-morphism card-hover ${highlight ? "bg-primary/5 border-primary/20" : ""}`}>
      <p className="text-sm font-medium text-muted-foreground mb-1">{label}</p>
      <h3 className={`text-3xl font-bold tracking-tight mb-2 ${highlight ? "gradient-text" : "text-foreground"}`}>{value}</h3>
      <p className="text-xs font-semibold text-muted-foreground/80">{change}</p>
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
