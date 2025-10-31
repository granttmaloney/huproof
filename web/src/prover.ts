// Browser wrapper for snarkjs groth16 proving
import { groth16 } from 'snarkjs';

export type ProofResult = {
  proof: any;
  publicSignals: any;
};

export async function generateProof(
  input: any,
  wasmPath: string,
  zkeyPath: string,
): Promise<ProofResult> {
  return groth16.fullProve(input, wasmPath, zkeyPath);
}


