'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function DocumentButton({ caseId }: { caseId: string }) {
  const [documenting, setDocumenting] = useState(false);
  const router = useRouter();

  const handleDocument = async () => {
    setDocumenting(true);
    try {
      const res = await fetch(`/api/cases/${caseId}/document`, {
        method: 'POST',
      });
      
      if (res.ok) {
        // Force refresh to grab new data
        router.refresh();
      } else {
        console.error("Documentation failed");
        alert("Failed to send case to documentation.");
      }
    } catch (error) {
      console.error(error);
      alert("Error contacting the server.");
    } finally {
      setDocumenting(false);
    }
  };

  return (
    <button 
      onClick={handleDocument} 
      disabled={documenting}
      className={`relative overflow-hidden group px-6 py-2 rounded-xl font-bold transition-all shadow-lg text-sm flex items-center gap-2 ${
        documenting 
          ? 'bg-purple-600/50 text-white/50 cursor-wait' 
          : 'bg-purple-600/20 text-purple-400 border border-purple-500/30 hover:bg-purple-600 hover:text-white hover:scale-[1.02]'
      }`}
    >
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
      </svg>
      {documenting ? 'Exporting...' : 'Send to Playbooks'}
    </button>
  );
}
