"""Describe sampled official UI curves; never reconstruct a replay from SVG.

Coordinates are rounded and rounds are downsampled. Counts below are counts of
drawn samples, not durations. No food, paid cost or pre-death length is inferred.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import itertools
import json
import math
from pathlib import Path
import re
from typing import Any


LABELS = {"dragons": "Dragons alive", "queen": "Queen length",
          "longest": "Longest dragon alive", "total": "Total team length"}
TABLE_LABELS = {"dragons": "Dragons alive", "queen": "Queen",
                "longest": "Longest now", "total": "Total length"}
NUMBER = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"
QUANTIZATION = 0.00500001  # Two-decimal SVG serialization, including float noise.
LIMITS = [
    "These are rounded, downsampled SVG samples, not raw per-round replay states.",
    "Adjacent drawn samples do not prove an unbroken lead between them; sample counts are never round durations.",
    "UI columns are named teams; they are not assumed to be engine Team A/B or Queen IDs.",
    "A Queen zero transition is associated with its displayed Dead(rN) annotation, not a recovered death event.",
    "Food, paid movement, exact pre-death length and death causality cannot be measured from these curves.",
    "Numeric intervals use the captured UI layout and two-decimal coordinate rounding; intermediate sample/window semantics remain unknown.",
]


class UIValidationError(ValueError):
    pass


def parse_path(path: str) -> list[tuple[float, float]]:
    """Read only the absolute M/L polylines observed in the official UI."""
    tokens = re.findall(r"[A-Za-z]|" + NUMBER, path)
    residue = re.sub(r"[ML]|" + NUMBER + r"|[\s,]", "", path)
    if residue or not tokens or tokens[0] != "M":
        raise UIValidationError("Only absolute, open M/L series polylines are supported")
    result, index = [], 0
    while index < len(tokens):
        if tokens[index] in ("M", "L"):
            index += 1
        if index + 1 >= len(tokens) or re.fullmatch(NUMBER, tokens[index]) is None or re.fullmatch(NUMBER, tokens[index + 1]) is None:
            raise UIValidationError("Malformed SVG series coordinate pair")
        point = float(tokens[index]), float(tokens[index + 1])
        if not all(math.isfinite(v) for v in point):
            raise UIValidationError("Nonfinite SVG coordinate")
        if result and point[0] <= result[-1][0]:
            raise UIValidationError("Series X coordinates must strictly increase")
        result.append(point)
        index += 2
    if len(result) < 2:
        raise UIValidationError("A series needs at least two samples")
    return result


def validate_layout(proof: dict[str, Any]) -> dict[str, Any]:
    """Check independently captured DOM tick positions, not the axis path top."""
    if proof.get("viewBox") != "0 0 100 42" or len(proof.get("ticks", [])) != 3:
        raise UIValidationError("Unsupported UI layout proof")
    height = float(proof["svgHeight"])
    if height <= 0 or abs(float(proof.get("svgTopWithinPlot", 0))) > 0.1:
        raise UIValidationError("SVG/tick reference origins do not match")
    positions = [float(str(t["topPixels"]).removesuffix("px")) * 42 / height for t in proof["ticks"]]
    if any(abs(a - b) > 0.02 for a, b in zip(positions, (7, 22, 37))):
        raise UIValidationError("DOM tick positions do not verify max=Y7, half=Y22, zero=Y37")
    return {"view_box": "0 0 100 42", "max_y": 7.0, "zero_y": 37.0,
            "dom_tick_y": positions, "basis": "captured_DOM_tick_positions"}


def _number(value: Any) -> int:
    text = str(value).strip().replace(",", "")
    if not re.fullmatch(r"\d+", text):
        raise UIValidationError(f"Noninteger UI count: {value!r}")
    return int(text)


def _terminal(data: dict[str, Any]) -> dict[str, Any]:
    table = next((t["rows"] for t in data.get("tables", []) if t.get("label") == "Current team statistics"), None)
    if not table or len(table[0]) != 3 or not all(table[0][1:]):
        raise UIValidationError("Two named current-statistics columns are required")
    names = list(table[0][1:])
    if names[0] == names[1]:
        raise UIValidationError("Duplicate team names cannot be attributed")
    rows = {r[0]: r[1:] for r in table[1:] if len(r) == 3}
    scores, deaths = [], []
    for column in range(2):
        score, dead_round = {}, None
        for metric, label in TABLE_LABELS.items():
            if label not in rows:
                raise UIValidationError(f"Missing terminal statistic {label}")
            value = str(rows[label][column]).strip()
            dead = re.fullmatch(r"Dead\s*\(r(\d+)\)", value) if metric == "queen" else None
            score[metric] = 0 if dead else _number(value)
            if dead:
                dead_round = int(dead[1])
        if not 0 <= score["queen"] <= score["longest"] <= score["total"]:
            raise UIValidationError("Terminal length hierarchy is inconsistent")
        if (score["dragons"] == 0) != (score["total"] == 0):
            raise UIValidationError("Terminal alive count and total length disagree")
        scores.append(score)
        deaths.append(dead_round)
    cursor = re.findall(r"\bRound\s+(\d+)\s*/\s*(\d+)\b", data.get("main", ""))
    cursor_now, cursor_end = tuple(map(int, cursor[-1])) if cursor else (None, None)
    eliminated = any(s["dragons"] == 0 for s in scores)
    terminated = cursor_now is not None and cursor_now == cursor_end and (cursor_end == 500 or eliminated)
    if eliminated:
        winner = 1 if scores[0]["dragons"] == 0 and scores[1]["dragons"] else 0 if scores[1]["dragons"] == 0 and scores[0]["dragons"] else None
        criterion = "elimination" if winner is not None else "tie"
    else:
        winner, criterion = None, "tie"
        for metric in ("queen", "longest", "total"):
            if scores[0][metric] != scores[1][metric]:
                winner, criterion = (0 if scores[0][metric] > scores[1][metric] else 1), metric
                break
    return {"column_names": names, "scores_by_column": scores, "queen_dead_ui_round_by_column": deaths,
            "cursor_round": cursor_now, "end_round": cursor_end, "terminated": terminated,
            "winner_column": winner if terminated else None, "criterion": criterion if terminated else "unknown"}


def _axis(chart: dict[str, Any], data: dict[str, Any]) -> tuple[float, float, float]:
    text = chart.get("axis_text")
    if not text:
        # Existing exports contain the same five labels in the STATS section.
        stats_text = data.get("main", "").split("STATS\n", 1)[-1].split("TOTALS THROUGH", 1)[0]
        pattern = re.escape(chart["label"]) + r"\s*\n" + r"\s*\n".join([r"([\d,]+(?:\.\d+)?)"] * 5)
        match = re.search(pattern, stats_text)
        if not match:
            raise UIValidationError(f"Missing five axis labels for {chart['label']}")
        labels = list(map(lambda n: float(n.replace(",", "")), match.groups()))
    else:
        labels = [float(s.replace(",", "")) for s in str(text).splitlines() if re.fullmatch(r"[\d,]+(?:\.\d+)?", s.strip())]
    if len(labels) != 5:
        raise UIValidationError("Axis text must expose Ymax, Yhalf, Yzero, Xstart, Xend")
    maximum, half, zero, start, end = labels
    if maximum <= 0 or zero != 0 or abs(half - maximum / 2) > 1e-6 or end <= start:
        raise UIValidationError("Unsupported or inconsistent axis labels")
    return maximum, start, end


def _interval(y: float, maximum: float) -> tuple[float, float]:
    return max(0.0, (37 - y - QUANTIZATION) * maximum / 30), max(0.0, (37 - y + QUANTIZATION) * maximum / 30)


def _integer_interval(y: float, maximum: float) -> tuple[int, int] | None:
    low, high = _interval(y, maximum)
    a, b = math.ceil(low - 1e-7), math.floor(high + 1e-7)
    return (a, b) if a <= b else None


def _round_interval(x: float, first: float, last: float, start: float, end: float) -> list[float]:
    # X serialization is rounded too. These remain UI-axis approximations.
    return [start + (x - first - QUANTIZATION) * (end - start) / (last - first),
            start + (x - first + QUANTIZATION) * (end - start) / (last - first)]


def _possible_order(ranges: dict[str, list[tuple[int, int]]]) -> tuple[list[int | None], list[str]]:
    """Conservative lexicographic comparison of quantized integer-count ranges."""
    leaders, criteria = set(), set()
    alive = [[False] if hi == 0 else [True] if lo > 0 else [False, True] for lo, hi in ranges["dragons"]]
    for a_alive, b_alive in itertools.product(*alive):
        if a_alive != b_alive:
            leaders.add(0 if a_alive else 1)
            criteria.add("elimination")
            continue
        if not a_alive:
            leaders.add(None)
            criteria.add("tie")
            continue
        equal_possible = True
        for metric in ("queen", "longest", "total"):
            if not equal_possible:
                break
            (al, ah), (bl, bh) = ranges[metric]
            if ah > bl:
                leaders.add(0); criteria.add(metric)
            if bh > al:
                leaders.add(1); criteria.add(metric)
            equal_possible = max(al, bl) <= min(ah, bh)
        if equal_possible:
            leaders.add(None); criteria.add("tie")
    return sorted(leaders, key=lambda x: -1 if x is None else x), sorted(criteria)


def analyze_ui(data: dict[str, Any], *, layout_proof: dict[str, Any], our_name: str | None = None,
               raw_report: dict[str, Any] | None = None, include_samples: bool = False) -> dict[str, Any]:
    if raw_report and raw_report.get("quality", {}).get("complete_match_verified") is True:
        return {"source_kind": "preferred_verified_raw_trajectory", "raw_report": raw_report,
                "ui_sampling_used_for_analysis": False}
    layout = validate_layout(layout_proof)
    terminal = _terminal(data)
    match = re.search(r"\bMatch\s+(\d+)\b", data.get("main", ""))
    issues, charts = [], {}
    colors = None
    for metric, label in LABELS.items():
        matches = [c for c in data.get("charts", []) if c.get("label") == label]
        if len(matches) != 1:
            raise UIValidationError(f"Exactly one {label} chart is required")
        chart = matches[0]
        if chart.get("viewBox") != layout["view_box"]:
            raise UIValidationError("SVG viewBox differs from captured layout proof")
        series = [p for p in chart.get("paths", []) if "series" in str(p.get("class", "")).split()]
        if len(series) != 2:
            raise UIValidationError(f"Two team series are required for {label}")
        fingerprints = [p.get("stroke") or p.get("style") for p in series]
        if not all(fingerprints) or fingerprints[0] == fingerprints[1]:
            raise UIValidationError("Distinct series colors are required to align charts")
        if colors is None:
            colors = fingerprints
        if set(fingerprints) != set(colors):
            raise UIValidationError("Team colors differ across charts")
        points = [parse_path(series[fingerprints.index(color)]["d"]) for color in colors]
        maximum, start, end = _axis(chart, data)
        if any(y < 7 - QUANTIZATION or y > 37 + QUANTIZATION for line in points for _, y in line):
            raise UIValidationError("Series is outside the verified numeric plot range")
        charts[metric] = {"points": points, "maximum": maximum, "start": start, "end": end}
    grids = [[x for x, _ in line] for chart in charts.values() for line in chart["points"]]
    reference = grids[0]
    if any(len(g) != len(reference) or any(abs(a - b) > 1e-7 for a, b in zip(g, reference)) for g in grids):
        raise UIValidationError("Four metrics must have identical drawn sample X positions; no interpolation is performed")
    axis_ranges = {(c["start"], c["end"]) for c in charts.values()}
    if len(axis_ranges) != 1:
        raise UIValidationError("Four charts expose different round-axis ranges")
    start, end = next(iter(axis_ranges))
    if abs(reference[0] - 5) > QUANTIZATION or abs(reference[-1] - 95) > QUANTIZATION:
        raise UIValidationError("Drawn endpoints do not verify the observed X5..X95 layout")
    if terminal["cursor_round"] is not None and end != terminal["cursor_round"]:
        raise UIValidationError("Chart range ends at a different displayed cursor round")
    candidates = []
    for mapping in ((0, 1), (1, 0)):  # rendered color index -> named UI column
        endpoint_match = all(_interval(chart["points"][series][-1][1], chart["maximum"])[0] - 1e-7
            <= terminal["scores_by_column"][column][metric]
            <= _interval(chart["points"][series][-1][1], chart["maximum"])[1] + 1e-7
            for metric, chart in charts.items() for series, column in enumerate(mapping))
        if endpoint_match:
            candidates.append(mapping)
    if len(candidates) != 1:
        issues.append("Endpoint attribution is ambiguous" if candidates else "Curve endpoints do not reconcile with the named terminal columns")
    mapping = candidates[0] if len(candidates) == 1 else None
    queen_transitions = []
    queen_chart = charts["queen"]
    for series, points in enumerate(queen_chart["points"]):
        zero = next((i for i, (_, y) in enumerate(points) if abs(y - 37) <= QUANTIZATION), None)
        persistent = zero is not None and all(abs(y - 37) <= QUANTIZATION for _, y in points[zero:])
        bracket = None if zero is None else [
            _round_interval(points[max(0, zero - 1)][0], reference[0], reference[-1], start, end)[0],
            _round_interval(points[zero][0], reference[0], reference[-1], start, end)[1]]
        queen_transitions.append({"series_index": series, "first_rendered_zero_sample": zero,
            "zero_persists_in_later_samples": persistent, "ui_axis_transition_bracket": bracket})
    if mapping is None and len(candidates) == 2:
        compatible = []
        for candidate in candidates:
            if all((terminal["queen_dead_ui_round_by_column"][column] is None
                    and queen_transitions[series]["first_rendered_zero_sample"] is None)
                   or (terminal["queen_dead_ui_round_by_column"][column] is not None
                    and queen_transitions[series]["zero_persists_in_later_samples"]
                    and queen_transitions[series]["ui_axis_transition_bracket"][0] <= terminal["queen_dead_ui_round_by_column"][column]
                    <= queen_transitions[series]["ui_axis_transition_bracket"][1])
                   for series, column in enumerate(candidate)):
                compatible.append(candidate)
        if len(compatible) == 1:
            mapping = compatible[0]
            issues = [i for i in issues if i != "Endpoint attribution is ambiguous"]
    samples = []
    discrete_consistent = True
    for index, x in enumerate(reference):
        ranges = {metric: [_integer_interval(line[index][1], chart["maximum"]) for line in chart["points"]]
                  for metric, chart in charts.items()}
        if any(r is None for pair in ranges.values() for r in pair):
            discrete_consistent = False
            leader, axes, possible = None, [], [0, 1, None]
        else:
            possible, axes = _possible_order(ranges)
            leader = possible[0] if len(possible) == 1 else None
        named_possible = [None if p is None else terminal["column_names"][mapping[p]] for p in possible] if mapping else None
        sample = {"sample_index": index, "svg_x": x, "approximate_ui_axis_interval":
            _round_interval(x, reference[0], reference[-1], start, end),
            "order_resolved": len(possible) == 1, "leader_series": leader,
            "leader_name": terminal["column_names"][mapping[leader]] if mapping is not None and leader is not None else None,
            "possible_leader_names": named_possible, "possible_deciding_axes": axes}
        samples.append(sample)
    if not discrete_consistent:
        issues.append("Some rendered ordinates are inconsistent with integer counts at the verified scale; those sample orders remain unresolved")
    for transition in queen_transitions:
        column = mapping[transition["series_index"]] if mapping is not None else None
        transition["column_name"] = terminal["column_names"][column] if column is not None else None
        transition["displayed_dead_ui_round"] = terminal["queen_dead_ui_round_by_column"][column] if column is not None else None
        zero = transition["first_rendered_zero_sample"]
        transition["nearest_sample_order_before"] = samples[zero - 1] if zero is not None and zero > 0 else None
        transition["first_zero_sample_order"] = samples[zero] if zero is not None else None
        transition["dead_annotation_within_sample_bracket"] = (None if column is None or transition["displayed_dead_ui_round"] is None or transition["ui_axis_transition_bracket"] is None else
            transition["ui_axis_transition_bracket"][0] <= transition["displayed_dead_ui_round"] <= transition["ui_axis_transition_bracket"][1])
        if column is not None and transition["displayed_dead_ui_round"] is not None and transition["dead_annotation_within_sample_bracket"] is not True:
            issues.append(f"Queen zero transition does not bracket {transition['column_name']}'s displayed death annotation")
    own_column = terminal["column_names"].index(our_name) if our_name in terminal["column_names"] else None
    own_leading = [s["sample_index"] for s in samples if s["order_resolved"] and s["leader_name"] == our_name] if own_column is not None else []
    outcome = ("unknown" if own_column is None or not terminal["terminated"] else "draw" if terminal["winner_column"] is None else
               "win" if terminal["winner_column"] == own_column else "loss")
    counts = Counter("unresolved" if not s["order_resolved"] else "unattributed" if mapping is None and s["leader_series"] is not None else s["leader_name"] for s in samples)
    changes = []
    if mapping is not None:
        for previous, current in zip(samples, samples[1:]):
            if previous["order_resolved"] and current["order_resolved"] and previous["leader_name"] != current["leader_name"]:
                changes.append({"previous_sample_index": previous["sample_index"], "sample_index": current["sample_index"],
                    "previous_leader_name": previous["leader_name"], "leader_name": current["leader_name"],
                    "ui_axis_bracket_between_samples": [previous["approximate_ui_axis_interval"][0], current["approximate_ui_axis_interval"][1]],
                    "scope": "Order differs at these two drawn samples; intervening turns are not reconstructed"})
    phase_counts = {}
    if mapping is not None:
        thresholds = {name + "_queen_displayed_dead": dead for name, dead in
                      zip(terminal["column_names"], terminal["queen_dead_ui_round_by_column"]) if dead is not None}
        if all(dead is not None for dead in terminal["queen_dead_ui_round_by_column"]):
            thresholds["both_queens_displayed_dead"] = max(terminal["queen_dead_ui_round_by_column"])
        for phase, threshold in thresholds.items():
            post = [s for s in samples if s["approximate_ui_axis_interval"][0] > threshold]
            phase_counts[phase] = {"displayed_dead_ui_round": threshold, "drawn_samples_after_annotation": len(post),
                "sample_order_counts": dict(Counter("unresolved" if not s["order_resolved"] else s["leader_name"] or "tie" for s in post)),
                "scope": "Samples whose entire projected X interval is after the UI death annotation; no event causality"}
    result = {"source_kind": "sampled_ui_svg", "match_id": int(match[1]) if match else None,
        "quality": {"issues": issues, "series_to_named_column_verified": mapping is not None,
                    "layout_basis": layout, "discrete_count_consistency": discrete_consistent,
                    "round_samples_are_complete": False, "point_or_window_semantics": "not_recovered",
                    "sample_order_basis": "Integer-count intervals consistent with the rendered ordinates; not verified per-round states",
                    "terminal_endpoints_checked": True},
        "terminal_ui": terminal, "our_name": our_name, "outcome": outcome,
        "sampling": {"drawn_samples": len(reference), "ui_axis_start": start, "ui_axis_end": end,
                     "svg_serialization_decimals": 2, "unsampled_intervals_exist": end - start + 1 > len(reference)},
        "series_colors": colors, "series_to_ui_column": list(mapping) if mapping is not None else None,
        "sample_order_counts_by_name": {"tie" if k is None else str(k): v for k, v in counts.items()},
        "sampled_own_lead_then_terminal_loss": bool(own_leading) and outcome == "loss" if mapping is not None and own_column is not None else None,
        "first_own_leading_sample": own_leading[0] if own_leading else None,
        "last_own_leading_sample": own_leading[-1] if own_leading else None,
        "rendered_sample_order_changes": changes, "sample_orders_after_displayed_queen_deaths": phase_counts,
        "queen_rendered_zero_transitions": queen_transitions, "measurement_limits": LIMITS}
    if include_samples:
        result["sample_orders"] = samples
    return result


def aggregate(reports: list[dict[str, Any]]) -> dict[str, Any]:
    usable = [r for r in reports if r.get("source_kind") == "sampled_ui_svg" and r["quality"]["series_to_named_column_verified"]]
    losses = [r for r in usable if r["outcome"] == "loss"]
    return {"records": len(reports), "usable_sampled_ui_records": len(usable),
            "errors_or_missing_charts": sum("error" in r for r in reports),
            "verified_raw_preferred": sum(r.get("source_kind") == "preferred_verified_raw_trajectory" for r in reports),
            "sampled_losses": len(losses),
            "records_with_quality_issues": sum(bool(r.get("quality", {}).get("issues")) for r in usable),
            "losses_with_a_sampled_own_lead": sum(r["sampled_own_lead_then_terminal_loss"] is True for r in losses),
            "scope": "Acquired, usable UI subset only; sampled lead is not continuous lead or proven whole-match cause"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("--layout-proof", type=Path, required=True)
    parser.add_argument("--our-name")
    parser.add_argument("--our-team-id", help="Resolve our name through saved team links, without inferring engine side")
    parser.add_argument("--raw-report-dir", type=Path, help="Prefer verified trajectory reports named <match-id>.json")
    parser.add_argument("--include-samples", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    proof = json.loads(args.layout_proof.read_text(encoding="utf-8-sig"))
    reports = []
    for path in args.inputs:
        try:
            raw = path.read_bytes()
            data = json.loads(raw.decode("utf-8-sig"))
            our_name = args.our_name
            if args.our_team_id:
                names = {link.get("text", "").strip() for link in data.get("links", [])
                         if re.search(r"/teams/" + re.escape(args.our_team_id) + r"(?:$|[/?#])", link.get("href", ""))}
                if len(names) != 1:
                    raise UIValidationError("Our team link does not identify exactly one name")
                linked = next(iter(names))
                if our_name is not None and our_name != linked:
                    raise UIValidationError("Explicit name differs from saved team link")
                our_name = linked
            match = re.search(r"\bMatch\s+(\d+)\b", data.get("main", ""))
            raw_path = args.raw_report_dir / f"{match[1]}.json" if args.raw_report_dir and match else None
            raw_report = json.loads(raw_path.read_text(encoding="utf-8-sig")) if raw_path and raw_path.exists() else None
            report = analyze_ui(data, layout_proof=proof, our_name=our_name, raw_report=raw_report, include_samples=args.include_samples)
            report["source"] = {"path": str(path.resolve()), "sha256": hashlib.sha256(raw).hexdigest(),
                                "layout_proof_path": str(args.layout_proof.resolve()),
                                "layout_proof_sha256": hashlib.sha256(args.layout_proof.read_bytes()).hexdigest()}
        except (ValueError, KeyError, TypeError, OSError) as error:
            report = {"source_path": str(path.resolve()), "error": str(error)}
        reports.append(report)
    output = json.dumps({"aggregate": aggregate(reports), "matches": reports}, ensure_ascii=False, indent=2)
    if args.out:
        args.out.write_text(output + "\n", encoding="utf-8")
    else:
        print(output)


if __name__ == "__main__":
    main()
