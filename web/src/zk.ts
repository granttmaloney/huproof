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

/**
 * Hash a string to a BigInt field element using Poseidon.
 * Splits string into chunks if needed to fit Poseidon arity.
 */
export function hashStringToBigInt(s: string): bigint {
  // Convert string to bytes, then to chunks of BigInts
  const encoder = new TextEncoder();
  const bytes = encoder.encode(s);
  
  // Convert bytes to array of BigInts (using 31-byte chunks to fit in field)
  const chunks: bigint[] = [];
  for (let i = 0; i < bytes.length; i += 31) {
    const chunk = bytes.slice(i, i + 31);
    let num = BigInt(0);
    for (let j = 0; j < chunk.length; j++) {
      num = num * BigInt(256) + BigInt(chunk[j]);
    }
    chunks.push(num);
  }
  
  // Hash chunks with Poseidon (arity 2, folding)
  if (chunks.length === 0) {
    return BigInt(0);
  }
  let result = chunks[0];
  for (let i = 1; i < chunks.length; i++) {
    result = poseidon([result, chunks[i]]);
  }
  return result;
}

/**
 * Convert a hex string to BigInt, then hash with Poseidon for field element.
 */
export function hashHexToBigInt(hexStr: string): bigint {
  // Remove 0x prefix if present
  const cleanHex = hexStr.startsWith('0x') ? hexStr.slice(2) : hexStr;
  // Parse hex to BigInt, then hash it
  const num = BigInt('0x' + cleanHex);
  // For very large numbers, split into chunks
  const maxChunk = BigInt(2) ** BigInt(248); // Safe chunk size
  if (num < maxChunk) {
    return poseidon([num]);
  }
  // Split large numbers
  const chunks: bigint[] = [];
  let remaining = num;
  while (remaining > BigInt(0)) {
    chunks.push(remaining % maxChunk);
    remaining = remaining / maxChunk;
  }
  let result = chunks[0];
  for (let i = 1; i < chunks.length; i++) {
    result = poseidon([result, chunks[i]]);
  }
  return result;
}


