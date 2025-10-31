import random
from typing import List


def l1_distance(a: List[int], b: List[int]) -> int:
    return sum(abs(x - y) for x, y in zip(a, b))


def test_synthetic_frr_far() -> None:
    rng = random.Random(42)
    N = 64
    # Base template in 12-bit range
    template = [rng.randint(200, 800) for _ in range(N)]

    def noisy_sample(stddev: float) -> List[int]:
        return [max(0, min(4095, int(x + rng.gauss(0, stddev)))) for x in template]

    # Genuine attempts (small noise)
    tau = 400
    trials = 100
    accepts = 0
    for _ in range(trials):
        s = noisy_sample(5.0)
        if l1_distance(template, s) <= tau:
            accepts += 1
    genuine_rate = accepts / trials
    assert genuine_rate >= 0.8

    # Impostor attempts: shift template by larger random offset
    impostor = [min(4095, max(0, x + rng.randint(50, 150))) for x in template]
    rejects = 0
    for _ in range(trials):
        s = [max(0, min(4095, int(x + rng.gauss(0, 5.0)))) for x in impostor]
        if l1_distance(template, s) > tau:
            rejects += 1
    impostor_reject_rate = rejects / trials
    assert impostor_reject_rate >= 0.9


