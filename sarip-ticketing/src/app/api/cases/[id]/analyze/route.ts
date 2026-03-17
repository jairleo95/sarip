import { NextRequest, NextResponse } from 'next/server';
import { getCaseById, updateCase } from '@/lib/storage';

export async function POST(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  
  try {
    const caseData = await getCaseById(id);
    if (!caseData) {
      return NextResponse.json({ error: 'Case not found' }, { status: 404 });
    }

    // Call local FastAPI LangGraph server
    const response = await fetch('http://localhost:8000/analyze', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        ticket_id: caseData.id,
        description: caseData.description,
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error("LangGraph API error:", errorText);
      return NextResponse.json({ error: 'LangGraph analysis failed' }, { status: response.status });
    }

    const analysisData = await response.json();

    // Update the case with the AI findings
    const updatedCase = await updateCase(id, {
      status: 'resolved',
      analysis: {
        failureMode: analysisData.failure_mode,
        recommendedAction: analysisData.recommended_action,
        confidenceScore: analysisData.confidence_score,
        requiresHumanApproval: analysisData.requires_human_approval,
        auditTrail: analysisData.audit_trail,
        dbContext: analysisData.db_context,
        traceContext: analysisData.trace_context
      }
    });

    return NextResponse.json(updatedCase);
  } catch (error) {
    console.error('API Error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
