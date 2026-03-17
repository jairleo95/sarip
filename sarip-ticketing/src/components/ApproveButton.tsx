'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function ApproveButton({ caseId }: { caseId: string }) {
  const [closing, setClosing] = useState(false);
  const router = useRouter();

  const handleClose = async () => {
    setClosing(true);
    try {
      const res = await fetch(`/api/cases/${caseId}/close`, {
        method: 'POST',
      });
      
      if (res.ok) {
        // Force refresh to grab new data
        router.refresh();
      } else {
        console.error("Closure failed");
        alert("Failed to mark ticket as resolved.");
      }
    } catch (error) {
      console.error(error);
      alert("Error contacting the server.");
    } finally {
      setClosing(false);
    }
  };

  return (
    <button 
      onClick={handleClose} 
      disabled={closing}
      className={`relative overflow-hidden group px-6 py-2 rounded-xl font-bold transition-all shadow-lg text-sm flex items-center gap-2 ${
        closing 
          ? 'bg-green-600/50 text-white/50 cursor-wait' 
          : 'bg-green-600/20 text-green-500 border border-green-500/30 hover:bg-green-600 hover:text-white hover:scale-[1.02]'
      }`}
    >
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
      </svg>
      {closing ? 'Processing...' : 'Mark as Resolved (AI Approved)'}
    </button>
  );
}
