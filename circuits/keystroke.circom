pragma circom 2.1.5;

include "circomlib/circuits/poseidon.circom";
include "circomlib/circuits/comparators.circom";

// Keystroke liveness circuit
// - Checks L1 distance between quantized `template` and `features` is <= tau
// - Commits to template via Poseidon and exposes it as public `C`
// - Binds proof to (nonce, origin_hash, timestamp) using a derived key from the template

template AbsDiff(nBits) {
    signal input a;      // in range [0, 2^nBits)
    signal input b;      // in range [0, 2^nBits)
    signal output out;   // |a - b|

    // Compute both differences as field values
    signal ndiff; // a - b
    signal diff;  // b - a

    component lt = LessThan(nBits);
    lt.in[0] <== a;
    lt.in[1] <== b;

    // if a < b => lt.out == 1 => out == (b - a); else out == (a - b)
    ndiff <== a - b;
    diff <== b - a;
    // Use one quadratic term: out = ndiff + lt.out * (diff - ndiff)
    signal delta;
    delta <== diff - ndiff;
    out <== ndiff + lt.out * delta;
}

template SumL1(N, nBits) {
    signal input A[N];
    signal input B[N];
    signal output out;

    var i;
    signal parts[N];
    component ad[N];
    for (i = 0; i < N; i++) {
        ad[i] = AbsDiff(nBits);
        ad[i].a <== A[i];
        ad[i].b <== B[i];
        parts[i] <== ad[i].out;
    }

    // Accumulate using a chain to avoid multiple assignments to the same signal
    signal acc[N+1];
    acc[0] <== 0;
    for (i = 0; i < N; i++) {
        acc[i+1] <== acc[i] + parts[i];
    }
    out <== acc[N];
}

template Keystroke(N, nBits) {
    // Public inputs
    signal input C;              // Poseidon(template..., salt)
    signal input nonce;          // challenge nonce
    signal input origin_hash;    // hash(domain)
    signal input timestamp;      // unix time
    signal input tau;            // threshold
    signal input sig;            // Poseidon(nonce, origin_hash, timestamp, key)

    // Private witness
    signal input tmpl[N];        // quantized reference
    signal input features[N];    // live sample
    signal input salt;           // randomness for commitment
    signal input salt_key;       // randomness for binding key

    // Distance <= tau
    component sum = SumL1(N, nBits);
    var i;
    for (i = 0; i < N; i++) {
        sum.A[i] <== tmpl[i];
        sum.B[i] <== features[i];
    }

    // sum.out <= tau
    component ltTau = LessThan(32); // tau assumed to fit in 32 bits
    ltTau.in[0] <== sum.out;
    ltTau.in[1] <== tau + 1; // ensure sum.out < tau+1 => sum.out <= tau
    // Enforce boolean true
    ltTau.out === 1;

    // Commitment to template: Poseidon(tmpl..., salt) == C
    // Note: Poseidon arity is limited; we fold template via a rolling hash
    // Use accumulator array to avoid reassigning the same signal
    signal roll[N+1];
    roll[0] <== salt;
    component h[N];
    for (i = 0; i < N; i++) {
        h[i] = Poseidon(2);
        h[i].inputs[0] <== roll[i];
        h[i].inputs[1] <== tmpl[i];
        roll[i+1] <== h[i].out;
    }
    roll[N] === C;

    // Binding tag: sig == Poseidon(nonce, origin_hash, timestamp, key)
    // key = Poseidon(rolling_key, salt_key) where rolling_key folds template
    // Fold template again to derive a binding key; use accumulator array
    signal rk[N+1];
    rk[0] <== salt_key;
    component hk[N];
    for (i = 0; i < N; i++) {
        hk[i] = Poseidon(2);
        hk[i].inputs[0] <== rk[i];
        hk[i].inputs[1] <== tmpl[i];
        rk[i+1] <== hk[i].out;
    }

    component keyHash = Poseidon(2);
    keyHash.inputs[0] <== rk[N];
    keyHash.inputs[1] <== salt_key;

    component bind = Poseidon(4);
    bind.inputs[0] <== nonce;
    bind.inputs[1] <== origin_hash;
    bind.inputs[2] <== timestamp;
    bind.inputs[3] <== keyHash.out;

    bind.out === sig;
}

component main = Keystroke(64, 12); // N=64 features, each < 2^12


