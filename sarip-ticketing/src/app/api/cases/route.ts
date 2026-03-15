import { NextResponse } from 'next/server';
import { getCases, saveCase, Case } from '@/lib/storage';

export async function GET() {
  try {
    const cases = await getCases();
    return NextResponse.json(cases);
  } catch (error) {
    return NextResponse.json({ error: 'Failed to fetch cases' }, { status: 500 });
  }
}

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const newCase: Case = {
      id: `TCK-${Math.floor(Math.random() * 90000) + 10000}`,
      title: body.title,
      description: body.description,
      severity: body.severity || 'medium',
      status: 'reported',
      createdAt: new Date().toISOString(),
    };

    await saveCase(newCase);
    return NextResponse.json(newCase);
  } catch (error) {
    return NextResponse.json({ error: 'Failed to save case' }, { status: 500 });
  }
}
