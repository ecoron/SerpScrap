"""Atomic JSON result persistence."""

from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any


class JsonOutputError(RuntimeError):
    """Raised when result JSON cannot be validated or written."""


def normalize_json_path(path: str | Path) -> Path:
    target = Path(path).expanduser()
    if not target.suffix:
        target = target.with_suffix(".json")
    elif target.suffix.lower() != ".json":
        raise JsonOutputError("Result output must use the .json extension; CSV is unsupported")
    return target


class JsonResultWriter:
    """Write a canonical result list as UTF-8 JSON using atomic replacement."""

    def write(
        self,
        path: str | Path,
        results: Iterable[Mapping[str, Any]],
        *,
        overwrite: bool = False,
    ) -> Path:
        target = normalize_json_path(path)
        rows = [dict(row) for row in results]
        try:
            payload = json.dumps(rows, ensure_ascii=False, indent=2) + "\n"
        except (TypeError, ValueError) as exc:
            raise JsonOutputError(f"Results are not JSON serializable: {exc}") from exc

        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and not overwrite:
            raise FileExistsError(f"Refusing to overwrite existing result file: {target}")

        temporary: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                newline="\n",
                dir=target.parent,
                prefix=f".{target.name}.",
                suffix=".tmp",
                delete=False,
            ) as handle:
                temporary = Path(handle.name)
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            temporary.replace(target)
        except Exception as exc:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
            if isinstance(exc, (FileExistsError, JsonOutputError)):
                raise
            raise JsonOutputError(f"Failed to write JSON results to {target}: {exc}") from exc
        return target.resolve()
