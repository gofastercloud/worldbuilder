#!/usr/bin/env python3
"""Record and summarise per-world fal.ai generation usage, tokens, and estimated costs.

Zero runtime dependencies: uses the standard library plus the vendored PyYAML in
`world-validate/scripts/vendor/`.

Ledger path: `<project-dir>/output/art-usage.yaml`
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any

# Share the vendored PyYAML from world-validate/scripts/vendor
_VENDOR = Path(__file__).resolve().parents[2] / "world-validate" / "scripts" / "vendor"
if _VENDOR.is_dir() and str(_VENDOR) not in sys.path:
    sys.path.insert(0, str(_VENDOR))

import yaml  # noqa: E402

LEDGER_REL = Path("output") / "art-usage.yaml"


def _ledger_path(project_dir: Path) -> Path:
    return project_dir / LEDGER_REL


def load_ledger(project_dir: Path) -> dict[str, Any]:
    path = _ledger_path(project_dir)
    if not path.is_file():
        return {"version": 1, "currency": "USD", "totals": _empty_totals(), "by_model": {}, "runs": []}
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return {"version": 1, "currency": "USD", "totals": _empty_totals(), "by_model": {}, "runs": []}
    runs = raw.get("runs")
    if not isinstance(runs, list):
        runs = []
    return {
        "version": int(raw.get("version", 1)),
        "currency": str(raw.get("currency", "USD")),
        "totals": _compute_totals(runs),
        "by_model": _compute_by_model(runs),
        "runs": runs,
    }


def _empty_totals() -> dict[str, Any]:
    return {
        "generations": 0,
        "total_tokens": 0,
        "total_megapixels": 0.0,
        "total_estimated_cost_usd": 0.0,
    }


def _compute_totals(runs: list[dict[str, Any]]) -> dict[str, Any]:
    gens = len(runs)
    tokens = sum(int(r.get("tokens_used") or 0) for r in runs)
    mp = round(sum(float(r.get("megapixels") or 0.0) for r in runs), 4)
    cost = round(sum(float(r.get("estimated_cost_usd") or 0.0) for r in runs), 6)
    return {
        "generations": gens,
        "total_tokens": tokens,
        "total_megapixels": mp,
        "total_estimated_cost_usd": cost,
    }


def _compute_by_model(runs: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for r in runs:
        ep = str(r.get("endpoint_id") or "unknown")
        grouped.setdefault(ep, []).append(r)
    return {ep: _compute_totals(grouped[ep]) for ep in sorted(grouped)}


def record_run(
    project_dir: Path,
    *,
    entity: str,
    endpoint_id: str,
    request_id: str | None = None,
    seed: int | None = None,
    width: int | None = None,
    height: int | None = None,
    tokens_used: int = 0,
    unit_price_usd: float | None = None,
    unit_type: str = "megapixels",
    units: float | None = None,
    estimated_cost_usd: float | None = None,
    output_file: str | None = None,
    notes: str | None = None,
    timestamp: str | None = None,
) -> dict[str, Any]:
    """Append one fal.ai generation record to `<project-dir>/output/art-usage.yaml`."""
    if not (project_dir / "project.yaml").is_file():
        raise FileNotFoundError(f"no project.yaml in {project_dir}")

    ledger = load_ledger(project_dir)

    mp = round((width * height) / 1_000_000.0, 4) if (width and height) else 0.0
    if units is None:
        if unit_type == "megapixels" and mp > 0:
            units = mp
        elif unit_type == "tokens" and tokens_used > 0:
            units = float(tokens_used)
        else:
            units = 1.0

    if estimated_cost_usd is None and unit_price_usd is not None:
        estimated_cost_usd = round(float(unit_price_usd) * float(units), 6)
    elif estimated_cost_usd is not None:
        estimated_cost_usd = round(float(estimated_cost_usd), 6)
    else:
        estimated_cost_usd = 0.0

    entry: dict[str, Any] = {
        "timestamp": timestamp or dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "entity": entity,
        "endpoint_id": endpoint_id,
    }
    if request_id:
        entry["request_id"] = request_id
    if seed is not None:
        entry["seed"] = int(seed)
    if width and height:
        entry["width"] = int(width)
        entry["height"] = int(height)
        entry["megapixels"] = mp
    if tokens_used:
        entry["tokens_used"] = int(tokens_used)
    entry["unit_type"] = unit_type
    entry["units"] = round(float(units), 4)
    if unit_price_usd is not None:
        entry["unit_price_usd"] = float(unit_price_usd)
    entry["estimated_cost_usd"] = estimated_cost_usd
    if output_file:
        entry["output_file"] = output_file
    if notes:
        entry["notes"] = notes

    ledger["runs"].append(entry)
    ledger["totals"] = _compute_totals(ledger["runs"])
    ledger["by_model"] = _compute_by_model(ledger["runs"])

    out_path = _ledger_path(project_dir)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(yaml.safe_dump(ledger, sort_keys=False), encoding="utf-8")
    return ledger


def _format_summary(ledger: dict[str, Any]) -> str:
    t = ledger["totals"]
    lines = [
        f"Generations: {t['generations']}",
        f"Total tokens: {t['total_tokens']}",
        f"Total megapixels: {t['total_megapixels']:.4f} MP",
        f"Estimated cost: ${t['total_estimated_cost_usd']:.6f} {ledger.get('currency', 'USD')}",
    ]
    by_model = ledger.get("by_model") or {}
    if by_model:
        lines.append("")
        lines.append("By model:")
        for ep, mt in by_model.items():
            lines.append(
                f"  - {ep}: {mt['generations']} run(s), {mt['total_tokens']} tokens, "
                f"{mt['total_megapixels']:.4f} MP, ${mt['total_estimated_cost_usd']:.6f}"
            )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Track fal.ai token and cost usage per world project.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    rec = sub.add_parser("record", help="Record a completed fal.ai generation")
    rec.add_argument("project", type=Path, help="World project directory containing project.yaml")
    rec.add_argument("--entity", required=True, help="Entity path e.g. characters/seren-voss")
    rec.add_argument("--endpoint", required=True, help="fal.ai endpoint ID e.g. fal-ai/flux/schnell")
    rec.add_argument("--request-id", default=None, help="fal.ai request_id")
    rec.add_argument("--seed", type=int, default=None, help="Returned generation seed")
    rec.add_argument("--width", type=int, default=None, help="Output image width in pixels")
    rec.add_argument("--height", type=int, default=None, help="Output image height in pixels")
    rec.add_argument("--tokens", type=int, default=0, help="Tokens used (if billed or reported in tokens)")
    rec.add_argument("--unit-price", type=float, default=None, help="Unit price in USD")
    rec.add_argument("--unit", default="megapixels", help="Billing unit (megapixels, images, tokens, seconds)")
    rec.add_argument("--units", type=float, default=None, help="Explicit billed unit quantity")
    rec.add_argument("--cost-usd", type=float, default=None, help="Explicit estimated or actual cost in USD")
    rec.add_argument("--output-file", default=None, help="Relative path to saved image file")
    rec.add_argument("--notes", default=None, help="Optional notes")
    rec.add_argument("--json", action="store_true", help="Output updated ledger totals as JSON")

    summ = sub.add_parser("summary", help="Show accumulated usage and costs for a world project")
    summ.add_argument("project", type=Path, help="World project directory containing project.yaml")
    summ.add_argument("--json", action="store_true", help="Output full ledger as JSON")

    args = parser.parse_args(argv)
    project_dir: Path = args.project.resolve()

    if args.cmd == "record":
        try:
            ledger = record_run(
                project_dir,
                entity=args.entity,
                endpoint_id=args.endpoint,
                request_id=args.request_id,
                seed=args.seed,
                width=args.width,
                height=args.height,
                tokens_used=args.tokens,
                unit_price_usd=args.unit_price,
                unit_type=args.unit,
                units=args.units,
                estimated_cost_usd=args.cost_usd,
                output_file=args.output_file,
                notes=args.notes,
            )
        except FileNotFoundError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        if args.json:
            print(json.dumps({"totals": ledger["totals"], "by_model": ledger["by_model"]}, indent=2))
        else:
            print(f"Recorded {args.entity} ({args.endpoint}) in {_ledger_path(project_dir)}")
            print(_format_summary(ledger))
        return 0

    if args.cmd == "summary":
        if not (project_dir / "project.yaml").is_file():
            print(f"error: no project.yaml in {project_dir}", file=sys.stderr)
            return 1
        ledger = load_ledger(project_dir)
        if args.json:
            print(json.dumps(ledger, indent=2))
        else:
            print(_format_summary(ledger))
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
