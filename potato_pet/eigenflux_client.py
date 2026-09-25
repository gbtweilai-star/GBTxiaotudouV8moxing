"""EigenFlux CLI adapter for the desktop panel.

Live CLI calls are preferred. When the network is unavailable, the adapter
falls back to EigenFlux's own local caches so the panel remains useful.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


_CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
_WINDOWS_PATH_RE = re.compile(r"(?i)(?:^|\s)[a-z]:\\")
_INTERNAL_RE = re.compile(
    r"(?i)(?:room_id|mirror_space|dimension_naming|gbt_allinone|"
    r"api[_ -]?key|access[_ -]?token|password|credential|"
    r"bearer\s+[a-z0-9._~+/=-]{12,}|-----begin [a-z ]*private key-----)"
)


class EigenFluxClient:
    """Small, testable wrapper around the EigenFlux command line."""

    def __init__(self, config: dict):
        cfg = config.get("eigenflux", {}) or {}
        self.config = cfg
        self.enabled = bool(cfg.get("enabled", True))
        self.server = str(cfg.get("server") or "eigenflux")
        home = str(
            cfg.get("home")
            or os.environ.get("EIGENFLUX_HOME")
            or Path.home() / ".eigenflux"
        )
        self.home = Path(os.path.expandvars(os.path.expanduser(home)))
        self.timeout = max(3, int(cfg.get("command_timeout_s", 20) or 20))
        self.exe = self._find_executable(cfg)
        self.feed_limit = max(1, min(int(cfg.get("feed_limit", 20) or 20), 50))
        self.message_limit = max(
            1, min(int(cfg.get("message_limit", 20) or 20), 50))
        self.friend_limit = max(
            1, min(int(cfg.get("friend_limit", 50) or 50), 100))

    @staticmethod
    def _find_executable(cfg: dict) -> str:
        explicit = str(cfg.get("executable") or "").strip()
        if explicit:
            return explicit
        found = shutil.which("eigenflux")
        if found:
            return found
        local = Path(os.environ.get("LOCALAPPDATA", "")) / "local" / "bin"
        for name in ("eigenflux.exe", "eigenflux.cmd", "eigenflux"):
            candidate = local / name
            if candidate.is_file():
                return str(candidate)
        return ""

    @property
    def installed(self) -> bool:
        return bool(self.exe and Path(self.exe).exists())

    @property
    def authenticated(self) -> bool:
        return (
            self.home / "servers" / self.server / "credentials.json"
        ).is_file()

    def status(self) -> dict:
        return {
            "ok": bool(self.installed),
            "enabled": self.enabled,
            "installed": self.installed,
            "authenticated": self.authenticated,
            "home": str(self.home),
            "server": self.server,
            "executable": self.exe,
        }

    def _base_command(self) -> list[str]:
        cmd = [
            self.exe,
            "--format",
            "json",
            "--no-interactive",
            "--homedir",
            str(self.home),
        ]
        if self.server:
            cmd.extend(["--server", self.server])
        return cmd

    def _run(self, args: list[str], timeout: int | None = None) -> dict:
        if not self.installed:
            return {
                "ok": False,
                "code": -1,
                "error": "EigenFlux CLI is not installed",
                "data": {},
                "raw": "",
            }
        cmd = self._base_command() + [str(item) for item in args]
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=max(3, int(timeout or self.timeout)),
                creationflags=_CREATE_NO_WINDOW,
                check=False,
            )
        except Exception as exc:  # noqa: BLE001
            return {
                "ok": False,
                "code": -1,
                "error": f"{type(exc).__name__}: {exc}",
                "data": {},
                "raw": "",
            }

        raw = (proc.stdout or "").lstrip("\ufeff").strip()
        payload = {}
        if raw:
            try:
                payload = json.loads(raw)
            except Exception:
                payload = {}
        code = payload.get("code") if isinstance(payload, dict) else None
        if code is None:
            code = 0 if proc.returncode == 0 and payload else proc.returncode
        error = ""
        if not isinstance(payload, dict) or not payload:
            error = (proc.stderr or proc.stdout or "").strip()[:500]
        elif int(code or 0) != 0:
            error = str(payload.get("msg") or payload.get("error") or "").strip()
        return {
            "ok": proc.returncode == 0 and int(code or 0) == 0,
            "code": int(code or 0),
            "error": error,
            "data": payload.get("data") if isinstance(payload, dict) else {},
            "raw": raw,
        }

    @staticmethod
    def _rows(data, *keys: str) -> list:
        if isinstance(data, list):
            return [row for row in data if isinstance(row, dict)]
        if not isinstance(data, dict):
            return []
        for key in keys:
            value = data.get(key)
            if isinstance(value, list):
                return [row for row in value if isinstance(row, dict)]
        return []

    def feed(self) -> dict:
        result = self._run([
            "feed",
            "poll",
            "--limit",
            str(self.feed_limit),
            "--action",
            "refresh",
        ])
        if result.get("ok"):
            data = result.get("data") or {}
            return {
                "ok": True,
                "source": "live",
                "items": self._rows(data, "items"),
                "notifications": self._rows(data, "notifications"),
                "warning": "",
            }
        cached = self._feed_cache()
        if cached is not None:
            cached["warning"] = result.get("error") or "using local cache"
            return cached
        return {
            "ok": False,
            "source": "none",
            "items": [],
            "notifications": [],
            "error": result.get("error") or "feed unavailable",
        }

    def messages(self) -> dict:
        result = self._run([
            "msg",
            "fetch",
            "--limit",
            str(self.message_limit),
        ])
        if result.get("ok"):
            return {
                "ok": True,
                "source": "live",
                "items": self._rows(
                    result.get("data") or {}, "messages", "items"),
                "warning": "",
            }
        cached = self._message_cache()
        if cached is not None:
            cached["warning"] = result.get("error") or "using local cache"
            return cached
        return {
            "ok": False,
            "source": "none",
            "items": [],
            "error": result.get("error") or "messages unavailable",
        }

    def friends(self) -> dict:
        result = self._run([
            "relation",
            "friends",
            "--limit",
            str(self.friend_limit),
        ])
        if result.get("ok"):
            return {
                "ok": True,
                "source": "live",
                "items": self._rows(
                    result.get("data") or {}, "friends", "items"),
                "warning": "",
            }
        cached = self._contacts_cache()
        if cached is not None:
            cached["warning"] = result.get("error") or "using local cache"
            return cached
        return {
            "ok": False,
            "source": "none",
            "items": [],
            "error": result.get("error") or "friends unavailable",
        }

    def profile(self) -> dict:
        result = self._run(["profile", "show"])
        if result.get("ok"):
            return {
                "ok": True,
                "source": "live",
                "data": result.get("data") if isinstance(
                    result.get("data"), dict) else {},
                "warning": "",
            }
        profile = self._read_json(
            self.home / "servers" / self.server / "profile.json", {})
        return {
            "ok": bool(profile),
            "source": "cache" if profile else "none",
            "data": profile if isinstance(profile, dict) else {},
            "warning": result.get("error") or "",
        }

    def refresh(self) -> dict:
        sections = {}
        with ThreadPoolExecutor(max_workers=4) as pool:
            jobs = {
                "feed": pool.submit(self.feed),
                "messages": pool.submit(self.messages),
                "friends": pool.submit(self.friends),
                "profile": pool.submit(self.profile),
            }
            for name, future in jobs.items():
                try:
                    sections[name] = future.result()
                except Exception as exc:  # noqa: BLE001
                    sections[name] = {
                        "ok": False,
                        "source": "none",
                        "items": [],
                        "error": f"{type(exc).__name__}: {exc}",
                    }
        errors = [
            str(section.get("error") or section.get("warning") or "")
            for section in sections.values()
            if not section.get("ok")
        ]
        return {
            "ok": any(section.get("ok") for section in sections.values()),
            "loaded_at": int(time.time()),
            "status": self.status(),
            "errors": [row for row in errors if row],
            **sections,
        }

    def send_message(
        self,
        content: str,
        *,
        conv_id: str = "",
        receiver_id: str = "",
        item_id: str = "",
    ) -> dict:
        content = str(content or "").strip()
        safe, reason = public_text_guard(content)
        if not safe:
            return {"ok": False, "error": reason}
        if not any((conv_id, receiver_id, item_id)):
            return {"ok": False, "error": "message target is required"}
        args = ["msg", "send", "--content", content]
        if conv_id:
            args.extend(["--conv-id", str(conv_id)])
        elif item_id:
            args.extend(["--item-id", str(item_id)])
        else:
            args.extend(["--receiver-id", str(receiver_id)])
        result = self._run(args)
        return {
            "ok": bool(result.get("ok")),
            "error": result.get("error") or "",
            "data": result.get("data") if isinstance(
                result.get("data"), dict) else {},
        }

    def _feed_cache(self) -> dict | None:
        root = self.home / "servers" / self.server / "data" / "broadcasts"
        files = sorted(
            root.rglob("feeds-*.json"),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        ) if root.exists() else []
        for path in files:
            payload = self._read_json(path, None)
            if isinstance(payload, dict) and isinstance(payload.get("items"), list):
                return {
                    "ok": True,
                    "source": "cache",
                    "items": self._rows(payload, "items"),
                    "notifications": self._rows(payload, "notifications"),
                }
        return None

    def _message_cache(self) -> dict | None:
        root = self.home / "servers" / self.server / "data" / "messages"
        rows = []
        seen = set()
        files = sorted(
            root.rglob("*.json"),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        ) if root.exists() else []
        for path in files:
            payload = self._read_json(path, None)
            candidates = self._rows(payload, "messages", "items")
            if isinstance(payload, list):
                candidates = self._rows(payload)
            for row in candidates:
                msg_id = str(row.get("msg_id") or "")
                key = msg_id or json.dumps(row, sort_keys=True, ensure_ascii=False)
                if key in seen:
                    continue
                seen.add(key)
                rows.append(row)
                if len(rows) >= self.message_limit:
                    break
            if len(rows) >= self.message_limit:
                break
        if not rows:
            return None
        rows.sort(
            key=lambda row: int(row.get("created_at") or 0),
            reverse=True,
        )
        return {"ok": True, "source": "cache", "items": rows}

    def _contacts_cache(self) -> dict | None:
        payload = self._read_json(
            self.home / "servers" / self.server / "contacts.json", None)
        rows = self._rows(payload)
        if not rows:
            return None
        return {
            "ok": True,
            "source": "cache",
            "items": rows[: self.friend_limit],
        }

    @staticmethod
    def _read_json(path: Path, default):
        try:
            with path.open("r", encoding="utf-8") as handle:
                return json.load(handle)
        except Exception:
            return default


def public_text_guard(text: str) -> tuple[bool, str]:
    """Reject obvious private or internal material before network delivery."""
    value = str(text or "").strip()
    if not value:
        return False, "message is empty"
    if len(value) > 2000:
        return False, "message is too long"
    if _WINDOWS_PATH_RE.search(value) or _INTERNAL_RE.search(value):
        return False, "message contains private or internal material"
    return True, ""
