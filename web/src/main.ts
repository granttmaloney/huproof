import { startCapture, computeFeatureVector } from './keystrokes';
import { generateProof } from './prover';
import { foldCommitment, foldKey, computeSig, toBigIntDecimal, hashStringToBigInt, hashHexToBigInt } from './zk';
import { saveTemplate, getTemplate } from './storage';

const app = document.getElementById('app')!;
app.innerHTML = `
  <h1>huproof demo</h1>
  <div>
    <button id="enroll">Enroll Start</button>
    <button id="login">Login Start</button>
    <button id="logout" style="display:none">Logout</button>
  </div>
  <div id="status" style="margin: 10px 0; font-weight: bold;"></div>
  <p id="challenge"></p>
  <input id="input" autocomplete="off" spellcheck="false" placeholder="Type the challenge above, then press Enter" />
  <div id="progress" style="display:none; margin: 10px 0;">
    <div>Generating proof...</div>
    <progress></progress>
  </div>
  <pre id="out"></pre>
`;

function setStatus(msg: string, isError = false) {
  const statusEl = document.getElementById('status') as HTMLElement;
  statusEl.textContent = msg;
  statusEl.style.color = isError ? 'red' : 'green';
}

function showProgress(show: boolean) {
  const progressEl = document.getElementById('progress') as HTMLElement;
  progressEl.style.display = show ? 'block' : 'none';
}

async function api(path: string, opts?: RequestInit) {
  try {
    const res = await fetch(`http://127.0.0.1:8000${path}`, {
      ...opts,
      headers: { 'Content-Type': 'application/json', ...(opts?.headers || {}) },
    });
    if (!res.ok) {
      const errorText = await res.text();
      let errorMsg = 'Request failed';
      try {
        const errorJson = JSON.parse(errorText);
        errorMsg = errorJson.detail || errorText;
      } catch {
        errorMsg = errorText || `HTTP ${res.status}`;
      }
      throw new Error(errorMsg);
    }
    return res.json();
  } catch (err: any) {
    setStatus(`Error: ${err.message}`, true);
    throw err;
  }
}

let current: any = null;
let stop: (() => any) | null = null;

let userId: string | null = null;

async function start(kind: 'enroll' | 'login') {
  try {
    setStatus('');
    const path = kind === 'enroll' ? '/api/enroll/start' : `/api/login/start?user_id=${encodeURIComponent(userId || '')}`;
    if (kind === 'login' && !userId) {
      setStatus('Please enroll first', true);
      return;
    }
    current = await api(path);
    (document.getElementById('challenge') as HTMLElement).innerText = current.challenge;
    const input = document.getElementById('input') as HTMLInputElement;
    input.value = '';
    if (stop) stop();
    const capturer = startCapture(input);
    stop = () => capturer.stop();
    setStatus(`Ready to ${kind}. Type the challenge and press Enter.`);
  } catch (err: any) {
    setStatus(`Failed to start ${kind}: ${err.message}`, true);
  }
}

document.getElementById('enroll')!.addEventListener('click', () => start('enroll'));
document.getElementById('login')!.addEventListener('click', () => start('login'));

document.getElementById('input')!.addEventListener('keydown', async (e) => {
  if (e.key !== 'Enter' || !current) return;
  
  showProgress(true);
  setStatus('Processing...');
  
  try {
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

  // Hash nonce and origin_hash strings to BigInt field elements
  const nonceField = hashStringToBigInt(current.nonce);
  const originField = hashHexToBigInt(current.origin_hash);
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
      setStatus('Generating ZK proof...');
      const wasm = '/artifacts/keystroke_js/keystroke.wasm';
      const zkey = '/artifacts/keystroke_final.zkey';
      const res = await generateProof(inputs, wasm, zkey);
      proof = res.proof;
      setStatus('Proof generated, submitting...');
    } catch (err: any) {
      console.warn('Proof generation failed, using dummy proof:', err);
      setStatus('Using bypass mode (proof generation failed)', true);
      // Requires backend BYPASS_ZK_VERIFY=1
    }

    if (current.commitment) {
      // Login finish
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
      if (rf.success && rf.token) {
        setStatus('Login successful!');
        (document.getElementById('logout') as HTMLElement).style.display = 'inline';
        localStorage.setItem('auth_token', rf.token);
      }
      out.textContent = JSON.stringify(rf, null, 2);
    } else {
      // Enroll finish
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
      if (rf.success && rf.user_id) {
        userId = rf.user_id;
        saveTemplate(userId, {
          template: features,
          salt: toBigIntDecimal(salt),
          saltKey: toBigIntDecimal(saltKey),
          commitment: toBigIntDecimal(C),
        });
        setStatus(`Enrollment successful! User ID: ${userId}`);
      }
      out.textContent = JSON.stringify(rf, null, 2);
    }
  } catch (err: any) {
    setStatus(`Error: ${err.message}`, true);
    const out = document.getElementById('out') as HTMLPreElement;
    out.textContent = `Error: ${err.message}`;
  } finally {
    showProgress(false);
  }
});

// Logout handler
document.getElementById('logout')!.addEventListener('click', async () => {
  const token = localStorage.getItem('auth_token');
  if (!token) {
    setStatus('No token found', true);
    return;
  }
  try {
    await api('/api/logout', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` },
    });
    localStorage.removeItem('auth_token');
    (document.getElementById('logout') as HTMLElement).style.display = 'none';
    setStatus('Logged out successfully');
  } catch (err: any) {
    setStatus(`Logout error: ${err.message}`, true);
  }
});


