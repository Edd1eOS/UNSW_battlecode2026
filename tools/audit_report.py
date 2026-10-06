"""Generate an evidence review from offline online-game audits and sampled UI curves.

This is a discovery report, not a candidate win-rate acceptance experiment.
Every denominator, missing record, and linked-series cluster stays explicit.
Never runs a browser, bot, engine, network request, or opponent code.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import statistics


AXES = {"elimination": "消灭", "queen": "Queen长度", "longest": "最长单位",
        "total_length": "总长度", "draw": "平局", "both_eliminated": "双方消灭"}
DEATHS = {"wall": "撞墙/海带", "self_body": "自撞身体", "other_body": "其他身体",
          "head_collision": "头碰头", "invalid_action": "无有效动作", "unknown": "未知"}
EVENTS = {"deaths": "单位死亡", "death_wall": "撞墙/海带死亡", "death_self_body": "自撞身体死亡",
          "death_other_body": "其他身体死亡", "death_head_collision": "头碰头死亡",
          "death_invalid_action": "无有效动作死亡", "splits": "成功分裂",
          "sprint_attempts": "冲刺尝试", "sonar_pings": "声呐"}


def _median(values):
    values = [v for v in values if v is not None]
    return statistics.median(values) if values else None


def _terminal(row):
    return "error" not in row and (row.get("result") or {}).get("terminated") is True and row.get("outcome") in ("win", "loss", "draw")


def _score(row, own=True):
    side = row.get("our_team")
    if side not in ("A", "B"): return {}
    if not own: side = "B" if side == "A" else "A"
    return (row.get("result") or {}).get("team" + side) or {}


def _counts(row, own=True):
    side = row.get("our_team")
    if side not in ("A", "B"): return {}
    if not own: side = "B" if side == "A" else "A"
    return (row.get("teams") or {}).get(side) or {}


def _selection_names(row):
    cells = (row.get("selected_table_row") or {}).get("cells", [])
    if len(cells) < 6: return None, None
    team_id = row.get("our_team_id")
    links = (row.get("selected_table_row") or {}).get("links", [])
    ours = next((x.get("text", "").split("\n")[0].strip() for x in links
                 if re.search(r"/teams/" + re.escape(str(team_id)) + r"(?:$|[/?#])", x.get("href", ""))), None)
    left, right = cells[2].split("\n")[0].strip(), cells[4].split("\n")[0].strip()
    opponent = right if left == ours else left if right == ours else None
    return cells[5].strip(), opponent


def _identity(row):
    selected_map, selected_opponent = _selection_names(row)
    return row.get("map") or selected_map or "未知", row.get("opponent") or selected_opponent or "未知"


def _queen_death(row):
    death = (row.get("queen") or {}).get("death") or {}
    return {"round": death.get("round"), "reason": death.get("reason") or "unknown",
            "evidence": death.get("evidence"), "id": (row.get("queen") or {}).get("id")}


def _peak(row):
    value = (row.get("team_longest_so_far") or {}).get(row.get("our_team"))
    terminal = _score(row).get("longestDragon")
    return {"historical_team_max": value, "terminal_team_max": terminal,
            "difference": value - terminal if value is not None and terminal is not None else None,
            "scope": "Two team maxima at different times; not one dragon's death loss or net resource cost"}


def _events_total(rows, own):
    result = {}
    for key in EVENTS:
        values = [_counts(r, own).get(key) for r in rows]
        known = [v for v in values if v is not None]
        result[key] = {"sum": sum(known) if known else None, "records_measured": len(known)}
    return result


def summarize(rows):
    terminal = [r for r in rows if _terminal(r)]
    dead = [r for r in terminal if _score(r).get("queenLength") == 0]
    losses = [r for r in terminal if r["outcome"] == "loss"]
    rounds = [_queen_death(r)["round"] for r in dead]
    longest_losses = [r for r in losses if (r.get("direct_cause") or {}).get("score_axis") == "longest"]
    longest_peak_measured = [r for r in longest_losses if _peak(r)["historical_team_max"] is not None]
    return {"selected_games": len(rows), "terminal_games": len(terminal),
        "selected_table_outcomes": dict(Counter(r.get("selected_table_outcome") or "unknown" for r in rows)),
        "terminal_outcomes": dict(Counter(r["outcome"] for r in terminal)),
        "terminal_losses": len(losses),
        "loss_score_axes": dict(Counter((r.get("direct_cause") or {}).get("score_axis") or "unknown" for r in losses)),
        "own_queen_alive": sum(_score(r).get("queenLength", 0) > 0 for r in terminal),
        "opponent_queen_alive": sum(_score(r, False).get("queenLength", 0) > 0 for r in terminal),
        "own_alive_queen_length_median": _median(_score(r).get("queenLength") for r in terminal if _score(r).get("queenLength", 0) > 0),
        "opponent_alive_queen_length_median": _median(_score(r, False).get("queenLength") for r in terminal if _score(r, False).get("queenLength", 0) > 0),
        "own_terminal_dragons_median": _median(_score(r).get("dragonCount") for r in terminal),
        "opponent_terminal_dragons_median": _median(_score(r, False).get("dragonCount") for r in terminal),
        "own_eliminated_games": sum(_score(r).get("dragonCount") == 0 for r in terminal),
        "opponent_eliminated_games": sum(_score(r, False).get("dragonCount") == 0 for r in terminal),
        "own_splits_per_game_median": _median(_counts(r).get("splits") for r in terminal),
        "opponent_splits_per_game_median": _median(_counts(r, False).get("splits") for r in terminal),
        "both_queens_dead": sum(_score(r).get("queenLength") == 0 and _score(r, False).get("queenLength") == 0 for r in terminal),
        "own_queen_deaths": len(dead), "own_queen_death_rounds_known": sum(v is not None for v in rounds),
        "own_queen_death_round_median_conditional_on_death": _median(rounds),
        "own_queen_death_round_bins": dict(Counter("未知" if v is None else "0–50" if v <= 50 else "51–100" if v <= 100 else "101–250" if v <= 250 else "251+" for v in rounds)),
        "own_queen_death_causes": dict(Counter(_queen_death(r)["reason"] for r in dead)),
        "own_queen_death_causes_known": sum(_queen_death(r)["reason"] != "unknown" for r in dead),
        "own_terminal_longest_median": _median(_score(r).get("longestDragon") for r in terminal),
        "opponent_terminal_longest_median": _median(_score(r, False).get("longestDragon") for r in terminal),
        "historical_max_above_terminal_games": sum((_peak(r)["difference"] or 0) > 0 for r in terminal),
        "historical_max_gap_records_measured": sum(_peak(r)["difference"] is not None for r in terminal),
        "historical_max_to_terminal_difference_median": _median(_peak(r)["difference"] for r in terminal),
        "longest_loss_historical_max_difference_median": _median(_peak(r)["difference"] for r in longest_losses),
        "longest_rule_losses": len(longest_losses), "longest_loss_peak_measured": len(longest_peak_measured),
        "longest_loss_terminal_deficit_median": _median(_score(r, False).get("longestDragon", 0) - _score(r).get("longestDragon", 0) for r in longest_losses),
        "longest_loss_own_to_rival_terminal_ratio_median": _median(_score(r).get("longestDragon", 0) / _score(r, False)["longestDragon"] for r in longest_losses if _score(r, False).get("longestDragon", 0) > 0),
        "longest_loss_past_peak_exceeds_rival_terminal": sum(_peak(r)["historical_team_max"] > _score(r, False).get("longestDragon", 0) for r in longest_peak_measured),
        "longest_loss_past_peak_equals_rival_terminal": sum(_peak(r)["historical_team_max"] == _score(r, False).get("longestDragon", 0) for r in longest_peak_measured),
        "longest_loss_past_peak_below_rival_terminal": sum(_peak(r)["historical_team_max"] < _score(r, False).get("longestDragon", 0) for r in longest_peak_measured),
        "own_events": _events_total(terminal, True), "opponent_events": _events_total(terminal, False)}


def series_membership(rows, sources):
    """Connected membership from explicit Game links; never guess from ID spacing."""
    parent, sets = {}, []
    def find(value):
        parent.setdefault(value, value)
        if parent[value] != value: parent[value] = find(parent[value])
        return parent[value]
    for source in sources.values():
        members = set()
        for link in source.get("links", []):
            match = re.search(r"/battles/(\d+)(?:$|[/?#])", link.get("href", ""))
            if match and re.match(r"Game\s+\d+\b", link.get("text", "")):
                members.add(int(match[1]))
        if len(members) < 2: continue
        sets.append(members)
        anchor = min(members)
        for value in members:
            a, b = find(anchor), find(value)
            parent[max(a, b)] = min(a, b)
    components = defaultdict(set)
    for value in parent: components[find(value)].add(value)
    assignments, groups = {}, {}
    for row in rows:
        match_id = row.get("match_id")
        root = find(match_id) if match_id in parent else None
        key = f"linked:{root}" if root is not None else f"unresolved:{match_id}"
        assignments[match_id] = key
        groups.setdefault(key, {"verified_link_membership": root is not None,
            "linked_match_ids": sorted(components[root]) if root is not None else [], "selected_match_ids": []})["selected_match_ids"].append(match_id)
    for group in groups.values(): group["selected_match_ids"].sort()
    return assignments, groups


def _usable_curve(row, curve):
    if not curve or curve.get("source_kind") != "sampled_ui_svg": return False
    quality = curve.get("quality") or {}
    if quality.get("series_to_named_column_verified") is not True or quality.get("issues"): return False
    ui = curve.get("terminal_ui") or {}
    if not _terminal(row) or ui.get("terminated") is not True or curve.get("outcome") != row.get("outcome"): return False
    names, scores = ui.get("column_names", []), ui.get("scores_by_column", [])
    audit_names = row.get("team_names") or {}
    fields = {"queenLength": "queen", "dragonCount": "dragons", "longestDragon": "longest", "totalLength": "total"}
    for side in ("A", "B"):
        name = audit_names.get(side)
        if name not in names: return False
        index = names.index(name)
        if index >= len(scores): return False
        if any((row["result"].get("team" + side) or {}).get(a) != scores[index].get(b) for a, b in fields.items()): return False
    return True


def build_findings(audit, trajectories=None, series_sources=None):
    rows = audit.get("matches", [])
    if any(r.get("match_id") is None for r in rows) or len({r.get("match_id") for r in rows}) != len(rows):
        raise ValueError("Every audit row needs a distinct match ID")
    trajectories = trajectories or {"matches": []}
    curves = {}
    for curve in trajectories.get("matches", []):
        if curve.get("match_id") is not None:
            match_id = int(curve["match_id"])
            if match_id in curves: raise ValueError("Duplicate trajectory match ID")
            curves[match_id] = curve
    membership, series = series_membership(rows, series_sources or {})
    by_map, by_opponent, by_series = defaultdict(list), defaultdict(list), defaultdict(list)
    cases, usable = [], []
    known_team_ids = {r["our_team_id"] for r in rows if r.get("our_team_id") is not None}
    inferred_team_id = next(iter(known_team_ids)) if len(known_team_ids) == 1 else None
    for row in rows:
        match_id = row.get("match_id")
        map_name, opponent = _identity({"our_team_id": inferred_team_id, **row})
        by_map[map_name].append(row); by_opponent[opponent].append(row); by_series[membership[match_id]].append(row)
        curve = curves.get(match_id)
        valid = _usable_curve(row, curve)
        if valid: usable.append(curve)
        if row.get("selected_table_outcome") != "loss" and row.get("outcome") != "loss": continue
        own, rival = _score(row), _score(row, False)
        cases.append({"match_id": match_id, "map": map_name, "opponent": opponent,
            "series": membership[match_id], "terminal_available": _terminal(row),
            "selected_table_outcome": row.get("selected_table_outcome"), "terminal_outcome": row.get("outcome"),
            "direct_terminal_rule": (row.get("direct_cause") or {}).get("score_axis") if _terminal(row) else None,
            "terminal_evidence": (row.get("direct_cause") or {}).get("evidence") if _terminal(row) else None,
            "own_terminal": own, "opponent_terminal": rival,
            "observed_queen_death": _queen_death(row), "observed_own_cumulative_events": _counts(row),
            "historical_max_to_terminal": _peak(row),
            "terminal_longest_deficit": rival.get("longestDragon", 0) - own.get("longestDragon", 0) if _terminal(row) else None,
            "historical_peak_minus_rival_terminal": _peak(row)["historical_team_max"] - rival.get("longestDragon", 0) if _peak(row)["historical_team_max"] is not None and _terminal(row) else None,
            "sampled_curve": {"usable": valid, "drawn_samples": (curve.get("sampling") or {}).get("drawn_samples"),
                "own_leading_samples": (curve.get("sample_order_counts_by_name") or {}).get(curve.get("our_name"), 0),
                "sampled_own_lead_then_terminal_loss": curve.get("sampled_own_lead_then_terminal_loss"),
                "scope": "Drawn, rounded, downsampled UI samples; not continuous rounds"} if valid else {"usable": False},
            "unverified": ["致死前路径、视野和安全替代行动", "历史最长单位的身份和死亡原因", "收珠与实际付费账单", "身体/头碰头的友敌归属", "对手策略意图"]
                if _terminal(row) and row.get("input_format") == "terminal_ui" else ["终局规则、Queen事件和曲线"] if not _terminal(row) else ["事件关联不能证明替代行动会赢"],
            "audit_warnings": row.get("warnings", []), "input_error": row.get("error")})
    selected_losses = sum(r.get("selected_table_outcome") == "loss" for r in rows)
    usable_losses = [c for c in usable if c.get("outcome") == "loss"]
    summary = summarize(rows)
    return {"purpose": "发现问题，不作为任何新版胜率或上线验收", "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "selection": audit.get("selection", {}), "selection_errors": audit.get("selection_errors", []),
        "denominators": {"selected_matches": len(rows), "selected_losses": selected_losses,
            "terminal_matches": summary["terminal_games"], "terminal_losses": summary["terminal_losses"],
            "platform_version_verified": sum(r.get("platform_version_verified") is True for r in rows),
            "queen_deaths_annotated": summary["own_queen_deaths"], "queen_death_causes_known": summary["own_queen_death_causes_known"],
            "usable_sampled_curve_matches": len(usable), "usable_sampled_curve_losses": len(usable_losses),
            "losses_with_any_own_leading_drawn_sample": sum(c.get("sampled_own_lead_then_terminal_loss") is True for c in usable_losses),
            "full_event_replays": sum(r.get("input_format") == "official_replay" for r in rows),
            "audit_records_with_warnings": sum(bool(r.get("warnings")) for r in rows),
            "verified_linked_series": sum(g["verified_link_membership"] for g in series.values()),
            "matches_without_verified_series": sum(not series[membership[r.get("match_id")]]["verified_link_membership"] for r in rows)},
        "summary": summary, "by_map": {k: summarize(v) for k, v in sorted(by_map.items())},
        "by_opponent": {k: {**summarize(v), "linked_series_count": len({membership[r["match_id"]] for r in v if series[membership[r["match_id"]]]["verified_link_membership"]})} for k, v in sorted(by_opponent.items())},
        "by_series": {k: {**series[k], **summarize(v)} for k, v in sorted(by_series.items())},
        "loss_cases": cases,
        "limits": ["同一系列通常共享对手与运行背景；五局不能当作完全独立抽样，不计算独立样本置信区间。",
            "部分采集按采集顺序形成，不能把部分地图或对手分布当成完整100场的估计。",
            "统计表左右列是具名UI列，不必等于引擎A/B；Queen日志仅凭唯一匹配死亡回合归属。",
            "曲线的领先样本不代表持续优势、每回合状态或战略因果。",
            "历史最长与终局最长之差不能归为某条龙死亡、净资源损失或付费损耗。",
            "累计事件没有逐行动因果链；其他身体/头碰头未分友敌，冲刺尝试不等于付费步数。",
            "无有效动作死亡不等于CPU错误；这些计数不能证实喂珠、主动自杀或超时。",
            "显示版本可核验平台标签；源码字节、提交映射和完整回放证据另行核验。"]}


def _fmt(value):
    return "未知" if value is None else f"{value:g}" if isinstance(value, float) else str(value)


def _escape(value):
    return str(value).replace("|", "\\|").replace("\r", " ").replace("\n", " ")


def _rule(case):
    axis = case["direct_terminal_rule"]
    a, b = case["own_terminal"], case["opponent_terminal"]
    if not case["terminal_available"]: return "终局尚缺"
    if axis == "elimination": return f"消灭：我方存活{a.get('dragonCount')}，对方{b.get('dragonCount')}"
    key = {"queen": "queenLength", "longest": "longestDragon", "total_length": "totalLength"}.get(axis)
    value = f"：{a.get(key)}<{b.get(key)}" if key else ""
    return AXES.get(axis, "未知规则") + value


def _table(headers, rows):
    return "\n".join(["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |",
                      *["| " + " | ".join(_escape(v) for v in row) + " |" for row in rows]])


def _outcomes(counts):
    return f"{counts.get('win', 0)}W/{counts.get('loss', 0)}L/{counts.get('draw', 0)}D"


def _axis_counts(counts):
    return "、".join(f"{AXES.get(k, k)}{v}" for k, v in sorted(counts.items())) or "无已确认败场"


def render_markdown(report):
    d, s = report["denominators"], report["summary"]
    selection_outcomes = s["selected_table_outcomes"]
    lines = ["# 同版本线上对局证据回顾", "", report["purpose"] + "。", "",
        f"清单截止：{report['selection'].get('cutoff_exclusive', '未提供')}。原始选择规则：{report['selection'].get('rule', '未提供')}。", "",
        f"固定清单{d['selected_matches']}场：{_outcomes(selection_outcomes)}。已取得终局{d['terminal_matches']}/{d['selected_matches']}，其中{_outcomes(s['terminal_outcomes'])}；尚缺{d['selected_matches'] - d['terminal_matches']}场终局。",
        f"平台版本标签已核验{d['platform_version_verified']}/{d['terminal_matches']}；完整事件回放{d['full_event_replays']}/{d['selected_matches']}。已核实链接系列{d['verified_linked_series']}组，{d['matches_without_verified_series']}场系列关系尚未核实。", "",
        "## 证据分母", "", _table(["指标", "已知分子 / 对应分母", "可支持的结论"], [
            ["终局判负规则", f"{d['terminal_losses']}/{d['selected_losses']}清单败场", "评分直接原因"],
            ["Queen死因", f"{d['queen_death_causes_known']}/{d['queen_deaths_annotated']}终局已标注死亡", "明确匹配的死亡事件原因"],
            ["可用曲线", f"{d['usable_sampled_curve_matches']}/{d['selected_matches']}清单场次", "取样点的大小关系"],
            ["曾有我方领先样本后终局败", f"{d['losses_with_any_own_leading_drawn_sample']}/{d['usable_sampled_curve_losses']}可用曲线败场", "至少一个绘制样本领先，不是持续领先"],
        ]), "", f"已取得败场的直接规则：{_axis_counts(s['loss_score_axes'])}。",
        f"我方Queen终局存活{s['own_queen_alive']}/{s['terminal_games']}，对方{s['opponent_queen_alive']}/{s['terminal_games']}；双方Queen均死{s['both_queens_dead']}/{s['terminal_games']}。",
        f"在存活Queen中，终局长度中位数为我方{_fmt(s['own_alive_queen_length_median'])}、对方{_fmt(s['opponent_alive_queen_length_median'])}。终局单位数中位数为我方{_fmt(s['own_terminal_dragons_median'])}、对方{_fmt(s['opponent_terminal_dragons_median'])}；被完全消灭分别{s['own_eliminated_games']}、{s['opponent_eliminated_games']}场。",
        f"仅在我方Queen死亡场中，已知死亡回合{s['own_queen_death_rounds_known']}/{s['own_queen_deaths']}，中位数{_fmt(s['own_queen_death_round_median_conditional_on_death'])}；活到终局的Queen不计入此中位数。",
        "Queen已知死因：" + "、".join(f"{DEATHS.get(k,k)}{v}" for k, v in sorted(s['own_queen_death_causes'].items())) + "。",
        "死亡回合分布：" + "、".join(f"{k}={s['own_queen_death_round_bins'][k]}" for k in ("0–50", "51–100", "101–250", "251+", "未知") if k in s['own_queen_death_round_bins']) + "。", "",
        f"终局最长中位数：我方{_fmt(s['own_terminal_longest_median'])}、对方{_fmt(s['opponent_terminal_longest_median'])}。历史最长高于终局最长{s['historical_max_above_terminal_games']}/{s['historical_max_gap_records_measured']}已测场；差值中位数{_fmt(s['historical_max_to_terminal_difference_median'])}，最长规则败场中的差值中位数{_fmt(s['longest_loss_historical_max_difference_median'])}。此差值不对应单个单位的死亡损失。", "",
        f"在{s['longest_rule_losses']}场最长规则败局中，终局落后长度的中位数{_fmt(s['longest_loss_terminal_deficit_median'])}，我方/对方终局最长比值中位数{format(s['longest_loss_own_to_rival_terminal_ratio_median'], '.1%') if s['longest_loss_own_to_rival_terminal_ratio_median'] is not None else '未知'}。可比较历史峰值的{s['longest_loss_peak_measured']}场中，我方历史最长高于对方终局最长{s['longest_loss_past_peak_exceeds_rival_terminal']}场、相等{s['longest_loss_past_peak_equals_rival_terminal']}场、仍低于{s['longest_loss_past_peak_below_rival_terminal']}场。这只比较两个观测数值，不证明保住峰值单位就会赢。", "",
        "## 累计事件", "", "下表是已取得终局的计数总和。覆盖分母逐项列出；没有收珠、真实付费和友敌归属账单。", "",
        _table(["事件", "我方总数 / 覆盖场", "对方总数 / 覆盖场"], [[label,
            f"{_fmt(s['own_events'][key]['sum'])}/{s['own_events'][key]['records_measured']}",
            f"{_fmt(s['opponent_events'][key]['sum'])}/{s['opponent_events'][key]['records_measured']}"] for key, label in EVENTS.items()]), "",
        f"每场成功分裂数的中位数：我方{_fmt(s['own_splits_per_game_median'])}、对方{_fmt(s['opponent_splits_per_game_median'])}。分裂会继承现有长度，此计数不是独立增长或资源净收益。", "",
        "## 按地图与对手聚类", "", "清单场数与已取终局场数分开；下列胜负只来自已取终局。", ""]
    headers = ["地图", "清单/终局", "终局胜负", "败场规则", "我方Queen存活", "最长中位数 我/敌"]
    lines += [_table(headers, [[name, f"{g['selected_games']}/{g['terminal_games']}", _outcomes(g['terminal_outcomes']), _axis_counts(g['loss_score_axes']),
                              f"{g['own_queen_alive']}/{g['terminal_games']}", f"{_fmt(g['own_terminal_longest_median'])}/{_fmt(g['opponent_terminal_longest_median'])}"] for name, g in report['by_map'].items()]), "",
              _table(["对手", "已核实系列", *headers[1:]], [[name, g['linked_series_count'], f"{g['selected_games']}/{g['terminal_games']}", _outcomes(g['terminal_outcomes']), _axis_counts(g['loss_score_axes']),
                              f"{g['own_queen_alive']}/{g['terminal_games']}", f"{_fmt(g['own_terminal_longest_median'])}/{_fmt(g['opponent_terminal_longest_median'])}"] for name, g in report['by_opponent'].items()]), "",
              "## 系列聚类", "", "仅用已保存页面的Game链接确定成员；不根据连续编号猜测系列。每组共享对手和背景，不把五局当完全独立样本。", "",
              _table(["系列", "清单成员", "清单/终局", "终局胜负", "败场规则"], [[key if g['verified_link_membership'] else "未核实", ", ".join(map(str, g['selected_match_ids'])),
                    f"{g['selected_games']}/{g['terminal_games']}", _outcomes(g['terminal_outcomes']), _axis_counts(g['loss_score_axes'])] for key, g in report['by_series'].items()]), "",
              "## 每一败场", "", "终局规则是直接判负依据；事件是观测事实；未证实项保留未知。清单中的败场即使尚缺终局也不删除。", ""]
    case_rows = []
    for case in report["loss_cases"]:
        q, events, peak, curve = case["observed_queen_death"], case["observed_own_cumulative_events"], case["historical_max_to_terminal"], case["sampled_curve"]
        queen = "尚缺" if not case["terminal_available"] else f"r{q['round']} {DEATHS.get(q['reason'], q['reason'])}" if q["round"] is not None else f"存活L{case['own_terminal'].get('queenLength')}" if case['own_terminal'].get('queenLength', 0) > 0 else "死亡回合未知"
        observed = f"Queen {queen}；死{_fmt(events.get('deaths'))}[头{_fmt(events.get('death_head_collision'))}、墙{_fmt(events.get('death_wall'))}、自{_fmt(events.get('death_self_body'))}、体{_fmt(events.get('death_other_body'))}]；分裂{_fmt(events.get('splits'))}"
        peak_text = f"{_fmt(peak['historical_team_max'])}→{_fmt(peak['terminal_team_max'])}（差{_fmt(peak['difference'])}；敌终局{_fmt(case['opponent_terminal'].get('longestDragon'))}）"
        curve_text = f"领先绘制样本{curve['own_leading_samples']}/{curve['drawn_samples']}" if curve['usable'] else "曲线缺失/不可用"
        case_rows.append([f"[{case['match_id']}](https://game.battlecode.au/battles/{case['match_id']})", case['map'], case['opponent'], _rule(case), observed, peak_text, curve_text, "；".join(case['unverified'])])
    lines += [_table(["Match", "地图", "对手", "直接终局规则", "已观测事件", "历史最长→终局", "曲线", "未证实"], case_rows), "", "## 边界与来源", "",
              *["- " + limit for limit in report['limits']]]
    if report.get("selection_errors"): lines += ["", "清单错误：" + "；".join(report["selection_errors"])]
    for name, provenance in report.get("sources", {}).items():
        lines += ["", f"{name}：[{provenance['path']}]({provenance['path']})，SHA256 `{provenance['sha256']}`。"]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--trajectories", type=Path)
    parser.add_argument("--ui-dir", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()
    audit = json.loads(args.audit.read_text(encoding="utf-8-sig"))
    trajectories = json.loads(args.trajectories.read_text(encoding="utf-8-sig")) if args.trajectories else None
    ui_sources = {}
    source_errors = []
    for row in audit.get("matches", []):
        match_id = row.get("match_id")
        path = args.ui_dir / f"{match_id}-ui.json" if args.ui_dir else Path(row["input_path"]) if row.get("input_format") == "terminal_ui" and row.get("input_path") else None
        if path and path.exists():
            try: ui_sources[match_id] = json.loads(path.read_text(encoding="utf-8-sig"))
            except (OSError, ValueError) as error: source_errors.append({"match_id": match_id, "error": str(error)})
    report = build_findings(audit, trajectories, ui_sources)
    report["series_source_errors"] = source_errors
    report["sources"] = {name: {"path": path.resolve().as_posix(), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        for name, path in (("终局审计", args.audit), ("取样曲线审计", args.trajectories)) if path}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(render_markdown(report), encoding="utf-8")
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["denominators"], ensure_ascii=False))


if __name__ == "__main__":
    main()
