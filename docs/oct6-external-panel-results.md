# 2026-10-06 外部面板结果说明

快照：2026-10-06，v5留出完成后。冻结generalist-v1至v5各完成104场，共520场；正式结果与有效机制分母分列。它们使用不同种子，数字差异不能直接归因于策略改动；两个公开弱基准不能证明天梯升级或换算Elo。v4另因确定的封闭通道选择缺陷被拒绝采用；v5修复该排序，但没有真实线上强度确认。v3随后完成[真实外部线上51场](oct6-online51-findings.md)，13W38L，未取得强度采用依据。同一线上v14旧版本的[100场回放发现报告](oct6-online100-raw-findings.md)属于另一批发现证据，不混入候选胜率。

## 冻结对象与范围

| 对象 | v1 | v2 | v3 |
| --- | --- | --- | --- |
| 源码包SHA256 | `a0aa14ca48f0bd49c0fe55001933a89a20ccdb2f9614980b91abd0f21a15bc12` | `9dc95a19606724d844589e39db8cb11a35c7cdc4f518700140346551336f5506` | `cfbc144413bce11a4e65381aabf6d9ce85e653defb42534d05acd878d7a08b43` |
| WASM SHA256 | `1691f1a8b5ef19277baa61489ce0e05a148f74d0a2390beb068ba50796d0351b` | `efeb0ce81f3a6b40f9a8a2b53062b392354fe7c17cdc3e1b55c1aa83aa3ae99f` | `3b7f2e6d55dd081533fedc9da83fdef8627982999ff29b8cb7f5da8c80ced53f` |
| 面板计划SHA256 | `aaa2a6a323cc1dcdb2b165506b739adfd711b76b5f61d833dea9556c6ad23db8` | `49b4264c7574a02a029230d7e33d79182dadaa80d4cb3a8721977af94edf43fe` | `205d9edd4cef661d29b612db58ce84971b7683fc913336f402611230bb2dab01` |
| 发现 / 留出种子 | 2026100601 / 2026100691 | 2026100602 / 2026100692 | 2026100603 / 2026100693 |

每个候选发现阶段为四张预先选定地图、两个公开外部对手、双方位置，共16场；留出为22个本地地图文件、两个对手、双方位置，共88场。17个地图名称出现在固定线上100场，另5个为补充，不证明完整线上地图池或同名线上地图字节一致。22地图与外部源码哈希均在各候选比赛前冻结，没有安排自家新旧版本相互对战。

原始正式结果、源码/地图/回放哈希与运行事件见本机[v1汇总](../test-results/external-panel-20261006/summary.json)、[v2汇总](../test-results/external-panel-v2-20261006/summary.json)、[v3汇总](../test-results/external-panel-v3-20261006/summary.json)及各自`games/<phase>/<opponent>/<map-seed-side>/result.json`。完整严格重建另存[v1轨迹](../test-results/generalist-v1-full-trajectory-strict.json)、[v2轨迹](../test-results/generalist-v2-full-trajectory-strict.json)、[v3轨迹](../test-results/generalist-v3-full-trajectory-strict.json)，未覆盖旧轨迹。产物在忽略目录中。

[环境同字节证明](../tests/EXTERNAL_VALIDATION.md#环境同字节核验)确认本机1.2.7与公开最新1.2.9的引擎、编译器资源和当前地图一致；不替代线上环境核验。

## 正式结果和有效分母

| 候选 / 阶段 | 完成 | 正式胜负 | 有效机制结果 | 对手错误排除场数 | 我方运行/基础设施/预算失败 |
| --- | --- | --- | --- | --- | --- |
| v1发现 | 16/16 | 16W0L | 8W0L / 8 | 8 | 0 / 0 / 0 |
| v1留出 | 88/88 | 82W6L | 42W3L / 45 | 43 | 0 / 0 / 0 |
| v1合计 | 104/104 | 98W6L | 50W3L / 53 | 51 | 0 / 0 / 0 |
| v2发现 | 16/16 | 16W0L | 8W0L / 8 | 8 | 0 / 0 / 0 |
| v2留出 | 88/88 | 85W2L1D | 44W1L1D / 46 | 42 | 0 / 0 / 0 |
| v2合计 | 104/104 | 101W2L1D | 52W1L1D / 54 | 50 | 0 / 0 / 0 |
| v3发现 | 16/16 | 16W0L | 9W0L / 9 | 7 | 0 / 0 / 0 |
| v3留出 | 88/88 | 86W1L1D | 45W1L1D / 47 | 41 | 0 / 0 / 0 |
| v3合计 | 104/104 | 102W1L1D | 54W1L1D / 56 | 48 | 0 / 0 / 0 |

全部预定结果保留。对手无效动作场的正式胜负仍列在合计，但不贡献有效机制强度胜场；没有删除败局。v1对手无效动作2502条，v2为2088条，v3为2041条。这些是事件数，不是比赛数，也不证明全部是CPU超时或某种策略意图。

| 候选 / 对手 | 全部正式结果 | 有效机制分母 | 全部Queen存活 | 全部终局Longest中位 |
| --- | --- | --- | --- | --- |
| v1 SAS | 50W2L / 52 | 52 | 20/52 | 33 |
| v1 murder | 48W4L / 52 | 1：Stripes A败 | 26/52 | 32（含无效场） |
| v2 SAS | 51W1L / 52 | 52 | 28/52 | 36.5 |
| v2 murder | 50W1L1D / 52 | 2：Queen of Spades B胜、Stripes A和 | 25/52 | 41（含无效场） |
| v3 SAS | 51W0L1D / 52 | 52 | 26/52 | 36 |
| v3 murder | 51W1L / 52 | 4：Trophy B、Arena B、Colosseum B、Trauma B | 29/52 | 35.5（含无效场） |

v1最坏20,866,554 points、v2为24,605,321、v3为20,154,421，均低于预设90M余量线，只覆盖已执行输入。v1留出在观察到地图名称的有效结果32W3L/35，补充地图10W0L/10；v2对应34W1L1D/36和10W0L/10；v3对应34W0L1D/35和11W1L/12。

## 严格整场轨迹

同一冻结分析器`panel_trajectory.py` SHA256为`f26372ff9e78c06e9be1d5c77f15c21e2bbcc8d1c12bba80a2ecb540f83eb71a`。三批均完整重建104/104，回放哈希、初始身体和正式终局核对失败0。净身体账可用于全部312场；gross收珠/付费完整账分别仅53/104、54/104、56/104，其他场因不支持的记录action kind明确拒绝gross。旧v1报告的104/104 gross覆盖率已被此严格重跑取代，未将未知账填成0或请求步数，也不将故障对手的净身体或资源归零。

| 有效机制整场指标 | v1（53场） | v2（54场） | v3（56场） |
| --- | --- | --- | --- |
| Queen终局存活 | 20/53（37.74%） | 28/54（51.85%） | 28/56（50%） |
| 终局Longest中位 | 32 | 34 | 32.5 |
| 净身体update增长中位 | 318 | 337.5 | 306 |
| 死亡前身体长度损失中位 | 136 | 158 | 136 |
| 净保有身体长度中位 | 133 | 150 | 171 |
| 收珠 / 实际付费损耗中位 | 342 / 9 | 369.5 / 11.5 | 338 / 6.5 |
| 全队死亡：头 / 自身 / 其他身体 / 墙 | 383 / 2798 / 1519 / 0 | 125 / 1274 / 1322 / 2045 | 186 / 1636 / 1580 / 2353 |

各列中位数独立计算，不能用两列中位数相减代替净保有中位数；身体守恒按每场逐条核验，分裂只转移长度。

这是不同种子、不同有效分母的描述统计，不是配对改进证明。v2减少自撞但增加墙死，且死亡长度损失中位更高，不能只看self下降。v2在没有确认出口时选择减少其他单位损失的fallback，可能把同样死局从自身体碰撞改为独自撞墙；此机制与种子均可影响分布。即使原始事件证明行动执行，也不能由死亡类型胜率单独归因策略有效。

## 可证失败链

- **Portals B重复Queen付费损失**：v1/v2各自留出都以Queen 2比3判负。v2原始完整账显示Queen初始3、收珠0、实际付费1、终局2、存活；不存在死亡才能输的问题。一次干区域付费先损失首项分数，其余长单位与总长度不能补偿。v3留出Queen3比3、Longest3比3、总长度9比9，正式平局；此实例与专门物理/政策测试支持干区域付费修补，仍不把不同种子的全局胜率变化归因于它。
- **Stripes A末单位接触**：v2最后HARVEST单位的终次记录为`direct_contact=1`、向东一步，r41（引擎0起算）头碰头；双方最后单位同时清空，正式平局。v1同位置在另一种子被消灭判负。v2接触链可证，不由两种子的胜负差反推出改善；新v3针对末单位交换价值与生存状态检查。
- **v1有效败局**：SAS Portals B（Queen 2比3）、SAS Trauma B（Queen 0比2），murder Stripes A（被消灭）。Queen评分和特殊拓扑仍未通过。
- **v1无效但正式Queen判负的Schooltime两局**：我方Longest195/139、总长度512/591仍因Queen0比3败。它们不贡献有效强度结论，但清楚说明Longest峰值不能越过Queen计分优先级。
- **v3唯一有效本地败局**：murder Arena B，第27轮（引擎r26）被消灭。弱基准面板上也仍存在接触/出生安全缺口，不能仅因102个正式胜场宣布通用策略完成。

上述直接规则、终次动作和精确长度账可核实；更深层的全局调度、拥挤或对手意图仍是待验证解释。各新版本在已看结果后产生，不继承上一版留出独立性；每版阶段单列。v4作为独立冻结原型追加，未改写前三版312场。

## v4完整面板与功能拒绝

v4在14:23:56 UTC冻结，源码包SHA256为`41a8c9fdc7d1dd188d1cd7d74a9b4eeac44633c498f043d4d5d7492017848c2f`，WASM为`f1f125c1be67b8e0bf0e8d9b7240214a62aa62189324c285c7155fc9bd02d4ec`，计划SHA256为`7de18a5aa86b8a0c6bb12e965529acbe4e1c0605cc7b3475f6457ce25a02d3a3`。发现/留出种子分别为2026100604/2026100694。

| v4阶段 | 完成 | 正式结果 | 有效机制结果 | 对手错误排除场数 | 我方运行/基础设施/预算失败 |
| --- | --- | --- | --- | --- | --- |
| 发现 | 16/16 | 16W0L0D | 9W0L0D / 9 | 7 | 0 / 0 / 0 |
| 留出 | 88/88 | 85W1L2D | 45W0L2D / 47 | 41 | 0 / 0 / 0 |
| 合计 | 104/104 | 101W1L2D | 54W0L2D / 56 | 48 | 0 / 0 / 0 |

对手无效动作2099条，保留正式结果且单列48场机制无效分母。[完整严格轨迹](../test-results/generalist-v4-full-trajectory-strict.json)重建104/104、回放/初始身体/正式终局核对失败0；净身体账可用于104场，收珠/实际付费gross仅56场可证，其余为空。有效56场Queen存活25/56（44.64%）、终局Longest中位36、净身体update增长366、死亡长度损失149、净保有170.5、收珠382.5/付费11.5。全队死亡头碰头200、自身1392、其他身体1367、墙2072。与前三版使用不同种子和有效分母，这些描述数字不能证明改进。

v4最坏21,774,119 points，低于90M余量线。唯一正式败局为murder Arena A消灭判负，因对手无效动作单列为机制无效；有效平局为murder Stripes A和SAS Portals B。全部三场未胜结果仍保留，不能把有效0败局称为通过成熟对手确认。

**拒绝采用的原因是功能错误，运行检查没有失败。** [独立封闭通道构造](../tests/generalist_birth_closed_route_test.cpp)在官方C++执行器复现：公开合法视野内，北向永久墙死端的确认延续深度2，东向延续深度8；东向有可能出生头接触，北向没有。v4将可能出生风险排在完整延续之前，选择北向深度2而最终必被堵死。官方stage `df00fc0156858d3b2e26b82b`输出`chosen=N depth=2 outside=0 portal=0 budget=0`。该测试PASS表示成功复现缺陷，不表示候选合格；弱基准101个正式胜场不能推翻确定的物理失败。

v5独立修复排序，在同构造选择东向深度8，并在相同深度的STAR合法视野构造继续避开可能出生头；[功能执行记录](../test-results/generalist-v5-functional-checks.json)区分构造测试与比赛。v5使用自己的预声明面板，不继承v4结果。[紧凑逐场清单](oct6-external-panel-manifest.json)保留五版520个真实结果的来源、地图/源码/WASM/回放哈希、正式胜负、机制资格及预算；v1复现driver为`tools/external_panel_v1_frozen.py`，其字节哈希与原记录一致。

## v5完整面板

v5在14:33:36 UTC冻结，源码包SHA256为`39cbf8c74f2d514ea5c0cb0b3b46fa16ef554486863427f0ebb8966f73b4c7fa`、WASM为`7b2dd8a38996a93c5c3bf45526d74a366409072916000b9d2c169200d4fed40b`。预声明计划SHA256为`87f69689654e68a73ca5fae7576f506c73ac0891e81e6a6ebaf7944b1198c76e`，发现/留出种子2026100605/2026100695。独立协议执行40个构造case、47个frame全通过，最坏8,414,441 points，WASM与正式冻结一致；构造协议检查不是比赛强度证据。

| v5阶段 | 完成 | 正式结果 | 有效机制结果 | 对手错误排除场数 | 我方运行/基础设施/预算失败 |
| --- | --- | --- | --- | --- | --- |
| 发现 | 16/16 | 16W0L0D | 8W0L0D / 8 | 8 | 0 / 0 / 0 |
| 留出 | 88/88 | 86W1L1D | 46W1L1D / 48 | 40 | 0 / 0 / 0 |
| 合计 | 104/104 | 102W1L1D | 54W1L1D / 56 | 48 | 0 / 0 / 0 |

对手无效动作1874条，全部48场保留正式结果且从机制资格单列。最坏比赛23,181,509 points，低于预设90M余量线。SAS Portals B有效败局500轮Queen3比3、Longest3比3，但总长度9比11判负；我方没有单位死亡，说明生存不能代替资源领先。murder Stripes A双方第50轮全部被消灭而平局。两场未胜结果均保留；不从不同种子的比较推断修补提升，也不将弱外部面板当作线上采用依据。

[v5完整严格轨迹](../test-results/generalist-v5-full-trajectory-strict.json)104/104重建，回放/初始身体/正式终局核对失败0；净身体账覆盖全部104场，gross仅56/104，其余明确为空。有效56场Queen存活28/56（50%）、终局Longest中位36、净身体update增长288.5、死亡长度损失121.5、净保有142、收珠314/实际付费9.5；全队死亡头碰头189、自身1239、其他身体1203、墙1300。五版完整重建共520场、问题0，gross可证53+54+56+56+56=275场，另外245场保持未知；这些账目覆盖率与机制资格分母分别验证。

## 真实线上外部确认

v3上传平台v19、提交18674，官方源ZIP下载与本地同字节；真实Unranked三系列共51场、每队页面全17地图，实际链接确定全部ID。raw和终局UI均51/51核对、0问题；正式13W38L：20消灭、9Queen、9Longest判负，Queen存活16/51。我方No-valid-action死亡0，不能自动等同独立核实线上所有CPU/预算。

risq-v为7W10L，Citadel为3W14L，STAR为3W14L。Citadel有14场、2483条No-valid-action死亡；保留全部正式结果，但不作为可靠强度证据，不将其资源归零。无记录双方该类死亡的37场为11W26L，与gross可证37/51分别检查。具体38败场和证据分母见[线上报告](oct6-online51-findings.md)。线上与本地种子、地图实例、对手及版本不同，不能直接把胜率差当作单一缺陷的因果；但本地弱bot胜场未验证成熟外部适应能力，当前不支持长期采用。

根代理已从可见UI核验回退Active v14／Guard v66，原提交评分1532恢复显示。这是旧提交原有评分，不是earned提升。手动Unranked不计rating；上传期间另5场自动比赛只能由平台总计56场16W40L减本组51场13W38L得表差3W2L，尚未逐场raw核验，单列未知而不混入这51场。

## 可支持的结论与复现

五个候选完成预定外部机制面板，未发现本地我方运行或预算失败；v4仍因独立复现的功能缺陷被拒绝采用，v5没有真实线上确认。SAS和murder均会分裂Queen、长期资源与长单位保护较弱，是两个公开机制对手；重复地图与换边不能当作许多独立成熟对手。真实线上外部51场未支持强度采用，已回退旧提交；本地胜场不换算Elo。

只重建、不启动比赛的命令：

```powershell
.venv\Scripts\python.exe tools\panel_trajectory.py --panel test-results\external-panel-20261006 --phase all --out test-results\generalist-v1-full-trajectory-strict.json
.venv\Scripts\python.exe tools\panel_trajectory.py --panel test-results\external-panel-v2-20261006 --phase all --out test-results\generalist-v2-full-trajectory-strict.json
.venv\Scripts\python.exe tools\panel_trajectory.py --panel test-results\external-panel-v3-20261006 --phase all --out test-results\generalist-v3-full-trajectory-strict.json
.venv\Scripts\python.exe tools\panel_trajectory.py --panel test-results\external-panel-v4-20261006 --phase all --out test-results\generalist-v4-full-trajectory-strict.json
.venv\Scripts\python.exe tools\panel_trajectory.py --panel test-results\external-panel-v5-20261006 --phase all --out test-results\generalist-v5-full-trajectory-strict.json
.venv\Scripts\python.exe -m unittest tests.import_online_replays_test tests.online100_evidence_test tests.online_raw_replay_test
```

线上证据导入、实际二进制/UI/净账/gross拒绝与51场边界/集成、包装器合计36项测试通过。根代理另记录完整unittest 102项通过（6.6秒，包括两项固定synthetic真实引擎fixture）；审计代理独立执行其余100项离线检查通过，没有另开候选比赛。证据导入与重建命令不会修改冻结candidate、runner、plan，不安装或执行下载源码，不启动新比赛。本轮另实际执行520场已完成独立外部WASM比赛与51场手动真实线上外部测试，按候选和阶段另列。原始100场回放238,802,240字节、新51场106,249,249字节和候选大型轨迹均保持在忽略目录，不含凭据进入可提交报告。
