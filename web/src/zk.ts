import { poseidon } from 'circomlibjs';

export function foldCommitment(template: number[], salt: bigint): bigint {
  let rolling = salt;
  for (const t of template) {
    rolling = poseidon([rolling, BigInt(t)]);
  }
  return rolling;
}

export function foldKey(template: number[], saltKey: bigint): bigint {
  let rolling = saltKey;
  for (const t of template) {
    rolling = poseidon([rolling, BigInt(t)]);
  }
  return poseidon([rolling, saltKey]);
}

export function computeSig(nonce: bigint, originHash: bigint, timestamp: bigint, keyHash: bigint): bigint {
  return poseidon([nonce, originHash, timestamp, keyHash]);
}

export function toBigIntDecimal(x: bigint): string {
  return x.toString(10);
}


