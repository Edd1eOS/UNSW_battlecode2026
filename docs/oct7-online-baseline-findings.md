# Oct7 Active v14 外部线上 51 场发现审计

本轮预声明的旧 Active v14／submission **15719** 对三个外部队伍、每队实际17图，共51场Unranked，正式 **20W31L**。这份报告用于定位现有系统缺陷，不是新候选强度或留出验收。

原始录像、终局UI、初始化/完整每轮净账与执行收珠/支付gross账均 **51/51** 通过，扫描/审计问题0，分析依赖全程未变。我方No-valid-action死亡0；STAR Devil [M1314508](https://game.battlecode.au/battles/1314508) 有对手2次该类死亡，仍保留正式消灭败。双方无记录该类死亡的50场为 **20W30L**；这个子集并不证明所有CPU/运行时状态均正常。

逐场原始哈希、UI哈希、实际对手header、资源全账和生命周期见 [证据清单](oct7-online-baseline-findings-manifest.json)。

| 对手 | 正式 | Queen存活 | 消灭/Queen/Longest败 | 无无效动作记录子集 |
|---|---:|---:|---:|---:|
| STAR | 7W10L | 4/17 | 5/4/1 | 7W9L |
| risq-v | 9W8L | 5/17 | 1/4/3 | 9W8L |
| very creative team name | 4W13L | 4/17 | 5/3/5 | 4W13L |

## 直接计分与生命周期事实

31败按官方首个判负项为11消灭、11Queen、9Longest。先判是否消灭；双方仍有龙时依Queen长度、最长单位、总长度逐项比较。不是把31场都解释成Queen死亡。

11场Queen败分为：**6场我方Queen已死、对方仍活；5场双方Queen活着但我方较短**。后一类包括Prisoners Dilemma的7比11、4比12，以及Trauma的3比10、3比27、7比15。保持低长度Queen存活不能自动赢首项。

9场Longest败中7场双方Queen死，2场Schooltime双方Queen均活且等长3。下表使用全场事件历史峰（包括初始和分裂继承），不是自主收入；死亡资本是全队实际死亡前身体长度之和。

| 比赛 | 我/敌终局Q | 我历史峰→终局L / 敌终局L | 我死亡资本 | 唯一Longest死亡次数/累计分数跌落 |
|---|---:|---:|---:|---:|
| [M1314342](https://game.battlecode.au/battles/1314342) very creative team name／Default | 0/0 | 12→12 / 24 | 140 | 1/1 |
| [M1314344](https://game.battlecode.au/battles/1314344) very creative team name／Islands | 0/0 | 16→13 / 35 | 207 | 2/2 |
| [M1314345](https://game.battlecode.au/battles/1314345) very creative team name／Maze | 0/0 | 30→9 / 85 | 252 | 1/2 |
| [M1314346](https://game.battlecode.au/battles/1314346) very creative team name／Portals | 0/0 | 20→18 / 41 | 450 | 6/31 |
| [M1314349](https://game.battlecode.au/battles/1314349) very creative team name／Schooltime | 3/3 | 17→13 / 20 | 234 | 2/9 |
| [M1314402](https://game.battlecode.au/battles/1314402) risq-v／Australia | 0/0 | 38→16 / 33 | 197 | 1/24 |
| [M1314407](https://game.battlecode.au/battles/1314407) risq-v／Maze | 0/0 | 34→34 / 51 | 320 | 2/8 |
| [M1314411](https://game.battlecode.au/battles/1314411) risq-v／Schooltime | 3/3 | 35→34 / 39 | 745 | 1/2 |
| [M1314505](https://game.battlecode.au/battles/1314505) STAR／Australia | 0/0 | 26→17 / 26 | 762 | 10/54 |

仅risq Australia我历史峰38高于敌終局33；STAR Australia历史峰26等于敌终局26；其余7场连我历史峰也低于敌终局最长。因此这一组同时有资本保留和增长不足证据，不能全归因于已经造出的冠军龙死亡。累计Longest分数跌落允许后续恢复，不等于终局差额；表格不证明保住某次峰就能翻盘。

## 资源全账

净收入=实际收珠−成功付费步；初始/分裂继承不记收入。净保留=终局总身体−初始身体；每场严格满足净保留=净收入−死亡资本。下表均为逐场中位数；Δ是每场我减敌差值的中位数，不能由两列中位数直接相减。

| 全部正式分组 | n | 净收入我/敌/Δ | 净保留我/敌/Δ | 死亡资本我/敌/Δ |
|---|---:|---:|---:|---:|
| 全部 | 51 | 299/506/-85 | 30/88/-18 | 244/419/-25 |
| 赢 | 20 | 423.5/393.5/69.5 | 58.5/30.0/49.5 | 360.0/338.5/14.5 |
| 消灭败 | 11 | 75/321/-134 | -6/90/-104 | 81/246/-51 |
| Queen败 | 11 | 350/377/-24 | 15/31/-13 | 337/361/-23 |
| Longest败 | 9 | 301/891/-289 | 49/205/-156 | 252/803/-214 |

全部51场净收入合计我24954、敌35185；净保留我2872、敌5241；实际死亡资本我22082、敌29944。对手死亡资本更大仍保留更多，说明绝对死亡总量必须连同收入与初始资本看，不能反推对手在故意献祭。

| 无无效动作记录敏感性 | n | 净收入我/敌/Δ中位数 | 净保留我/敌/Δ中位数 |
|---|---:|---:|---:|
| 全部 | 50 | 294.0/477.0/-86.0 | 32.5/88.0/-16.0 |
| 消灭败 | 10 | 68.5/253.5/-210.0 | -6.0/94.0/-104.0 |
| Queen败 | 11 | 350/377/-24 | 15/31/-13 |
| Longest败 | 9 | 301/891/-289 | 49/205/-156 |

剔除仅这一场有对手无效动作的记录后，净收入合计我23863、敌34402；净保留我2884、敌5177。Queen与Longest败组数字不变，消灭败分母11→10。正式51场结果没有删除。

## 全程优势持续性

使用完整的每轮末官方首计分领先关系，不挑选最有利窗口。51场中50场曾领先、48场随后至少失去过一次领先；逐场领先轮数中位149、最长连续领先中位98、领先轮比例中位44.4%。初始相等状态单独保留，每轮末领先从r0起采样。

固定阶段覆盖所有实际发生轮次：官方0–99、100–299、300至正式终局；提前结束的比赛没有补造后期轮次。下面计数汇合各场实际轮次，不能当作互相独立的样本。

| 全51阶段 | 实际轮样本 | 我领先 | 敌领先 | 平手 |
|---|---:|---:|---:|---:|
| 早0–99 | 5096 | 2967 | 1620 | 509 |
| 中100–299 | 8993 | 3944 | 4996 | 53 |
| 末300–终局 | 7583 | 3130 | 4447 | 6 |

Queen败组的我领先轮数按早/中/末为845/950/471，对应实际样本1100/2200/2200；Longest败组为497/762/247，对应900/1800/1800。全11场Queen败有10场曾领先、9场Longest败全部曾领先并失去领先。敏感性50场阶段我领先2918/3770/2983，实际样本4996/8793/7432；完整逐组持续领先及失去领先次数保存在证据清单。

## 7次友军Queen头碰撞

38次Queen死亡为28H、8W、1O、1S；28H均有同一个明确动作内双头死亡配对，21敌军、7友军。下面的7次中，6个碰撞伙伴在Queen最近自己的输入时已经是龙头，且位于其合法7×7窗口；1个是Queen自己同轮新生的child。6次工龙移动撞Queen时，Queen头位于该工龙本次输入窗口；另1次Queen主动撞友军头，对方也位于Queen输入窗口。这只说明当前观察可见，不保证有可行安全替代，未恢复私有Memory/Atlas。

| 比赛 | UI轮 / 原始r | Queen最后动作 | 实际碰撞动作 | 伙伴类别 |
|---|---:|---|---|---|
| [M1314405](https://game.battlecode.au/battles/1314405) risq-v／Devil | 26 / 25 | Q1 MOVE S | ID12 MOVE N | 已存在可见head ID12 |
| [M1314407](https://game.battlecode.au/battles/1314407) risq-v／Maze | 225 / 224 | Q1 SPLIT 2 | ID123 MOVE E | 已存在可见head ID123 |
| [M1314408](https://game.battlecode.au/battles/1314408) risq-v／Portals | 76 / 75 | Q0 MOVE N | ID0 MOVE N | 已存在可见head ID22 |
| [M1314417](https://game.battlecode.au/battles/1314417) risq-v／weakhold | 239 / 238 | Q1 MOVE W | ID17 MOVE E | 已存在可见head ID17 |
| [M1314508](https://game.battlecode.au/battles/1314508) STAR／Devil | 51 / 50 | Q0 SPLIT 2 | ID28 MOVE S | 已存在可见head ID28 |
| [M1314510](https://game.battlecode.au/battles/1314510) STAR／Maze | 442 / 441 | Q0 SPLIT 2 | ID435 MOVE S | 同轮自己的child ID435 |
| [M1314517](https://game.battlecode.au/battles/1314517) STAR／Tower Defense | 197 / 196 | Q1 MOVE N | ID33 MOVE S | 已存在可见head ID33 |

STAR Maze M1314510 的原始r441：Queen0 SPLIT2产生child435（头4,17、颈4,16），child同轮MOVE S，Queen和child在同一动作中头碰撞死亡。它是自己的新生尾头事故，不是敌军新生威胁；当前窗口可见不能证明父子联合存在安全出路。

## 通用算法建议与证据边界

这些事实支持继续分别测试三个机制：所有提前返回和最后fallback都经过同一动作验证，尤其在没有可行移动时最小化同队Queen/最后单位损失；分裂要联合评估静止父体、反转子体的当轮首步与后续机会，未知门户/其他龙可能移动时保留未知；资源分配同时维护Queen可持续净增长与主Longest资本的持续增长/保留，不能把人口或瞬时收珠作为首计分胜利的替代。5场存活但较短的Queen败使“仅保活”不是完整目标。

以上是待验证设计，不是已证明会提高胜率的改动。没有识别对手私有源码或战术意图；原始全身体仅用于赛后账本和可见性诊断，不作为bot输入。这51场与Oct6候选51场的种子、地图实例及对手版本不同，不能用胜率差归因于一项策略；相关系列也不能换算Elo。

## 来源与复验

请求前冻结清单SHA `13dcf8340cad68ae1bf7d1bed70fc677629209e0dbe96d0cf89e6a583b5d52ca`；实际比赛ID来自三个Root页面快照的17条literal href，不按连续ID推算。实际请求顺序为novel（series1314339）、risq（1314401）、STAR（1314504），共51；滚动小时额度60→9，整轮授权上限102。额度后值为Root观察记录，与离线原始验证分别标注在request-log中。中途看到STAR1314506是最终系列的Game3，不是镜像系列的证据。

15719源码依据是Oct6同一不可变提交的可信官方下载ZIP SHA `c8d6920ebadf25d30b94786fc441770bcd9df2e7a644897c3315e08befb0149a`，不是冒称本轮重新下载；八个成员与当前冻结源字节完全吻合。本轮路径/哈希/大小JSON口径源码包SHA `7b34540202f70a60c6ddaacfdfe9ab19cc4e6aec222e3d11f6459b415b5fc4ee`。旧文件名+字节口径42162...不能直接与之相比较。本地编译WASM SHA4d4f...不等于平台二进制下载证明。每场原始header唯一botId15719和终局v14 UI共同核定我方身份/side；匿名对手header不是其私有源码证明。

```powershell
.venv\Scripts\python.exe tools/audit_online_panel.py --manifest test-results/oct7-online-baseline-selection.json --download-dir 'D:/edge下载' --ui-dir test-results/oct7-online-baseline-ui --out test-results/oct7-online-baseline-raw --submission-proof test-results/oct7-active-v14-submission-proof.json --freeze-record test-results/oct7-active-v14-panel/candidate/freeze.json --submission-id 15719 --platform-version 14 --our-team-id 1035 --expected-count 51
.venv\Scripts\python.exe tools/oct7_online_baseline_lifecycle.py --audit-dir test-results/oct7-online-baseline-raw --out <new-output.json>
```

冷审计源、实际selection、请求log、ZIP成员CRC预检、原始index和最终lifecycle均由证据清单逐一哈希绑定。所有原Oct6文档、原审计工具和候选保持原字节；此次未启动任何匹配或网站动作。
