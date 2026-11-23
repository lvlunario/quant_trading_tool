"""Content-addressed pre-freeze regression manifest for the M5 candidate."""
from dataclasses import dataclass
from datetime import date, datetime
from hashlib import sha256
import json
import os
from pathlib import Path, PurePosixPath
import re
from zoneinfo import ZoneInfo

from .m5_workflow_rehearsal import M5WorkflowRehearsal


_HEX_64 = re.compile(r"[0-9a-f]{64}")
_SAFE_TREES = ("atlas", "fixtures", "preview", "tests")
_SAFE_SUFFIXES = frozenset((".csv", ".html", ".json", ".md", ".py"))
_RUNBOOKS = (
    "docs/M5_RELEASE_CANDIDATE.md",
    "docs/M5_DEFECT_REGISTER.md",
    "docs/PROGRAM.md",
    "docs/QUALITY.md",
    "docs/SECURITY.md",
)
_MAX_FILE_BYTES = 2_000_000
_MAX_BUNDLE_BYTES = 32_000_000
_REGRESSION_COMMANDS = (
    ("full_unittest", "python -m unittest discover -s tests -v", 0),
    ("workflow_rehearsal", "python -m atlas --m5-workflow-rehearsal-demo", 3),
    ("regression_manifest", "python -m atlas --m5-regression-manifest-demo", 3),
)


def _canonical_sha256(value):
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":")).encode("ascii")
    return sha256(payload).hexdigest()


@dataclass(frozen=True, order=True)
class RegressionFileEvidence:
    path: str
    sha256: str
    size_bytes: int

    def __post_init__(self):
        candidate = PurePosixPath(self.path)
        if (not self.path or candidate.is_absolute() or
                ".." in candidate.parts or
                _HEX_64.fullmatch(self.sha256 or "") is None or
                not isinstance(self.size_bytes, int) or
                self.size_bytes < 0 or
                self.size_bytes > _MAX_FILE_BYTES):
            raise ValueError("invalid_m5_regression_file_evidence")

    def canonical_record(self):
        return {
            "path": self.path,
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
        }


def _bundle_sha256(files):
    return _canonical_sha256([item.canonical_record() for item in files])


@dataclass(frozen=True)
class M5RegressionManifest:
    generated_at: datetime
    rehearsal_sha256: str
    files: tuple[RegressionFileEvidence, ...]
    schema_version: int = 1
    scope: str = "pre_freeze_reduced_candidate_regression_manifest"
    regression_executed: bool = False
    candidate_build_frozen: bool = False
    founder_response_recorded: bool = False
    milestone_accepted: bool = False
    deployment_authorized: bool = False
    private_data_authorized: bool = False
    release_authorized: bool = False
    real_money_authorized: bool = False

    def __post_init__(self):
        local_date = (
            self.generated_at.astimezone(ZoneInfo("Asia/Manila")).date()
            if isinstance(self.generated_at, datetime) and
            self.generated_at.tzinfo is not None else None
        )
        paths = tuple(item.path for item in self.files)
        required_prefixes = tuple(f"{name}/" for name in _SAFE_TREES)
        if (self.schema_version != 1 or
                local_date is None or local_date < date(2026, 11, 19) or
                _HEX_64.fullmatch(self.rehearsal_sha256 or "") is None or
                self.scope !=
                "pre_freeze_reduced_candidate_regression_manifest" or
                not self.files or
                self.files != tuple(sorted(self.files)) or
                len(paths) != len(set(paths)) or
                any(not any(path.startswith(prefix)
                            for prefix in required_prefixes) and
                    path not in _RUNBOOKS for path in paths) or
                any(not any(path.startswith(prefix) for path in paths)
                    for prefix in required_prefixes) or
                any(path not in paths for path in _RUNBOOKS) or
                self.total_bytes > _MAX_BUNDLE_BYTES or
                any(value is not False for value in (
                    self.regression_executed,
                    self.candidate_build_frozen,
                    self.founder_response_recorded,
                    self.milestone_accepted,
                    self.deployment_authorized,
                    self.private_data_authorized,
                    self.release_authorized,
                    self.real_money_authorized))):
            raise ValueError("invalid_m5_regression_manifest")

    @property
    def total_bytes(self):
        return sum(item.size_bytes for item in self.files)

    @property
    def source_bundle_sha256(self):
        return _bundle_sha256(self.files)

    def public_summary(self):
        return {
            "schema_version": self.schema_version,
            "receipt_state": "pre_freeze_regression_manifest",
            "status": "blocked",
            "phase": "M5 Release candidate preparation",
            "scope": self.scope,
            "generated_at": self.generated_at.isoformat(),
            "source_bundle": {
                "content_addressed": True,
                "file_count": len(self.files),
                "total_bytes": self.total_bytes,
                "sha256": self.source_bundle_sha256,
                "coverage_roots": list(_SAFE_TREES),
                "runbook_count": len(_RUNBOOKS),
            },
            "regression_contract": {
                "ready_for_replay": True,
                "execution_recorded": False,
                "command_count": len(_REGRESSION_COMMANDS),
                "commands": [
                    {
                        "sequence": index,
                        "name": name,
                        "command": command,
                        "expected_exit": expected_exit,
                    }
                    for index, (name, command, expected_exit) in enumerate(
                        _REGRESSION_COMMANDS, start=1)
                ],
            },
            "candidate_gate": {
                "ready": False,
                "blocker": "candidate_build_not_frozen",
                "manifest_only": True,
            },
            "founder_response_recorded": False,
            "milestone_acceptance_recorded": False,
            "deployment_authorized": False,
            "private_data_authorized": False,
            "release_authorized": False,
            "real_money_authorized": False,
            "investment_performance_established": False,
        }

    @property
    def manifest_sha256(self):
        return _canonical_sha256(self.public_summary())


def _candidate_paths(product_root):
    for tree_name in _SAFE_TREES:
        tree = product_root / tree_name
        if not tree.is_dir() or tree.is_symlink():
            raise ValueError("invalid_m5_regression_manifest_root")
        for candidate in sorted(tree.rglob("*")):
            if candidate.is_symlink():
                raise ValueError("invalid_m5_regression_manifest_file")
            if (candidate.is_file() and
                    candidate.suffix.lower() in _SAFE_SUFFIXES and
                    "__pycache__" not in candidate.parts):
                yield candidate
    for relative in _RUNBOOKS:
        candidate = product_root / relative
        if (not candidate.is_file() or candidate.is_symlink()):
            raise ValueError("invalid_m5_regression_manifest_runbook")
        yield candidate


def _file_evidence(product_root, candidate):
    resolved = candidate.resolve(strict=True)
    if not resolved.is_relative_to(product_root):
        raise ValueError("invalid_m5_regression_manifest_file")
    content = resolved.read_bytes()
    if len(content) > _MAX_FILE_BYTES:
        raise ValueError("invalid_m5_regression_manifest_file")
    return RegressionFileEvidence(
        path=resolved.relative_to(product_root).as_posix(),
        sha256=sha256(content).hexdigest(),
        size_bytes=len(content),
    )


def build_m5_regression_manifest(rehearsal, product_root, *, generated_at):
    """Bind the public-safe candidate surface without executing or freezing it."""
    if (not isinstance(rehearsal, M5WorkflowRehearsal) or
            not isinstance(generated_at, datetime) or
            generated_at.tzinfo is None or
            generated_at < rehearsal.executed_at):
        raise ValueError("invalid_m5_regression_manifest_input")
    rehearsal_summary = rehearsal.public_summary()
    if (rehearsal_summary.get("status") != "blocked" or
            rehearsal_summary.get("workflow", {}).get(
                "workstreams_executed") != 4 or
            rehearsal_summary.get("workflow", {}).get(
                "automated_execution_failures") != 0 or
            rehearsal_summary.get("candidate_gate", {}).get("ready") is not
            False or
            rehearsal_summary.get("milestone_acceptance_recorded") is not
            False or
            rehearsal_summary.get("release_authorized") is not False):
        raise ValueError("invalid_m5_regression_manifest_input")

    try:
        root = Path(os.fspath(product_root)).resolve(strict=True)
    except (OSError, TypeError, ValueError):
        raise ValueError("invalid_m5_regression_manifest_root") from None
    if not root.is_dir() or root.is_symlink():
        raise ValueError("invalid_m5_regression_manifest_root")
    files = tuple(sorted(
        _file_evidence(root, candidate)
        for candidate in _candidate_paths(root)
    ))
    return M5RegressionManifest(
        generated_at=generated_at,
        rehearsal_sha256=rehearsal.rehearsal_sha256,
        files=files,
    )
