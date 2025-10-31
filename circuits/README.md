# Circuits

Build Groth16 artifacts for the keystroke liveness circuit.

Prereqs: circom (>=2.1) and snarkjs in PATH.

Commands:

```bash
# 1) Compile circuit (r1cs, wasm)
npm run build

# 2) Powers of Tau (PoT)
npm run ptau:new
npm run ptau:contrib

# 3) Circuit-specific setup
npm run setup
npm run setup:contrib

# 4) Export verification key
npm run export:vkey

# 5) Prove and verify (example expects build/input.json)
npm run prove
npm run verify
```

Artifacts are written to `build/`. The FastAPI backend expects `build/verification_key.json` to exist.
