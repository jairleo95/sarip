import { getCaseById } from '@/lib/storage';
import Link from 'next/link';

export default async function CaseDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = await params;
  const caseData = await getCaseById(resolvedParams.id);

  if (!caseData) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh] animate-in fade-in duration-700">
        <h2 className="text-2xl font-bold mb-4">Case Not Found</h2>
        <p className="text-muted-foreground mb-8">The requested incident could not be found in the system.</p>
        <Link href="/" className="px-6 py-3 bg-secondary rounded-xl font-bold hover:bg-secondary/80 transition-all">
          Return to Dashboard
        </Link>
      </div>
    );
  }

  const severityColors = {
    low: "bg-green-500/10 text-green-500 border-green-500/20",
    medium: "bg-amber-500/10 text-amber-500 border-amber-500/20",
    high: "bg-red-500/10 text-red-500 border-red-500/20",
  };

  return (
    <div className="flex flex-col gap-8 max-w-4xl animate-in slide-in-from-bottom-8 duration-500">
      
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <Link href="/" className="text-sm font-medium text-muted-foreground hover:text-primary mb-4 inline-flex items-center gap-2 transition-colors">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            Back to Queue
          </Link>
          <div className="flex items-center gap-4 mt-2">
            <h1 className="text-3xl font-bold tracking-tight">{caseData.title}</h1>
            <span className={`px-3 py-1 rounded-full text-xs uppercase font-bold border ${severityColors[caseData.severity]}`}>
              {caseData.severity}
            </span>
          </div>
          <p className="text-muted-foreground font-mono mt-2 flex items-center gap-2">
            {caseData.id}
            <span className="w-1.5 h-1.5 rounded-full bg-border" />
            <span className="text-sm font-sans">Reported {new Date(caseData.createdAt).toLocaleString()}</span>
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          <div className="text-sm font-semibold flex items-center gap-2 px-4 py-2 rounded-lg bg-secondary/50 border border-border capitalize">
            <span className="w-2 h-2 rounded-full bg-blue-400 animate-pulse shadow-[0_0_8px_rgba(96,165,250,0.6)]" />
            {caseData.status}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="glass-morphism rounded-3xl border border-border overflow-hidden shadow-2xl">
        <div className="p-8 border-b border-border bg-secondary/10">
          <h3 className="text-sm font-bold text-muted-foreground uppercase tracking-wider mb-4">Incident Description</h3>
          <p className="text-lg leading-relaxed text-foreground whitespace-pre-wrap">
            {caseData.description}
          </p>
        </div>
        
        <div className="p-8 bg-background/50">
          <h3 className="text-sm font-bold text-muted-foreground uppercase tracking-wider mb-4 flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-primary" />
            Agent Analysis Timeline
          </h3>
          
          <div className="p-6 border border-dashed border-border rounded-2xl text-center bg-secondary/20">
            <p className="text-muted-foreground">
              LangGraph Agent execution is currently deferred. <br/>
              <span className="text-sm mt-2 inline-block">Once integrated, the resolution timeline and RCA will appear here.</span>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
