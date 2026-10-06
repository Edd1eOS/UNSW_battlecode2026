# 2026-10-06 固定100场线上UI证据

[完整发现报告](oct6-online100-findings.md)包含54个败场的终局规则、已观测事件与未证实原因。此数据用于发现问题，不是新版胜率验证或上线验收。

## 来源与截止范围

- 来源：官方[我的比赛列表](https://game.battlecode.au/games?mine=1)及100个`https://game.battlecode.au/battles/<matchId>`页面。
- 我方队伍ID：1035。逐场页面显示平台版本v14、名称`Guard v66 - Queen threat buffer`；没有验证提交ID映射或源码字节。
- 页面显示时间范围：2026-10-06 13:13–19:47，UTC+08。清单截止字段：`2026-10-06T19:48:00+08:00`。
- 清单选择记录：`2026-10-06T11:54:53Z`。按平台表顺序取截止分钟之前最新100场已完成排位，没有按胜负、地图或对手筛选。
- 100场覆盖17张地图、19个对手及21个页面链接系列。19个系列各有5场入选，两个边界系列分别入选2场和3场；同系列和重复对手不能当作完全独立样本。

页面显示时间和选择记录作为原始字段保留；没有原始API时间戳或原始事件回放来增加其精度。

## 文件与校验

文件：[oct6-online100-ui.json.gz](../tests/fixtures/oct6-online100-ui.json.gz)。

- 压缩大小：475,522字节（464.4 KiB）。
- 解压大小：2,697,224字节。
- 压缩SHA256：`1023d9f00bb9a2502db556f00d0143c88375f126bc1c644350d3a83dd6052447`。
- 解压JSON SHA256：`07cbc173d669c7c6056d4f500aa54804e10c0f5d5fa87c80d4136146568d7a07`。
- gzip时间字段为0；JSON使用UTF-8、键排序和固定紧凑分隔符。原始UI和选择文件的UTF-8文本完整保存，各有原始字节SHA256；没有重新编造回合、行动或身份。

格式`unswbc.online-terminal-ui.v1`包含：`selection`及原文、100条`ui_exports`（每条含match ID、来源链接、原文和校验值）、被捕获的`chart_layout_proof`及原文、来源范围和已核实观测。读取`raw_json_utf8`后再解析JSON，可恢复原始终局、Queen过滤事件、SVG曲线和链接。

## 证据层级

1. 100/100终局UI：46W54L；54败场直接评分轴为最长单位26、消灭20、Queen长度8。没有平局、身份/轮次/原因校验警告。
2. 我方Queen死亡75场，75/75均有与终局死亡回合唯一匹配的过滤日志：头碰头51、墙/海带14、其他身体10。日志没有碰撞伙伴或完整前序行动，所以头碰头不能全部标为敌方攻击。
3. 100/100曲线具名映射及终局端点校验通过，质量问题0。SVG为两位小数、下采样的绘制样本；不是完整逐回合状态。53/54败场有至少一个我方领先的绘制样本，这不证明持续领先。
4. 原始事件回放0/100。未恢复完整身体轨迹、长单位身份/死因、收珠/付费账单、可替代动作、CPU错误或对手私有策略。

我方Queen终局存活25/100（25%），对方28/100（28%）；双方Queen均死60/100。Queen死因按75次死亡计：头碰头51/75=68%，墙/海带14/75≈18.7%，其他身体10/75≈13.3%。终局败因按54次失败计：最长26/54≈48.1%，消灭20/54≈37.0%，Queen长度8/54≈14.8%。精确分子分母保留，非整数百分比显示到一位小数。

历史全队最长与终局全队最长来自不同时刻，可能对应不同单位；其差值不是已证实的死亡长度或净资源损耗。26场最长败局中，历史峰值仍低于对方终局最长的20场，只能证明曾观测到的峰值不足，不能区分资源不足、付费消耗或达到大长度之前的死亡等机制。

## 敏感信息检查

压缩包只包含比赛页面UI导出、列表选择和图表布局证据。UI字段限定为`title/main/tables/links/queen_events/charts/chart_note`；保存链接均指向官方比赛/队伍页面。未包含API key、Authorization、cookie、账号密码、签名下载地址、私有机器人源码/二进制或本机认证文件。身份信息仅是页面显示的公开队伍名称、队伍ID、比赛ID和版本标签。

## 离线复现

在仓库根目录运行：

```text
python -m unittest discover -s tests -p online100_evidence_test.py
```

[真实数据集成检查](../tests/online100_evidence_test.py)直接对固定原始捕获调用[audit_online](../tools/audit_online.py)和[ui_trajectory](../tools/ui_trajectory.py)，再核验[报告生成器](../tools/audit_report.py)的54败场和系列分母。全部为标准库离线工作；不需要忽略目录中的测试产物、Node、API key、浏览器或引擎。

如需重新生成Markdown，执行以下Python代码（输出到当前目录的新文件）：

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path('tests').resolve()))
from online100_evidence_test import Online100EvidenceTest
from tools.audit_report import build_findings, render_markdown

Online100EvidenceTest.setUpClass()
e = Online100EvidenceTest
report = build_findings(
    {'matches': e.audits, 'selection': e.payload['selection']},
    {'matches': e.curves}, e.sources)
Path('oct6-online100-regenerated.md').write_text(
    render_markdown(report), encoding='utf-8')
```

重生成的统计及逐场表应一致；生成时间等展示元数据不用于证据校验。压缩包中的选择/观测常数是事实记录；没有包含候选机器人的预测结果或镜像实现测试。
