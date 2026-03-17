import { NextRequest, NextResponse } from 'next/server';
import { getCaseById, updateCase } from '@/lib/storage';

export async function POST(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  
  try {
    const caseData = await getCaseById(id);
    if (!caseData) {
      return NextResponse.json({ error: 'Case not found' }, { status: 404 });
    }

    // Update the case status to closed
    const updatedCase = await updateCase(id, {
      status: 'closed'
    });

    return NextResponse.json(updatedCase);
  } catch (error) {
    console.error('API Error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
