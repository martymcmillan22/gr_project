from __future__ import annotations

import hashlib
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


EICAR_SIGNATURE = b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"


def is_clamscan_available() -> bool:
    return bool(shutil.which("clamscan"))


@dataclass(frozen=True)
class AttachmentScanResult:
    is_clean: bool
    status: str
    notes: str
    sha256: str


def _sha256_for_uploaded_file(uploaded_file) -> str:
    digest = hashlib.sha256()
    uploaded_file.seek(0)
    for chunk in uploaded_file.chunks():
        digest.update(chunk)
    uploaded_file.seek(0)
    return digest.hexdigest()


def _contains_eicar(uploaded_file) -> bool:
    uploaded_file.seek(0)
    tail = b""
    for chunk in uploaded_file.chunks():
        haystack = tail + chunk
        if EICAR_SIGNATURE in haystack:
            uploaded_file.seek(0)
            return True
        tail = haystack[-128:]
    uploaded_file.seek(0)
    return False


def _run_clamscan(uploaded_file) -> tuple[str, str] | None:
    executable = shutil.which("clamscan")
    if not executable:
        return None

    uploaded_file.seek(0)
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
            for chunk in uploaded_file.chunks():
                tmp.write(chunk)

        result = subprocess.run(
            [executable, "--no-summary", tmp_path],
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
        )

        output = (result.stdout or result.stderr or "").strip()
        if result.returncode == 0:
            return ("clean", "clamav clean")
        if result.returncode == 1:
            return ("flagged", output or "clamav detected threat")
        return ("error", output or "clamav scanner error")
    except Exception as exc:
        return ("error", f"clamav execution failure: {exc}")
    finally:
        uploaded_file.seek(0)
        if tmp_path:
            try:
                Path(tmp_path).unlink(missing_ok=True)
            except Exception:
                pass


def scan_uploaded_attachment(uploaded_file) -> AttachmentScanResult:
    file_hash = _sha256_for_uploaded_file(uploaded_file)

    if _contains_eicar(uploaded_file):
        return AttachmentScanResult(
            is_clean=False,
            status="flagged",
            notes="Blocked by EICAR signature rule.",
            sha256=file_hash,
        )

    clam_result = _run_clamscan(uploaded_file)
    if clam_result is not None:
        status, notes = clam_result
        return AttachmentScanResult(
            is_clean=status == "clean",
            status=status,
            notes=notes,
            sha256=file_hash,
        )

    return AttachmentScanResult(
        is_clean=False,
        status="error",
        notes="Upload blocked: clamscan is not available on this server.",
        sha256=file_hash,
    )
