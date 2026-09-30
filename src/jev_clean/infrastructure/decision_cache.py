"""Private exact-input inference cache. Reuse is never disguised as fresh inference."""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import sqlite3
import stat
import time
from collections import OrderedDict
from contextlib import AbstractContextManager
from dataclasses import asdict
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from jev_clean.infrastructure.model import (
    DISPOSITION_LABELS,
    INPUT_CONTRACT,
    MODEL_ID,
    MODEL_REVISION,
    QUESTIONS,
    parse_prediction,
)
from jev_clean.infrastructure.scanner import no_symlink_ancestors
from jev_clean.infrastructure.trash import secure_dir


class DecisionCache(AbstractContextManager):
    def __init__(self, directory: Path, advisor, roots: list[Path], mode: str):
        secure_dir(directory)
        self.directory = directory
        self.path = directory / "decisions.sqlite3"
        for path in (
            self.path,
            Path(str(self.path) + "-wal"),
            Path(str(self.path) + "-shm"),
            directory / "scan.lock",
        ):
            if not no_symlink_ancestors(path):
                raise ValueError("Symlink decision cache refused")
            if path.exists():
                info = path.lstat()
                if (
                    not stat.S_ISREG(info.st_mode)
                    or info.st_uid != os.getuid()
                    or info.st_nlink != 1
                    or info.st_mode & 0o022
                ):
                    raise ValueError("Unsafe decision cache file ownership/type/links")
        self.fd = os.open(directory / "scan.lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        try:
            fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            os.close(self.fd)
            raise RuntimeError("Another disk scan owns this checkpoint; finish or stop it first") from None
        try:
            self._initialize(advisor, roots, mode)
        except BaseException:
            if hasattr(self, "db"):
                self.db.close()
            os.close(self.fd)
            raise

    def _initialize(self, advisor, roots, mode):
        if not self.path.exists():
            fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
            os.close(fd)
        self.db = sqlite3.connect(self.path)
        os.chmod(self.path, 0o600)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("CREATE TABLE IF NOT EXISTS decisions (key TEXT PRIMARY KEY, result TEXT NOT NULL)")
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS checkpoint (scope TEXT PRIMARY KEY, epoch REAL NOT NULL, finished INTEGER NOT NULL, stats TEXT NOT NULL)"
        )
        try:
            runtime = version("laya-mlx")
        except PackageNotFoundError:
            runtime = "test-boundary"
        self.namespace = json.dumps(
            [
                MODEL_ID,
                MODEL_REVISION,
                INPUT_CONTRACT,
                DISPOSITION_LABELS,
                runtime,
                type(advisor).__module__,
                type(advisor).__qualname__,
                QUESTIONS,
            ],
            sort_keys=True,
        )
        self.scope = hashlib.sha256(
            json.dumps([mode, list(map(str, roots)), self.namespace]).encode()
        ).hexdigest()
        previous = self.db.execute(
            "SELECT epoch,finished FROM checkpoint WHERE scope=?", (self.scope,)
        ).fetchone()
        self.resumed = bool(previous and not previous[1])
        self.epoch = previous[0] if self.resumed else time.time()
        self.last_commit = time.monotonic()
        self.memory: OrderedDict = OrderedDict()
        self.save_progress({}, False)

    def get(self, state: str):
        key = hashlib.sha256((self.namespace + "\n" + state).encode()).hexdigest()
        if key in self.memory:
            self.memory.move_to_end(key)
            return self.memory[key]
        row = self.db.execute("SELECT result FROM decisions WHERE key=?", (key,)).fetchone()
        if not row:
            return None
        raw = json.loads(row[0])
        decision = parse_prediction(
            {"answers": {"disposition": {"choice": raw["choice"], "probabilities": raw["probabilities"]}}},
            0.0,
            raw["backend"],
        )
        self._remember(key, decision)
        return decision

    def _remember(self, key, decision):
        self.memory[key] = decision
        self.memory.move_to_end(key)
        if len(self.memory) > 4096:
            self.memory.popitem(last=False)

    def put(self, state: str, decision):
        key = hashlib.sha256((self.namespace + "\n" + state).encode()).hexdigest()
        self.db.execute("INSERT OR REPLACE INTO decisions VALUES (?,?)", (key, json.dumps(asdict(decision))))
        self._remember(key, decision)
        if time.monotonic() - self.last_commit > 2:
            self.db.commit()
            self.last_commit = time.monotonic()

    def save_progress(self, stats: dict, finished: bool):
        self.db.execute(
            "INSERT OR REPLACE INTO checkpoint VALUES (?,?,?,?)",
            (self.scope, self.epoch, int(finished), json.dumps(stats)),
        )
        self.db.commit()

    def __exit__(self, *args):
        try:
            self.db.commit()
            self.db.close()
        finally:
            os.close(self.fd)
