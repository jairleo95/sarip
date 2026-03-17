'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function AnalyzeButton({ caseId, isRetry = false }: { caseId: string, isRetry?: boolean }) {
  const [analyzing, setAnalyzing] = useState(false);
  const router = useRouter();

  const handleAnalyze = async () => {
    setAnalyzing(true);
    try {
      const res = await fetch(`/api/cases/${caseId}/analyze`, {
        method: 'POST',
      });
      
      if (res.ok) {
        // Force refresh to grab new data with the analysis
        router.refresh();
      } else {
        console.error("Analysis failed");
        alert("Failed to analyze ticket.");
      }
    } catch (error) {
      console.error(error);
      alert("Error contacting the server.");
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <button 
      onClick={handleAnalyze} 
      disabled={analyzing}
      className={`relative overflow-hidden group px-6 py-3 rounded-xl font-bold transition-all shadow-lg ${
        analyzing 
          ? 'bg-secondary text-muted-foreground cursor-wait' 
          : isRetry
            ? 'bg-secondary text-foreground border border-border hover:bg-secondary/80 hover:scale-[1.02]'
            : 'bg-primary text-white shadow-primary/20 hover:scale-[1.02]'
      }`}
    >
      {/* Shine effect */}
      {!analyzing && !isRetry && (
        <div className="absolute inset-0 -translate-x-full group-hover:animate-[shimmer_1.5s_infinite] bg-gradient-to-r from-transparent via-white/20 to-transparent z-10" />
      )}
      
      <span className="flex items-center gap-2 relative z-20">
        {analyzing ? (
          <>
            <svg className="animate-spin -ml-1 mr-2 h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Re-investigating...
          </>
        ) : isRetry ? (
          <>
            <svg className="w-4 h-4 text-muted-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Re-Analyze
          </>
        ) : (
          <>
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            Analyze with SARIP AI
          </>
        )}
      </span>
    </button>
  );
}
