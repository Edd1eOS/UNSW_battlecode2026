"""Render the fixed online discovery audit; no replay, bot or engine execution."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[1]


def median(values):
    values = list(values)
    return statistics.median(values) if values else None


def escape(value):
    return str(value).replace("|", "\\|").replace("\n", " ")


def build(index):
    rows = index["matches"]
    verified = [row for row in rows if row.get("audit_status") == "verified"]
    games = [row["metrics"] for row in verified]
    losses = [game for game in games if game["outcome"] == "loss"]
    gross = [game for game in games if game["gross_ledger_verified"]]
    deaths = [death for game in games for death in game["unique_longest_deaths"]]
    counters = sum((Counter(game["event_counts"]) for game in games), Counter())
    maps = []
    for name in sorted({game["map"] for game in games}):
        group = [game for game in games if game["map"] == name]
        maps.append({"map": name, "games": len(group), "wins": sum(g["outcome"] == "win" for g in group),
                     "losses": sum(g["outcome"] == "loss" for g in group),
                     "elimination_losses": sum(g["outcome"] == "loss" and g["score_axis"] == "elimination" for g in group),
                     "queen_alive": sum(g["queen_alive"] for g in group),
                     "terminal_longest_median": median(g["terminal_longest"] for g in group),
                     "friendly_head_deaths": sum(g["event_counts"].get("friendly_head_deaths", 0) for g in group),
                     "self_body_deaths": sum(g["event_counts"].get("death_self_body", 0) for g in group)})
    summary = {**index["summary"],
               "queen_positive_update_games": sum(g["resources"]["queen_positive_updates"] > 0 for g in games),
               "queen_net_update_growth_median": median(g["queen_net_update_growth"] for g in games),
               "unique_longest_deaths": len(deaths),
               "unique_longest_death_games": sum(bool(g["unique_longest_deaths"]) for g in games),
               "unique_longest_death_reasons": dict(Counter(d["reason"] for d in deaths)),
               "unique_longest_deaths_reversing_immediate_lead": sum(d["reversed_own_lead_immediately"] for d in deaths),
               "losses_with_a_leading_round": sum(g["continuous_lead"]["leading_rounds"] > 0 for g in losses),
               "losses_with_ten_continuous_leading_rounds": sum(g["continuous_lead"]["longest_continuous_lead"] >= 10 for g in losses),
               "peak_above_terminal_games": sum(g["historical_event_longest"] > g["terminal_longest"] for g in games),
               "peak_minus_terminal_median": median(g["historical_event_longest"] - g["terminal_longest"] for g in games),
               "body_balance_nonzero_games": sum(g["resources"]["reconstructed_balance_residual"] != 0 for g in games),
               "gross_ledger_denominator": len(gross),
               "gross_medians": {key: median(g["gross_resources"][key] for g in gross) for key in
                                  ("food_collected", "paid_step_cost", "queen_food_collected", "queen_paid_step_cost")},
               "gross_refusal_reasons": dict(Counter(reason for row in rows for reason in row.get("gross_ledger_issues", []))),
               "own_event_counts": dict(counters)}
    # Keep provenance and numeric results, never the downloaded source or replay payload.
    manifest = {"schema_version": 1, "generated_utc": index["generated_utc"],
                "fixed_evidence": index["fixed_evidence"], "source_proof": index["source_proof"],
                "analyzer_dependencies": index["analyzer_dependencies"], "summary": summary,
                "scope": "Fixed 100 online discovery games; not candidate strength validation",
                "selection_cutoff_exclusive": index["selection"]["cutoff_exclusive"], "maps": maps,
                "matches": [{"match_id": row["match_id"], "import_status": row["import_status"],
                             "audit_status": row["audit_status"], "replay_sha256": row.get("replay_sha256"),
                             "replay_bytes": row.get("replay_bytes"), "sources": row["sources"],
                             "validation_issues": row.get("validation_issues", []),
                             "gross_ledger_issues": row.get("gross_ledger_issues", []),
                             "metrics": {key: row["metrics"][key] for key in
                                 ("outcome", "score_axis", "map", "opponent", "our_team", "queen_alive", "queen_length",
                                  "queen_peak_length", "queen_net_update_growth", "queen_head_collision_relation",
                                  "terminal_longest", "opponent_terminal_longest", "historical_round_longest",
                                  "historical_event_longest", "resources", "gross_resources", "continuous_lead", "event_counts")}
                                 if "metrics" in row else None} for row in rows]}
    proof = index["source_proof"]
    s = summary
    lines = ["# 2026-10-06 固定100场：原始回放补充审计", "",
             f"生成时间UTC `{index['generated_utc']}`。这是此前固定100场的证据升级；[原UI发现报告](oct6-online100-findings.md)和[压缩UI证据](oct6-online100-fixture.md)保留原快照，不覆盖。完整机器报告及每局回放SHA见[审计清单](oct6-online100-raw-manifest.json)。", "",
             "## 来源与可证范围", "",
             "名单仍为6 Oct 13:13–19:47北京时间的最新100场已完成排位，截止19:48之前；不因结果、地图、对手、缺失或错误换局。21个系列、19个对手、17个地图名称存在重复与相关性。", "",
             f"原始回放取得及完整核对为 **{s['whole_match_verified']}/{s['selected']}**；提交ID、初始身体、明确队伍归属、每轮状态、正式终局、固定UI种子/地图/死亡事件/累计事件均核对，解析或审计失败{s['decoder_or_audit_failures']}、扫描安全问题{s['scan_issues']}。每场我方匿名header唯一`botId=15719`，并由冻结UI确认平台v14/Guard v66；不能按UI列序或龙ID奇偶推队伍。对手匿名header不证明其提交或私有源码。", "",
             f"根代理在官方Submissions页观察Active v14与完整Download v14 Guard v66链接，再下载[提交15719源码ZIP]({proof['source_url']})。ZIP SHA256 `{proof['zip_sha256']}`；八个成员均与已存档v66同字节，源码包SHA256 `{proof['source_bundle_sha256']}`。仅读ZIP成员并哈希，未解压执行、上传或把源码内容加入此证据。线上提交二进制SHA仍未独立取得。", "",
             "原始回放约238.8MB，保留在忽略目录`test-results/online100-raw`，不入Git。该清单只保存来源、哈希和统计，没有cookie、token、API key、认证头或下载URL查询参数。下载文件名提供系列来源；官方可见UI下载行为由根代理记录，哈希负责字节复现，不把文件名当身份的唯一依据。", "",
             "## 直接结果和新观测", "",
             f"- 正式结果仍为46W54L；54败局直接判负：Longest 26/54（48.15%），消灭20/54（37.04%），Queen长度8/54（14.81%）。这不是候选胜率。",
             f"- Queen存活{s['our_queen_alive']}/100。75次Queen死亡：51头碰头、14墙/海带、10其他身体；51次头碰头中10次友军（19.61%）、41次敌军（80.39%）。其他身体10次暂未区分友敌。",
             f"- 全队头碰头死亡5177次：友军2168（41.88%）、敌军3009（58.12%）。这是死亡事件数，一次友军相撞会计两条死亡，不能叫2168次碰撞。总分裂19119次。",
             f"- Queen有正增长update的局数{s['queen_positive_update_games']}/100，净update增长中位{s['queen_net_update_growth_median']:g}；47/100局Queen分裂，197次分裂累计转给子龙398长度。分裂守恒，不能计作收珠或自主增长，也不能由此判定喂养意图。",
             f"- 100/100全队身体守恒残差为0。收珠/付费完整账只有{s['gross_ledger_denominator']}/100；另外27场含不支持的记录action kind，严格拒绝gross，保留净身体账。73场Queen收珠中位9、实际付费损耗中位6，全队收珠中位354、付费中位8；该分母不可外推到100场。请求MOVE、UI sprint尝试不当作真实付费。",
             f"- 当时唯一Longest单位死亡{s['unique_longest_deaths']}次（{s['unique_longest_death_games']}/100局）：头碰头253、自撞30、墙/海带15、其他身体10；其中54条在死亡瞬间把原比较优势反转给对方。可能同局多次，不能等同54个直接败因。",
             f"- 54敗局中{s['losses_with_a_leading_round']}/54曾在完整轮末比较领先，{s['losses_with_ten_continuous_leading_rounds']}/54曾连续至少10轮领先。领先按消灭→Queen→Longest→总长度计算；仍只称轮末连续，不能声称每个轮内时刻。",
             "- 70/100局实际历史Longest峰值高于终局值，差值中位3。26个Longest败局终局落后中位13.5；其中实际峰值大于对方终局5局、相等1局、仍小于20局。故既有保不住已经长出的单位，也有从未长到足够长度的失败。峰值含初始/分裂继承长度，不等同自主增长。", "",
             "UI的Longest so far取初始与轮末峰值；逐事件实际峰值可更高。例如M1238557我方轮末15、轮内17；M1237739对方轮末14、轮内15。这属于明确采样口径，并非身份或引擎核对错误。", "",
             "## 地图分组（发现样本）", "",
             "| 地图 | W–L/局数 | 消灭败局 | Queen存活 | 终局Longest中位 | 友军头死亡 | 自身体死亡 |",
             "| --- | --- | --- | --- | --- | --- | --- |"]
    for group in maps:
        lines.append(f"| {escape(group['map'])} | {group['wins']}–{group['losses']}/{group['games']} | {group['elimination_losses']} | {group['queen_alive']}/{group['games']} | {group['terminal_longest_median']:g} | {group['friendly_head_deaths']} | {group['self_body_deaths']} |")
    lines += ["", "## 54个败场：判负与观测分离", "",
              "回合采用网页1起算。`Q峰`为实际观测峰值；`Q转`为Queen分裂转走总长度；`L峰→末/敌末`是全队历史峰值、终局Longest与敌方终局Longest。`独L死`是当时唯一最长单位死亡条数。友头为全队友军头死亡条数。碰撞原因和此前增长不是自动确定的根本策略因果。", "",
              "| Match | 对手 / 地图 | 直接规则 | Queen死亡 | Q峰 / Q转 | L峰→末/敌末 | 独L死 / 友头 | 连续领先轮数 |",
              "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    axis = {"elimination": "消灭", "longest": "Longest", "queen": "Queen长度", "total": "总长度"}
    reason = {"H": "头碰头", "W": "墙/海带", "O": "其他身体", "S": "自身身体"}
    for game in losses:
        death = game["queen_death"]
        q = "存活" if not death else f"r{death['round'] + 1} {reason.get(death['reason'], death['reason'])}"
        if death and death["reason"] == "H":
            q += "（" + {"friendly": "友军", "enemy": "敌军"}.get(game["queen_head_collision_relation"], "未定") + "）"
        lines.append(f"| [M{game['match_id']}](https://game.battlecode.au/battles/{game['match_id']}) | {escape(game['opponent'])} / {escape(game['map'])} | {axis.get(game['score_axis'], game['score_axis'])} | {q} | {game['queen_peak_length']} / {game['resources']['queen_length_transferred_by_split']} | {game['historical_event_longest']}→{game['terminal_longest']}/{game['opponent_terminal_longest']} | {len(game['unique_longest_deaths'])} / {game['event_counts'].get('friendly_head_deaths', 0)} | {game['continuous_lead']['longest_continuous_lead']} |")
    lines += ["", "## 待验证机制与限制", "",
              "Trophy 7/8败且全部被消灭、Devil 6/8败其中5次消灭；Devil有444条友军头死亡且Queen存活0/8。Portals的132条自撞占全部210条的62.86%。这支持优先检查狭道/出口容量、友军时序、门户后的真实身体与路径承诺；但没有证明对手故意围堵，或每条死亡由同一种代码缺陷造成。", "",
              "Queen增长、付费与分裂同时存在，净长度兑现不足。可检验的通用机制是Queen独立保留资源与退路、关键长单位减少接触损失、分裂数量受可用空间和交通约束。当前表仅给假说和可观测验收项，没有从对手计数逆推出私有算法，也不能证明新候选已经改进。", "",
              "匿名对手提交未验证；当前冻结100场只用于发现。对手无效动作场仍完整保留在这100场中，不能因失去gross账就删局。离线全图仅用于审计，不得给bot提供隐藏信息。", "",
              "## 离线复现", "",
              "取得相同官方ZIP/replay后：", "", "```powershell",
              ".venv\\Scripts\\python.exe tools\\import_online_replays.py --download-dir '<下载目录>' --source-zip '<官方下载源码ZIP>' --archive-source opponents\\v66-queen-threat-buffer --source-link-confirmed",
              ".venv\\Scripts\\python.exe tools\\report_online_raw.py",
              ".venv\\Scripts\\python.exe -m unittest tests.import_online_replays_test tests.online100_evidence_test tests.online_raw_replay_test",
              "```", "",
              "`--source-link-confirmed`仅在有可信官方可见链接记录时使用。导入器拒绝路径穿越、嵌套成员、符号链接、超大成员和不同字节重复；单场解析失败记录原ID并继续，不用其他比赛替换。单场缓存由原回放/UI/源包/分析器/官方decoder哈希绑定。上述重建不启动任何比赛；原始回放缺失时实回放集成检查显式skip。", ""]
    return manifest, "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "test-results/online100-raw/index.json")
    parser.add_argument("--manifest", type=Path, default=ROOT / "docs/oct6-online100-raw-manifest.json")
    parser.add_argument("--markdown", type=Path, default=ROOT / "docs/oct6-online100-raw-findings.md")
    args = parser.parse_args()
    index = json.loads(args.input.read_text(encoding="utf-8"))
    fixed_ui_hash = hashlib.sha256((ROOT / "tests/fixtures/oct6-online100-ui.json.gz").read_bytes()).hexdigest()
    if index["summary"]["selected"] != 100 or index["fixed_evidence"]["ui_fixture_sha256"] != fixed_ui_hash:
        raise ValueError("This findings report is only for the frozen October 6 online100 selection")
    if not index["summary"]["complete_selected_raw_audit"] or not index["summary"]["dependencies_unchanged_during_run"]:
        raise ValueError("Final report requires complete fixed raw audit and stable analyzer dependencies")
    manifest, markdown = build(index)
    args.manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.markdown.write_text(markdown, encoding="utf-8")
    print(json.dumps(manifest["summary"], ensure_ascii=False))


if __name__ == "__main__":
    main()
