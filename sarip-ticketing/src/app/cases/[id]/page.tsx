import { getCaseById } from '@/lib/storage';
import Link from 'next/link';
import AnalyzeButton from '@/components/AnalyzeButton';
import ApproveButton from '@/components/ApproveButton';
import DocumentButton from '@/components/DocumentButton';
import DeepResearchButton from '@/components/DeepResearchButton';

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
            <span className={`px-3 py-1 rounded-full text-xs uppercase font-bold border ${severityColors[caseData.severity as keyof typeof severityColors] || ''}`}>
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
          <div className={`text-sm font-semibold flex items-center gap-2 px-4 py-2 rounded-lg border capitalize ${
            caseData.status === 'closed' || caseData.status === 'documented'
              ? 'bg-green-500/10 text-green-500 border-green-500/20' 
              : 'bg-secondary/50 border-border'
          }`}>
            {(caseData.status !== 'closed' && caseData.status !== 'documented') && (
              <span className="w-2 h-2 rounded-full bg-blue-400 animate-pulse shadow-[0_0_8px_rgba(96,165,250,0.6)]" />
            )}
            {(caseData.status === 'closed' || caseData.status === 'documented') && (
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            )}
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
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
            <h3 className="text-sm font-bold text-muted-foreground uppercase tracking-wider flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-primary shadow-[0_0_8px_rgba(var(--primary),0.6)]" />
              SARIP AI Analysis
            </h3>
            
            {caseData.status !== 'documented' && (
              <div className="flex items-center gap-3">
                {(caseData.status === 'resolved' || caseData.status === 'closed') && (
                  <DocumentButton caseId={caseData.id} />
                )}
                {caseData.status === 'resolved' && (
                  <ApproveButton caseId={caseData.id} />
                )}
                {caseData.status !== 'closed' && (
                  <AnalyzeButton caseId={caseData.id} isRetry={!!caseData.analysis} />
                )}
              </div>
            )}
          </div>
          
          {!caseData.analysis ? (
            <div className="p-8 border border-dashed border-border rounded-2xl text-center bg-secondary/10 flex flex-col items-center justify-center gap-4">
              <div className="w-12 h-12 rounded-full bg-secondary flex items-center justify-center">
                <svg className="w-6 h-6 text-muted-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
                </svg>
              </div>
              <div>
                <p className="font-bold text-lg mb-1">Awaiting AI Investigation</p>
                <p className="text-muted-foreground text-sm max-w-md mx-auto">
                  SARIP engine has not analyzed this ticket yet. Click the button above to trigger the LangGraph orchestration.
                </p>
              </div>
              
              {/* L3 Fallback Planner ONLY IF HIGH RISK OR UNKNOWN */}
              {caseData.analysis && ((caseData.analysis as any).requiresHumanApproval || (caseData.analysis as any).failureMode === 'UNKNOWN_ERROR_REQUIRES_HUMAN' || (caseData.analysis as any).failureMode === 'UNKNOWN' || (caseData.analysis as any).confidenceScore < 0.9) && (
                 <DeepResearchButton caseId={caseData.id} context={caseData.description} />
              )}
            </div>
          ) : (
            <div className="flex flex-col gap-6 animate-in fade-in zoom-in-95 duration-500">
              
              {/* Top Result Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="p-5 rounded-2xl border border-border bg-gradient-to-br from-secondary/40 to-background flex flex-col gap-2 relative overflow-hidden">
                  <div className="absolute top-0 right-0 w-24 h-24 bg-red-500/5 blur-2xl rounded-full" />
                  <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Failure Mode</span>
                  <span className="text-xl font-black text-foreground">{caseData.analysis.failureMode || 'UNKNOWN'}</span>
                </div>
                
                <div className="p-5 rounded-2xl border border-border bg-gradient-to-br from-secondary/40 to-background flex flex-col gap-2 relative overflow-hidden">
                  <div className="absolute top-0 right-0 w-24 h-24 bg-primary/5 blur-2xl rounded-full" />
                  <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider">RCA Action</span>
                  <span className="text-xl font-black text-primary">{caseData.analysis.recommendedAction || 'N/A'}</span>
                </div>
                
                <div className="p-5 rounded-2xl border border-border bg-gradient-to-br from-secondary/40 to-background flex flex-col gap-2 relative overflow-hidden">
                  <div className="absolute top-0 right-0 w-24 h-24 bg-green-500/5 blur-2xl rounded-full" />
                  <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Confidence Score</span>
                  <div className="flex items-center gap-3">
                    <span className="text-2xl font-black text-foreground">
                      {caseData.analysis.confidenceScore ? `${(caseData.analysis.confidenceScore * 100).toFixed(0)}%` : 'N/A'}
                    </span>
                    {caseData.analysis.requiresHumanApproval && (
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-primary/20 text-primary border border-primary/30 uppercase">
                        Needs Human
                      </span>
                    )}
                  </div>
                </div>
              </div>
              
              {/* Technical Context */}
              <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-6">
                {caseData.analysis.dbContext && Object.keys(caseData.analysis.dbContext).length > 0 && (
                  <div>
                    <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-4 border-b border-border pb-2 flex items-center gap-2">
                      <svg className="w-4 h-4 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2 1.5 3 3 3h10c1.5 0 3-1 3-3V7c0-2-1.5-3-3-3H7C5.5 4 4 5 4 7zM4 11h16M8 15h4" />
                      </svg>
                      Database Records
                    </h4>
                    <pre className="text-xs text-blue-300 font-mono leading-relaxed bg-[#0d1117] p-4 rounded-xl border border-blue-500/20 overflow-x-auto shadow-inner max-h-64 overflow-y-auto">
                      {JSON.stringify(caseData.analysis.dbContext, null, 2)}
                    </pre>
                  </div>
                )}
                
                {caseData.analysis.traceContext && caseData.analysis.traceContext.length > 0 && (
                  <div>
                    <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-4 border-b border-border pb-2 flex items-center gap-2">
                      <svg className="w-4 h-4 text-orange-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      System Logs (Traces)
                    </h4>
                    <pre className="text-xs text-orange-300 font-mono leading-relaxed bg-[#0d1117] p-4 rounded-xl border border-orange-500/20 overflow-x-auto shadow-inner max-h-64 overflow-y-auto">
                      {JSON.stringify(caseData.analysis.traceContext, null, 2)}
                    </pre>
                  </div>
                )}
              </div>

              {/* Timeline */}
              <div className="mt-4">
                <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-4 border-b border-border pb-2">Investigation Trail</h4>
                <div className="flex flex-col gap-3">
                  {caseData.analysis.auditTrail && caseData.analysis.auditTrail.length > 0 ? (
                    caseData.analysis.auditTrail.map((msg: any, idx: number) => {
                      const msgText = typeof msg === 'string' ? msg : JSON.stringify(msg, null, 2);
                      return (
                        <div key={idx} className="flex gap-4 items-start">
                          <div className="w-6 h-6 rounded-full bg-secondary flex items-center justify-center shrink-0 border border-border mt-0.5">
                            <span className="text-[10px] text-muted-foreground font-mono">{idx + 1}</span>
                          </div>
                          <pre className="text-sm text-foreground/80 font-mono leading-relaxed bg-secondary/20 px-4 py-2 rounded-xl flex-1 border border-white/5 whitespace-pre-wrap overflow-x-auto">
                            {msgText}
                          </pre>
                        </div>
                      );
                    })
                  ) : (
                    <p className="text-sm text-muted-foreground italic">No audit trail recorded.</p>
                  )}
                </div>
              </div>
              
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
