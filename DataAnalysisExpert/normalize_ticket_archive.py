from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any


NOISE_PATTERNS = (
    re.compile(r"^unknown$", re.IGNORECASE),
    re.compile(r"^hst\s*#", re.IGNORECASE),
    re.compile(r"purchase order", re.IGNORECASE),
    re.compile(r"^coolman fuels$", re.IGNORECASE),
    re.compile(r"^wholesale marketer$", re.IGNORECASE),
)

GENERIC_WORDS = {
    "and",
    "co",
    "company",
    "corp",
    "corporation",
    "limited",
    "ltd",
    "inc",
    "incorporated",
    "storage",
    "produce",
    "club",
    "golf",
    "farm",
    "farms",
    "fuels",
    "service",
    "services",
    "group",
    "exeter",
}

PREVIEW_PREFIX = "/ticket-previews/"


@dataclass(frozen=True)
class Candidate:
    account: str
    canonical: str
    current: str
    count: int
    reason: str
    score: float


def text(value: Any) -> str:
    return str(value or "").strip()


def normalize_name(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", " ", text(value).lower())
    return re.sub(r"\s+", " ", cleaned).strip()


def compact_name(value: str) -> str:
    return normalize_name(value).replace(" ", "")


def token_set(value: str) -> set[str]:
    return {
        token
        for token in normalize_name(value).split()
        if token and token not in GENERIC_WORDS
    }


def similarity(left: str, right: str) -> float:
    if not left or not right:
        return 0.0
    return SequenceMatcher(a=compact_name(left), b=compact_name(right)).ratio()


def classify_mismatch(current: str, canonical: str) -> tuple[bool, str, float]:
    raw_current = text(current)
    raw_canonical = text(canonical)
    if not raw_current or not raw_canonical:
        return False, "", 0.0

    current_norm = normalize_name(raw_current)
    canonical_norm = normalize_name(raw_canonical)
    if current_norm == canonical_norm:
        return False, "", 1.0

    score = similarity(raw_current, raw_canonical)
    current_tokens = token_set(raw_current)
    canonical_tokens = token_set(raw_canonical)
    token_overlap = len(current_tokens & canonical_tokens)
    subset_match = bool(current_tokens) and current_tokens <= canonical_tokens

    for pattern in NOISE_PATTERNS:
        if pattern.search(raw_current):
            return True, "generic_noise", score

    if subset_match and (token_overlap >= 1 or score >= 0.5):
        return True, "partial_name", score

    if score >= 0.84:
        return True, "ocr_near_match", score

    if token_overlap >= 2 and score >= 0.68:
        return True, "token_overlap", score

    if canonical_norm in current_norm or current_norm in canonical_norm:
        return True, "substring_match", score

    return False, "", score


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_account_map(
    customer_groups: list[dict[str, Any]],
) -> tuple[dict[str, str], dict[str, list[str]]]:
    grouped_names: dict[str, set[str]] = defaultdict(set)
    for group in customer_groups:
        canonical = text(group.get("customer"))
        if not canonical:
            continue
        for account_value in group.get("accounts", []):
            account = text(account_value)
            if account:
                grouped_names[account].add(canonical)

    resolved = {
        account: next(iter(names))
        for account, names in grouped_names.items()
        if len(names) == 1
    }
    ambiguous = {
        account: sorted(names)
        for account, names in grouped_names.items()
        if len(names) > 1
    }
    return resolved, ambiguous


def audit_candidates(
    data: dict[str, Any],
) -> tuple[list[Candidate], dict[str, str], dict[str, list[str]]]:
    account_map, ambiguous_accounts = build_account_map(
        data["customer_groups"]
    )
    grouped_counts: Counter[tuple[str, str, str]] = Counter()
    for row in data["tickets"]:
        account = text(row.get("account"))
        canonical = account_map.get(account)
        if not canonical:
            continue
        current = text(row.get("customer"))
        grouped_counts[(account, canonical, current)] += 1

    candidates: list[Candidate] = []
    for (account, canonical, current), count in sorted(grouped_counts.items()):
        if current == canonical:
            continue
        should_fix, reason, score = classify_mismatch(current, canonical)
        if not should_fix:
            reason = "grouped_account_override"
        candidates.append(
            Candidate(account, canonical, current, count, reason, score)
        )
    candidates.sort(
        key=lambda item: (item.account, item.canonical, item.current)
    )
    return candidates, account_map, ambiguous_accounts


def write_report(
    report_path: Path,
    candidates: list[Candidate],
    ambiguous_accounts: dict[str, list[str]],
) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "Ticket archive customer normalization audit",
        "",
        f"Candidate mismatches: {len(candidates)}",
        f"Ambiguous grouped accounts skipped: {len(ambiguous_accounts)}",
        "",
    ]

    if candidates:
        lines.extend([
            "Candidates:",
            "account | canonical | current | rows | reason | similarity",
            "--- | --- | --- | ---: | --- | ---:",
        ])
        for item in candidates:
            lines.append(
                " | ".join(
                    [
                        item.account,
                        item.canonical,
                        item.current or "[blank]",
                        str(item.count),
                        item.reason,
                        f"{item.score:.3f}",
                    ]
                )
            )
        lines.append("")

    if ambiguous_accounts:
        lines.extend([
            "Ambiguous grouped accounts skipped:",
            "account | grouped customer names",
            "--- | ---",
        ])
        for account, names in sorted(ambiguous_accounts.items()):
            lines.append(f"{account} | {', '.join(names)}")
        lines.append("")

    report_path.write_text("\n".join(lines), encoding="utf-8")


def apply_customer_normalization(
    data: dict[str, Any],
    candidates: list[Candidate],
) -> int:
    replacement_map = {
        (item.account, item.current): item.canonical for item in candidates
    }
    changes = 0
    for row in data["tickets"]:
        account = text(row.get("account"))
        current = text(row.get("customer"))
        canonical = replacement_map.get((account, current))
        if canonical and current != canonical:
            row["customer"] = canonical
            changes += 1
    return changes


def rewrite_preview_paths(data: dict[str, Any]) -> int:
    changes = 0
    for row in data["tickets"]:
        for field_name in ("page_url", "preview_url"):
            current = text(row.get(field_name))
            if not current or current.startswith(PREVIEW_PREFIX):
                continue
            filename = current.rsplit("/", 1)[-1]
            new_value = PREVIEW_PREFIX + filename
            if current != new_value:
                row[field_name] = new_value
                changes += 1
    return changes


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Audit and normalize ticket archive customer mismatches "
            "using grouped account mappings."
        )
    )
    parser.add_argument(
        "--data",
        default="tickets-data.json",
        help="Path to the ticket archive JSON file.",
    )
    parser.add_argument(
        "--report",
        default="DataAnalysisExpert/ocr-normalization-report.md",
        help="Where to write the candidate mismatch report.",
    )
    parser.add_argument(
        "--apply-customers",
        action="store_true",
        help="Apply the detected grouped-customer normalizations.",
    )
    parser.add_argument(
        "--apply-preview-paths",
        action="store_true",
        help="Rewrite preview paths to the /ticket-previews/ prefix.",
    )
    args = parser.parse_args()

    data_path = Path(args.data).expanduser().resolve()
    report_path = Path(args.report).expanduser().resolve()
    data = load_json(data_path)
    candidates, _, ambiguous_accounts = audit_candidates(data)
    write_report(report_path, candidates, ambiguous_accounts)

    customer_changes = 0
    preview_changes = 0
    if args.apply_customers:
        customer_changes = apply_customer_normalization(data, candidates)
    if args.apply_preview_paths:
        preview_changes = rewrite_preview_paths(data)

    if customer_changes or preview_changes:
        data_path.write_text(
            json.dumps(data, indent=2) + "\n",
            encoding="utf-8",
        )
        data = load_json(data_path)
        candidates, _, ambiguous_accounts = audit_candidates(data)
        write_report(report_path, candidates, ambiguous_accounts)

    print(f"report={report_path}")
    print(f"candidates={len(candidates)}")
    print(f"customer_changes={customer_changes}")
    print(f"preview_path_changes={preview_changes}")
    print(f"ambiguous_accounts={len(ambiguous_accounts)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
