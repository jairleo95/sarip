import { NextRequest, NextResponse } from 'next/server';
import { getCaseById, updateCase } from '@/lib/storage';

export async function POST(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  
  try {
    const caseData = await getCaseById(id);
    if (!caseData || !caseData.analysis) {
      return NextResponse.json({ error: 'Case not found or not analyzed' }, { status: 404 });
    }

    // Prepare data directly from the case's saved AI analysis
    const payload = {
      ticket_id: caseData.id,
      company_name: "Extract_From_Router", // Simplification for UI demo
      description: caseData.description,
      failure_mode: caseData.analysis.failureMode || "UNKNOWN",
      recommended_action: caseData.analysis.recommendedAction || "UNKNOWN",
      db_context: caseData.analysis.dbContext || {},
      trace_context: caseData.analysis.traceContext || []
    };

    // Call local FastAPI LangGraph server to generate the markdown file
    const response = await fetch('http://localhost:8000/document_case', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error("Documentation API error:", errorText);
      return NextResponse.json({ error: 'Documentation generation failed' }, { status: response.status });
    }

    // Update the case status to documented
    const updatedCase = await updateCase(id, {
      status: 'documented'
    });

    return NextResponse.json(updatedCase);
  } catch (error) {
    console.error('API Error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
