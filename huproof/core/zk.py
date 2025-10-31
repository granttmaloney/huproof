import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from time import perf_counter

from .logging import get_logger


logger = get_logger()


class ZKVerifyError(Exception):
    pass


def verify_groth16(vkey_path: Path, public_inputs: dict[str, Any], proof: dict[str, Any]) -> bool:
    """Verify a Groth16 proof using snarkjs CLI.

    Returns True if verification succeeds, False otherwise.
    Raises ZKVerifyError if snarkjs is missing or vkey does not exist.
    """
    snarkjs = shutil.which("snarkjs")
    if snarkjs is None:
        raise ZKVerifyError("snarkjs not found in PATH")
    if not vkey_path.exists():
        raise ZKVerifyError(f"verification key not found: {vkey_path}")

    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        public_path = td_path / "public.json"
        proof_path = td_path / "proof.json"

        public_path.write_text(json.dumps(public_inputs))
        proof_path.write_text(json.dumps(proof))

        cmd = [snarkjs, "groth16", "verify", str(vkey_path), str(public_path), str(proof_path)]
        t0 = perf_counter()
        proc = subprocess.run(cmd, capture_output=True, text=True)
        dt_ms = (perf_counter() - t0) * 1000.0
        if proc.returncode == 0:
            logger.info("zk_verify_ok", ms=round(dt_ms, 2))
            return True
        logger.warning(
            "zk_verify_failed",
            code=proc.returncode,
            ms=round(dt_ms, 2),
            stdout=proc.stdout,
            stderr=proc.stderr,
        )
        return False


