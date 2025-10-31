type TemplateRecord = {
  template: number[];
  salt: string; // decimal string
  saltKey: string; // decimal string
  commitment: string; // decimal string
};

const KEY = 'huproof.templates.v1';

function loadAll(): Record<string, TemplateRecord> {
  try {
    return JSON.parse(localStorage.getItem(KEY) || '{}');
  } catch {
    return {};
  }
}

function saveAll(data: Record<string, TemplateRecord>) {
  localStorage.setItem(KEY, JSON.stringify(data));
}

export function saveTemplate(userId: string, rec: TemplateRecord) {
  const all = loadAll();
  all[userId] = rec;
  saveAll(all);
}

export function getTemplate(userId: string): TemplateRecord | null {
  const all = loadAll();
  return all[userId] || null;
}


