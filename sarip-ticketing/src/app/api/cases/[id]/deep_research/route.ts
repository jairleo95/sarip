import { NextResponse } from 'next/server';

export async function POST(
  request: Request,
  { params }: { params: { id: string } }
) {
  try {
    const body = await request.json();
    
    // Call the LangGraph FastAPI Orchestrator endpoint for Deep Research
    const response = await fetch('http://localhost:8000/deep_research', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ticket_context: body.context || `Investigate case ${params.id}`
      }),
    });

    if (!response.ok) {
        throw new Error("L3 Planner API Failed");
    }
    
    const data = await response.json();
    
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json({ error: 'Failed to run L3 investigation' }, { status: 500 });
  }
}
