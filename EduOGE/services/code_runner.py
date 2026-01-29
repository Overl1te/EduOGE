import os
import sys
import subprocess
import tempfile


class RunnerError(Exception):
    def __init__(self, kind: str, message: str = ""):
        super().__init__(message)
        self.kind = kind  # "syntax" | "timeout" | "runtime"
        self.message = message


def _limit(s: str, limit: int = 20000) -> str:
    """Limit output size but do NOT strip whitespace (it may be meaningful)."""
    s = (s or "")
    return s if len(s) <= limit else (s[:limit] + "\n...[trimmed]...")


def _classify_python(stderr: str) -> str:
    s = stderr or ""
    if "SyntaxError" in s or "IndentationError" in s:
        return "syntax"
    return "runtime"


def _classify_js(stderr: str) -> str:
    s = stderr or ""
    if "SyntaxError" in s:
        return "syntax"
    return "runtime"


def run_python(code: str, input_data: str, timeout_sec: int = 2) -> str:
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as f:
        f.write(code)
        filename = f.name

    try:
        result = subprocess.run(
            [sys.executable, "-I", filename],
            input=input_data,
            text=True,
            capture_output=True,
            timeout=timeout_sec,
        )
        if result.returncode != 0:
            kind = _classify_python(result.stderr)
            raise RunnerError(kind, _limit(result.stderr))
        return _limit(result.stdout)
    except subprocess.TimeoutExpired:
        raise RunnerError("timeout", "Timeout")
    finally:
        try:
            os.remove(filename)
        except OSError:
            pass


def run_js(code: str, input_data: str, timeout_sec: int = 2) -> str:
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
        f.write(code)
        filename = f.name

    try:
        result = subprocess.run(
            ["node", filename],
            input=input_data,
            text=True,
            capture_output=True,
            timeout=timeout_sec,
        )
        if result.returncode != 0:
            kind = _classify_js(result.stderr)
            raise RunnerError(kind, _limit(result.stderr))
        return _limit(result.stdout)
    except subprocess.TimeoutExpired:
        raise RunnerError("timeout", "Timeout")
    finally:
        try:
            os.remove(filename)
        except OSError:
            pass
