#!/usr/bin/env python3
"""Write a bounded, typed ZhiCoach report without copying private artifacts."""
import argparse
import datetime as dt
import hashlib
import json
import os
import subprocess
import tempfile
import uuid
import re

SKILL_ID = "zhiphoto"
REPO_ID = "zhiphoto-repo"
SUPPRESSED = {"eval", "zhicoach", "reporting"}
CONTEXTS = {"customer", *SUPPRESSED}
ID_PATTERN = re.compile(r"^[a-z][a-z0-9_-]{1,63}$")
INPUT_KEYS = {"schema_version", "report_id", "run_id", "started_at", "ended_at", "termination_status", "producer", "model_tool_config", "redaction_status", "sensitivity_class", "evidence"}
EVIDENCE_TYPES = {"human_feedback", "agent_observation", "machine_evidence", "agent_inference"}
DEFAULT_SOURCE_REPO = "/Volumes/T7-APFS/Development/zhiphoto"

def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()

def skill_tree_hash(root):
    digest = hashlib.sha256()
    for base, dirs, files in os.walk(root):
        if any(os.path.islink(os.path.join(base, directory)) for directory in dirs):
            raise ValueError("symlink in skill tree")
        dirs[:] = sorted(d for d in dirs if d != "__pycache__")
        for name in sorted(files):
            if name == ".DS_Store" or name.endswith(".pyc"):
                continue
            path = os.path.join(base, name)
            if os.path.islink(path):
                raise ValueError("symlink in skill tree")
            relative = os.path.relpath(path, root).replace(os.sep, "/")
            digest.update(relative.encode() + b"\0" + bytes.fromhex(sha256_file(path)) + b"\n")
    return digest.hexdigest()

def git_head(repo):
    try:
        return subprocess.check_output(["git", "-C", repo, "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError):
        return None

def resolve_source_repo(local_candidate, requested):
    candidates = []
    if requested:
        candidates.append(requested)
    configured = os.environ.get("ZHIPHOTO_REPO_PATH")
    if configured:
        candidates.append(configured)
    candidates.extend([local_candidate, DEFAULT_SOURCE_REPO])
    seen = set()
    for candidate in candidates:
        repo = os.path.abspath(candidate)
        if repo in seen:
            continue
        seen.add(repo)
        commit = git_head(repo)
        if commit:
            return repo, commit
    return None, None

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    write = sub.add_parser("write")
    write.add_argument("--context", required=True)
    write.add_argument("--input", required=True)
    write.add_argument("--repo-path", default=None, help="ZhiPhoto source repository, if the installed copy cannot infer it")
    write.add_argument("--inbox", default="/Volumes/T7-APFS/Development/zhicoach/.local/run-reports/inbox")
    args = parser.parse_args(argv)
    if args.context not in CONTEXTS:
        parser.error("invalid context")
    if args.context in SUPPRESSED:
        print(json.dumps({"status": "suppressed", "context": args.context}, sort_keys=True)); return 0
    with open(args.input, encoding="utf-8") as stream:
        source = json.load(stream)
    if not isinstance(source, dict):
        parser.error("input must be an object")
    if set(source) - INPUT_KEYS:
        parser.error("unknown input fields")
    required = {"schema_version", "run_id", "started_at", "ended_at", "termination_status", "producer", "model_tool_config", "redaction_status", "sensitivity_class", "evidence"}
    missing = sorted(required - set(source))
    if missing: parser.error("missing input fields: " + ", ".join(missing))
    if source["schema_version"] != "1.0" or not isinstance(source["run_id"], str) or not ID_PATTERN.fullmatch(source["run_id"]): parser.error("invalid schema or run_id")
    try:
        started = dt.datetime.fromisoformat(source["started_at"].replace("Z", "+00:00")); ended = dt.datetime.fromisoformat(source["ended_at"].replace("Z", "+00:00"))
    except (AttributeError, TypeError, ValueError):
        parser.error("invalid ISO-8601 timestamp")
    if started.tzinfo is None or ended.tzinfo is None or ended < started or not isinstance(source["redaction_status"], str) or source["redaction_status"] not in {"redacted", "not_sensitive"} or not isinstance(source["sensitivity_class"], str) or source["sensitivity_class"] not in {"public", "internal", "confidential", "restricted"} or not isinstance(source["termination_status"], str) or source["termination_status"] not in {"completed", "failed", "interrupted", "cancelled"}: parser.error("invalid timing, outcome, or redaction")
    producer = source["producer"]
    if not isinstance(producer, dict) or set(producer) != {"id", "version"} or not isinstance(producer["id"], str) or not producer["id"] or not ID_PATTERN.fullmatch(producer["id"]) or not isinstance(producer["version"], str) or not producer["version"] or len(producer["version"]) > 100: parser.error("invalid producer")
    if not isinstance(source["model_tool_config"], dict) or set(source["model_tool_config"]) - {"model", "tools"} or not isinstance(source["model_tool_config"].get("model", ""), str) or len(source["model_tool_config"].get("model", "")) > 200 or not isinstance(source["model_tool_config"].get("tools", []), list) or len(source["model_tool_config"].get("tools", [])) > 100 or any(not isinstance(tool, str) or len(tool) > 200 for tool in source["model_tool_config"].get("tools", [])): parser.error("invalid model/tool configuration")
    evidence = source["evidence"]
    if not isinstance(evidence, list) or len(evidence) > 1000: parser.error("invalid evidence list")
    for item in evidence:
        if not isinstance(item, dict) or set(item) != {"evidence_id", "type", "text", "source"} or not isinstance(item["evidence_id"], str) or not ID_PATTERN.fullmatch(item["evidence_id"]) or not isinstance(item["type"], str) or item["type"] not in EVIDENCE_TYPES or not isinstance(item["text"], str) or not isinstance(item["source"], str) or len(item["text"]) > 20000 or len(item["source"]) > 500: parser.error("invalid evidence")
    if len({item["evidence_id"] for item in evidence}) != len(evidence): parser.error("duplicate evidence id")
    report_id = source.get("report_id") or "r" + uuid.uuid5(uuid.NAMESPACE_URL, source["run_id"] + started.isoformat()).hex
    if not isinstance(report_id, str) or not ID_PATTERN.fullmatch(report_id): parser.error("invalid report_id")
    skill = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    local_repo = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
    repo, commit = resolve_source_repo(local_repo, args.repo_path)
    if not repo:
        parser.error("could not resolve a Git-backed ZhiPhoto source repository; pass --repo-path or set ZHIPHOTO_REPO_PATH")
    report = {"schema_version": "1.0", "report_id": report_id, "run_id": source["run_id"], "skill_id": SKILL_ID, "repo_id": REPO_ID, "skill_commit": commit, "installed_hash": skill_tree_hash(skill), "producer": source["producer"], "started_at": source["started_at"], "ended_at": source["ended_at"], "termination_status": source["termination_status"], "model_tool_config": source["model_tool_config"], "redaction_status": source["redaction_status"], "sensitivity_class": source["sensitivity_class"], "evidence": evidence, "artifacts": []}
    if not ID_PATTERN.fullmatch(report_id): parser.error("invalid report_id")
    parent = os.path.join(os.path.abspath(args.inbox), SKILL_ID); os.makedirs(parent, exist_ok=True); destination = os.path.join(parent, report_id); report_path = os.path.join(destination, "report.json")
    if os.path.exists(report_path): print(json.dumps({"status": "duplicate", "report_id": report_id}, sort_keys=True)); return 0
    temporary = tempfile.mkdtemp(prefix=f".{report_id}-", dir=parent); temporary_report = os.path.join(temporary, "report.json")
    with open(temporary_report, "w", encoding="utf-8") as stream: json.dump(report, stream, sort_keys=True, separators=(",", ":")); stream.write("\n"); stream.flush(); os.fsync(stream.fileno())
    try: os.rename(temporary, destination)
    except FileExistsError: print(json.dumps({"status": "duplicate", "report_id": report_id}, sort_keys=True)); return 0
    print(json.dumps({"status": "written", "report_id": report_id, "report_dir": destination}, sort_keys=True)); return 0

if __name__ == "__main__":
    raise SystemExit(main())
