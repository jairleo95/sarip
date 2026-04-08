'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function DeepResearchButton({ caseId, context }: { caseId: string, context: string }) {
  const [isResearching, setIsResearching] = useState(false);
  const [report, setReport] = useState<string | null>(null);
  const router = useRouter();

  const handleDeepResearch = async () => {
    setIsResearching(true);
    setReport(null);
    try {
      const res = await fetch(`/api/cases/${caseId}/deep_research`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ context })
      });
      
      if (!res.ok) throw new Error('Research failed');
      
      const data = await res.json();
      setReport(data.report);
      router.refresh(); 
    } catch (error) {
      console.error(error);
      alert('Error ejecutando Investigador L3');
    } finally {
      setIsResearching(false);
    }
  };

  return (
    <div className="flex flex-col gap-4 mt-8 pt-8 border-t border-border animate-in fade-in duration-700">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
         <div>
            <h4 className="font-bold text-foreground text-lg">Escalamiento Forense Nivel 3 (L3)</h4>
            <p className="text-sm text-muted-foreground mt-1 max-w-lg">
               El pipeline determinista requiere ayuda. Usa el Agente Planificador autónomo para revisar código fuente (Java) y 
               ejecutar SQL dinámicamente. Esto tardará varios minutos.
            </p>
         </div>
        <button
          onClick={handleDeepResearch}
          disabled={isResearching}
          className="px-6 py-3 rounded-xl font-bold transition-all flex items-center gap-2 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white shadow-[0_0_20px_rgba(147,51,234,0.3)] disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
        >
          {isResearching ? (
            <>
              <svg className="animate-spin -ml-1 mr-2 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Planificando y Ejecutando...
            </>
          ) : (
            <>
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
              </svg>
              Investigar con IA L3
            </>
          )}
        </button>
      </div>

      {report && (
         <div className="p-6 bg-secondary/10 rounded-2xl border border-purple-500/30 font-mono text-sm whitespace-pre-wrap mt-4 shadow-inner">
            <h5 className="font-bold text-purple-400 mb-4 border-b border-purple-500/30 pb-2 uppercase tracking-widest flex items-center gap-2">
               <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                 <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
               </svg>
               L3 Forensic Report 
            </h5>
            <div className="text-muted-foreground leading-relaxed">
              {report}
            </div>
         </div>
      )}
    </div>
  );
}
