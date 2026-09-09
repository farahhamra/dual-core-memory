#!/usr/bin/env python3
"""
observe.py - Continuous Learning v2 (CLv2) Native Windows Observation & Mining Pipeline.

Extracts procedural instincts from chat transcripts and tool activity.
Operates as a milestone/post-hoc batch mining pipeline (System 2) on platforms
where background daemon hooks cannot survive parent termination (e.g. Windows Job Objects).

Enforces:
1. Strict schema validation on internal transcript logs with loud failure.
2. High-precision negative stop-phrase filtering (0% false positives on conversational phrases).
3. Symmetric two-sighting trust gate:
   - 1st sighting of explained directive: 0.65 (staged below 0.70 gate)
   - 2nd sighting (reinforcement): 0.85 (promoted past 0.70 gate)
4. Sanitized project scoping using sha256 hashes without leaking raw paths.
"""

import os
import sys
import re
import json
import hashlib
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

class SchemaMismatchError(Exception):
    """Raised when transcript format does not match expected schema."""
    pass

# Negative stop-phrases that must NEVER trigger an instinct
NEGATIVE_STOP_PHRASES = [
    "never mind",
    "nevermind",
    "always wanted to",
    "always wanted",
    "always meant to",
    "not always",
    "not necessarily",
    "as always",
    "almost always",
    "hardly ever",
    "is it always",
    "should we never",
    "why always",
    "can you",
    "could you",
    "would you",
]

def get_homunculus_dir() -> Path:
    """Resolve homunculus root directory across Windows / Linux / macOS."""
    env_dir = os.environ.get("CLV2_HOMUNCULUS_DIR") or os.environ.get("HOMUNCULUS_DIR")
    if env_dir:
        return Path(env_dir)

    # Windows AppData
    appdata = os.environ.get("LOCALAPPDATA")
    if appdata:
        cand = Path(appdata) / "ecc-homunculus"
        return cand

    # XDG or home fallback
    xdg = os.environ.get("XDG_DATA_HOME")
    if xdg:
        return Path(xdg) / "ecc-homunculus"

    return Path.home() / ".local" / "share" / "ecc-homunculus"

def detect_project(project_dir: Optional[Path] = None) -> Tuple[str, str]:
    """
    Detect project ID and name in a sanitized manner.
    Returns (project_id, project_name).
    """
    cwd = project_dir or Path.cwd()
    
    # 1. Check CLAUDE_PROJECT_DIR
    env_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    if env_dir:
        p = Path(env_dir)
        pid = hashlib.sha256(str(p.resolve()).encode("utf-8")).hexdigest()[:12]
        return pid, p.name

    # 2. Check Git remote
    git_config = cwd / ".git" / "config"
    if git_config.exists():
        try:
            content = git_config.read_text(encoding="utf-8", errors="ignore")
            match = re.search(r'url\s*=\s*(.+)', content)
            if match:
                url = match.group(1).strip()
                pid = hashlib.sha256(url.encode("utf-8")).hexdigest()[:12]
                name = url.rstrip("/").split("/")[-1].replace(".git", "")
                return pid, name
        except Exception:
            pass

    # 3. Fallback: hash normalized absolute directory path
    norm_path = str(cwd.resolve()).lower().replace("\\", "/")
    pid = hashlib.sha256(norm_path.encode("utf-8")).hexdigest()[:12]
    return pid, cwd.name or "project"

def find_default_transcript() -> Optional[Path]:
    """Auto-locate Antigravity transcript or standard observations.jsonl."""
    # Check Antigravity IDE AppData path
    appdata = os.environ.get("USERPROFILE") or str(Path.home())
    conv_id = os.environ.get("CONVERSATION_ID")
    
    candidates = []
    if conv_id:
        cand = Path(appdata) / ".gemini" / "antigravity-ide" / "brain" / conv_id / ".system_generated" / "logs" / "transcript.jsonl"
        candidates.append(cand)

    brain_dir = Path(appdata) / ".gemini" / "antigravity-ide" / "brain"
    if brain_dir.exists():
        # Look for most recent conversation transcript
        found = list(brain_dir.glob("*/.system_generated/logs/transcript.jsonl"))
        if found:
            found.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            candidates.extend(found)

    # Check homunculus observations.jsonl
    homunculus = get_homunculus_dir()
    cand_obs = homunculus / "observations.jsonl"
    if cand_obs.exists():
        candidates.append(cand_obs)

    for c in candidates:
        if c.exists() and c.stat().st_size > 0:
            return c

    return None

def validate_and_parse_transcript(path: Path) -> List[Dict[str, Any]]:
    """
    Parse and strictly schema-validate an Antigravity transcript or observations.jsonl.
    Raises SchemaMismatchError on unrecognized format.
    """
    if not path.exists():
        raise FileNotFoundError(f"Transcript file not found: {path}")

    entries: List[Dict[str, Any]] = []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    if not lines:
        return []

    is_antigravity = False
    is_ecc = False

    for idx, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except Exception as e:
            raise SchemaMismatchError(f"Line {idx+1} in {path.name} is not valid JSON: {e}")

        # Check schema type on first valid record
        if not is_antigravity and not is_ecc:
            if "step_index" in record and "type" in record:
                is_antigravity = True
            elif "tool_name" in record or "timestamp" in record or "prompt" in record:
                is_ecc = True
            else:
                raise SchemaMismatchError(
                    f"Unsupported transcript schema in {path.name}. Expected fields "
                    f"{{'step_index', 'type', 'content', 'source'}}. "
                    f"Please verify Antigravity IDE version or pass a canonical observations.jsonl."
                )

        if is_antigravity:
            # Validate Antigravity schema fields
            if "type" not in record or "step_index" not in record:
                raise SchemaMismatchError(
                    f"Line {idx+1} missing required fields ('step_index', 'type') in Antigravity transcript."
                )
        entries.append(record)

    return entries

def is_negative_stop_phrase(text: str) -> bool:
    """Return True if text contains conversational negative stop-phrases or question forms."""
    t_lower = text.lower().strip()
    
    # Direct check for question patterns
    if t_lower.endswith("?") or t_lower.startswith(("is it ", "can we ", "could you ", "why do ", "should we ")):
        return True

    for stop in NEGATIVE_STOP_PHRASES:
        if stop in t_lower:
            return True

    return False

def extract_direct_imperatives(text: str) -> List[Dict[str, Any]]:
    """
    Extract developer imperatives from user input using high-precision regex patterns.
    """
    results = []
    
    # Check negative stop phrases first
    if is_negative_stop_phrase(text):
        return []

    term = r"(?:\.(?:\s+|$)|[\n\r]|$)"
    patterns = [
        # "always <action> [because <reason>]"
        (
            rf"\b(?:always|make sure to always|ensure to always)\s+([^\n]+?)(?:\s+because\s+([^\n]+?))?{term}",
            "always",
            True
        ),
        # "never <action> [because <reason>]"
        (
            rf"\b(?:never|do not ever|don't ever)\s+([^\n]+?)(?:\s+because\s+([^\n]+?))?{term}",
            "never",
            True
        ),
        # "use <X> instead of <Y> [because <reason>]"
        (
            rf"\b(?:use|prefer)\s+([^\n]+?)\s+(?:instead of|rather than|over)\s+([^\n]+?)(?:\s+because\s+([^\n]+?))?{term}",
            "preference",
            False
        ),
        # "do not <X>, use <Y>"
        (
            rf"\b(?:do not|don't)\s+([^\n]+?),\s*(?:use|do)\s+([^\n]+?){term}",
            "correction",
            False
        ),
    ]

    for pat, directive_type, has_reason in patterns:
        for match in re.finditer(pat, text, re.IGNORECASE):
            groups = match.groups()
            raw_action = groups[0].strip() if len(groups) > 0 and groups[0] else ""
            if not raw_action or len(raw_action) < 4:
                continue

            # Check if negative stop phrase is inside action
            if is_negative_stop_phrase(raw_action):
                continue

            reason = ""
            if directive_type == "preference":
                target = groups[0].strip()
                instead_of = groups[1].strip() if len(groups) > 1 else ""
                reason = groups[2].strip() if len(groups) > 2 and groups[2] else ""
                action = f"Use {target} instead of {instead_of}"
                trigger = f"when choosing between {target} and {instead_of}"
                domain = "coding-style"
            elif directive_type == "correction":
                avoid = groups[0].strip()
                prefer = groups[1].strip()
                action = f"Use {prefer} instead of {avoid}"
                trigger = f"when working with {avoid}"
                domain = "workflow"
            elif directive_type == "always":
                reason = groups[1].strip() if len(groups) > 1 and groups[1] else ""
                action = f"Always {raw_action}"
                trigger = f"when handling {raw_action}"
                domain = "workflow"
            elif directive_type == "never":
                reason = groups[1].strip() if len(groups) > 1 and groups[1] else ""
                action = f"Never {raw_action}"
                trigger = f"when considering {raw_action}"
                domain = "workflow"
            else:
                action = raw_action
                trigger = "when relevant"
                domain = "general"

            slug = re.sub(r"[^a-z0-9]+", "-", action.lower()).strip("-")[:60]
            results.append({
                "id": slug,
                "title": action,
                "action": action,
                "trigger": trigger,
                "has_rationale": bool(reason),
                "rationale": reason,
                "domain": domain,
                "raw_text": text.strip(),
            })

    return results

def calculate_confidence(
    candidate: Dict[str, Any],
    existing_meta: Optional[Dict[str, Any]] = None
) -> Tuple[float, int]:
    """
    Calculate confidence based on the symmetric two-sighting trust gate:
    - 1st Sighting:
        - With rationale: 0.65 (held at gate)
        - Terse correction: 0.55 (held at gate)
        - Tool error recovery: 0.45 (held at gate)
    - 2nd Sighting / Reinforcement:
        - With rationale: 0.85 (promoted past 0.70 gate)
        - Terse correction: 0.70 (promoted)
        - Tool error recovery: 0.60 (held)
    """
    has_rationale = candidate.get("has_rationale", False)
    is_error_recovery = candidate.get("is_error_recovery", False)

    if existing_meta:
        # Reinforcement! Sighting >= 2
        prev_count = int(existing_meta.get("reinforcement_count", 1))
        new_count = prev_count + 1
        if is_error_recovery:
            conf = 0.60
        elif has_rationale:
            conf = 0.85
        else:
            conf = 0.70
        return conf, new_count

    # First sighting
    new_count = 1
    if is_error_recovery:
        conf = 0.45
    elif has_rationale:
        conf = 0.65
    else:
        conf = 0.55
    return conf, new_count

def mine_transcript(
    entries: List[Dict[str, Any]],
    project_id: str,
    project_name: str,
    homunculus_dir: Path
) -> List[Dict[str, Any]]:
    """
    Extract candidate instincts from parsed transcript entries and assign confidence.
    """
    candidates = []
    
    # 1. Parse user directives
    for entry in entries:
        content = entry.get("content", "")
        source = entry.get("source", "")
        entry_type = entry.get("type", "")

        # Look for explicit user input steps
        if entry_type in ("USER_INPUT", "prompt") or source in ("USER_EXPLICIT", "user"):
            if isinstance(content, str) and content.strip():
                directives = extract_direct_imperatives(content)
                candidates.extend(directives)

    # 2. Score candidates against existing homunculus files
    scoped_dir = homunculus_dir / "projects" / project_id / "instincts" / "personal"
    global_dir = homunculus_dir / "instincts" / "personal"

    processed = []
    for cand in candidates:
        cand_id = cand["id"]
        # Check if already exists in scoped or global
        existing_file = None
        for d in (scoped_dir, global_dir):
            target = d / f"{cand_id}.yaml"
            if target.exists():
                existing_file = target
                break

        existing_meta = None
        if existing_file:
            try:
                txt = existing_file.read_text(encoding="utf-8")
                # Parse frontmatter
                m = {}
                for line in txt.split("---")[1].splitlines():
                    if ":" in line:
                        k, v = line.split(":", 1)
                        m[k.strip()] = v.strip().strip("\"'")
                existing_meta = m
            except Exception:
                pass

        conf, count = calculate_confidence(cand, existing_meta)
        cand["confidence"] = conf
        cand["reinforcement_count"] = count
        cand["project_id"] = project_id
        cand["project_name"] = project_name
        cand["scope"] = "project"
        cand["status"] = "promotable" if conf >= 0.70 else "staged"
        processed.append(cand)

    return processed

def write_instinct_file(
    instinct: Dict[str, Any],
    homunculus_dir: Path,
    scope: str = "project"
) -> Path:
    """
    Persist instinct to homunculus directory with YAML frontmatter + markdown body.
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    project_id = instinct["project_id"]
    
    if scope == "project" and project_id:
        target_dir = homunculus_dir / "projects" / project_id / "instincts" / "personal"
    else:
        target_dir = homunculus_dir / "instincts" / "personal"

    target_dir.mkdir(parents=True, exist_ok=True)
    file_path = target_dir / f"{instinct['id']}.yaml"

    title = instinct["title"]
    action = instinct["action"]
    trigger = instinct["trigger"]
    conf = instinct["confidence"]
    count = instinct["reinforcement_count"]
    domain = instinct.get("domain", "workflow")
    rationale = instinct.get("rationale", "")

    evidence_text = f"- Observed user directive: \"{instinct.get('raw_text', title)}\"\n"
    if rationale:
        evidence_text += f"- Rationale provided: {rationale}\n"
    evidence_text += f"- Sighting #{count} recorded at {now_iso}\n"

    content = f"""---
id: "{instinct['id']}"
name: "{title}"
trigger: "{trigger}"
confidence: {conf}
domain: "{domain}"
source: "observe-pipeline"
scope: "{scope}"
project_id: "{project_id}"
reinforcement_count: {count}
updated_at: "{now_iso}"
---

# {title}

## Action
{action}

## Evidence
{evidence_text}
"""
    file_path.write_text(content, encoding="utf-8")
    return file_path

def main():
    parser = argparse.ArgumentParser(description="Continuous Learning v2 (CLv2) Native Windows Observer")
    parser.add_argument("--transcript", type=str, help="Path to transcript.jsonl or observations.jsonl")
    parser.add_argument("--project-dir", type=str, help="Root directory of the project")
    parser.add_argument("--dry-run", action="store_true", help="Preview extracted instincts without writing")
    parser.add_argument("--verbose", action="store_true", help="Print verbose extraction details")
    args = parser.parse_args()

    project_dir = Path(args.project_dir) if args.project_dir else Path.cwd()
    project_id, project_name = detect_project(project_dir)

    transcript_path = Path(args.transcript) if args.transcript else find_default_transcript()
    if not transcript_path:
        print("[observe.py] No transcript found. Run with --transcript <path>.", file=sys.stderr)
        sys.exit(0)

    try:
        entries = validate_and_parse_transcript(transcript_path)
    except SchemaMismatchError as err:
        print(f"[observe.py ERROR] {err}", file=sys.stderr)
        sys.exit(1)

    homunculus = get_homunculus_dir()
    instincts = mine_transcript(entries, project_id, project_name, homunculus)

    if not instincts:
        if args.verbose:
            print(f"[observe.py] Scanned {len(entries)} events in {transcript_path.name}: 0 new instincts discovered.")
        return

    print(f"[observe.py] Discovered {len(instincts)} candidate instinct(s) from {transcript_path.name}:")
    for inst in instincts:
        status_tag = f"PROMOTABLE (conf: {inst['confidence']})" if inst['confidence'] >= 0.70 else f"STAGED (conf: {inst['confidence']}, sighting: #{inst['reinforcement_count']})"
        print(f"  [{status_tag}] {inst['id']}: {inst['action']}")

        if not args.dry_run:
            out_file = write_instinct_file(inst, homunculus, scope="project")
            print(f"    -> Written to {out_file}")

if __name__ == "__main__":
    main()
