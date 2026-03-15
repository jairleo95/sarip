import fs from 'fs/promises';
import path from 'path';

const STORAGE_PATH = path.join(process.cwd(), 'data', 'cases.json');

export interface Case {
  id: string;
  title: string;
  description: string;
  severity: 'low' | 'medium' | 'high';
  status: 'reported' | 'investigating' | 'resolved';
  createdAt: string;
}

export async function initStorage() {
  const dir = path.dirname(STORAGE_PATH);
  try {
    await fs.access(dir);
  } catch {
    await fs.mkdir(dir, { recursive: true });
  }

  try {
    await fs.access(STORAGE_PATH);
  } catch {
    await fs.writeFile(STORAGE_PATH, JSON.stringify([], null, 2));
  }
}

export async function getCases(): Promise<Case[]> {
  await initStorage();
  const data = await fs.readFile(STORAGE_PATH, 'utf-8');
  return JSON.parse(data);
}

export async function getCaseById(id: string): Promise<Case | null> {
  const cases = await getCases();
  return cases.find(c => c.id === id) || null;
}

export async function saveCase(newCase: Case): Promise<Case> {
  const cases = await getCases();
  cases.push(newCase);
  await fs.writeFile(STORAGE_PATH, JSON.stringify(cases, null, 2));
  return newCase;
}
