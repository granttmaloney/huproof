import { startCapture, computeFeatureVector } from './keystrokes';
import { generateProof } from './prover';
import { foldCommitment, foldKey, computeSig, toBigIntDecimal } from './zk';
import { saveTemplate, getTemplate } from './storage';

const app = document.getElementById('app')!;
app.innerHTML = `
  <h1>huproof demo</h1>
  <div>
    <button id="enroll">Enroll Start</button>
    <button id="login">Login Start</button>
  </div>
  <p id="challenge"></p>
  <input id="input" autocomplete="off" spellcheck="false" />
  <pre id="out"></pre>
`;

async function api(path: string, opts?: RequestInit) {
  const res = await fetch(`http://127.0.0.1:8000${path}`, {
    ...opts,
    headers: { 'Content-Type': 'application/json', ...(opts?.headers || {}) },
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

let current: any = null;
let stop: (() => any) | null = null;

let userId: string | null = null;

async function start(kind: 'enroll' | 'login') {
  const path = kind === 'enroll' ? '/api/enroll/start' : `/api/login/start?user_id=${encodeURIComponent(userId || '')}`;
  current = await api(path);
  (document.getElementById('challenge') as HTMLElement).innerText = current.challenge;
  const input = document.getElementById('input') as HTMLInputElement;
  input.value = '';
  if (stop) stop();
  const capturer = startCapture(input);
  stop = () => capturer.stop();
}

document.getElementById('enroll')!.addEventListener('click', () => start('enroll'));
document.getElementById('login')!.addEventListener('click', () => start('login'));

document.getElementById('input')!.addEventListener('keydown', async (e) => {
  if (e.key !== 'Enter' || !current) return;
  const { events } = (stop as any)();
  const features = computeFeatureVector(current.challenge, events, 64);
  const out = document.getElementById('out') as HTMLPreElement;

  let templateVec = features.slice();
  let salt = BigInt(Math.floor(Math.random() * 1e9) + 1);
  let saltKey = BigInt(Math.floor(Math.random() * 1e9) + 2);
  let C = foldCommitment(templateVec, salt);
  let keyHash = foldKey(templateVec, saltKey);

  // If logging in, load stored template/salts
  if (current.commitment && userId) {
    const rec = getTemplate(userId);
    if (!rec) {
      (document.getElementById('out') as HTMLPreElement).textContent = 'No local template found; enroll first.';
      return;
    }
    templateVec = rec.template;
    salt = BigInt(rec.salt);
    saltKey = BigInt(rec.saltKey);
    C = BigInt(rec.commitment);
    keyHash = foldKey(templateVec, saltKey);
  }

  // Note: proper BigInt mapping for nonce/origin pending; demo uses zeros
  const nonceField = BigInt(0);
  const originField = BigInt(0);
  const tsField = BigInt(current.timestamp);
  const tauField = BigInt(current.tau);
  const sig = computeSig(nonceField, originField, tsField, keyHash);

  const inputs: any = {
    C: toBigIntDecimal(C),
    nonce: toBigIntDecimal(nonceField),
    origin_hash: toBigIntDecimal(originField),
    timestamp: toBigIntDecimal(tsField),
    tau: toBigIntDecimal(tauField),
    sig: toBigIntDecimal(sig),
    tmpl: templateVec.map((x) => x.toString()),
    features: features.map((x) => x.toString()),
    salt: toBigIntDecimal(salt),
    salt_key: toBigIntDecimal(saltKey),
  };

  let proof: any = { pi_a: [], pi_b: [], pi_c: [] };
  try {
    const wasm = '/artifacts/keystroke_js/keystroke.wasm';
    const zkey = '/artifacts/keystroke_final.zkey';
    const res = await generateProof(inputs, wasm, zkey);
    proof = res.proof;
  } catch {
    // Requires backend BYPASS_ZK_VERIFY=1
  }

  if (current.commitment) {
    const payload = {
      public_inputs: {
        nonce: current.nonce,
        origin_hash: current.origin_hash,
        tau: current.tau,
        timestamp: current.timestamp,
        C: toBigIntDecimal(C),
        sig: toBigIntDecimal(sig),
      },
      proof,
    };
    const rf = await api('/api/login/finish', { method: 'POST', body: JSON.stringify(payload) });
    out.textContent = JSON.stringify(rf, null, 2);
  } else {
    const payload = {
      commitment: toBigIntDecimal(C),
      public_inputs: {
        nonce: current.nonce,
        origin_hash: current.origin_hash,
        tau: current.tau,
        timestamp: current.timestamp,
        C: toBigIntDecimal(C),
        sig: toBigIntDecimal(sig),
      },
      proof,
    };
    const rf = await api('/api/enroll/finish', { method: 'POST', body: JSON.stringify(payload) });
    userId = rf.user_id;
    saveTemplate(userId, {
      template: features,
      salt: toBigIntDecimal(salt),
      saltKey: toBigIntDecimal(saltKey),
      commitment: toBigIntDecimal(C),
    });
    out.textContent = JSON.stringify(rf, null, 2);
  }
});


