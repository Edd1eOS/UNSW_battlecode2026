# 2026-10-06 固定100场：原始回放补充审计

生成时间UTC `2026-10-06T13:42:01.496086+00:00`。这是此前固定100场的证据升级；[原UI发现报告](oct6-online100-findings.md)和[压缩UI证据](oct6-online100-fixture.md)保留原快照，不覆盖。完整机器报告及每局回放SHA见[审计清单](oct6-online100-raw-manifest.json)。

## 来源与可证范围

名单仍为6 Oct 13:13–19:47北京时间的最新100场已完成排位，截止19:48之前；不因结果、地图、对手、缺失或错误换局。21个系列、19个对手、17个地图名称存在重复与相关性。

原始回放取得及完整核对为 **100/100**；提交ID、初始身体、明确队伍归属、每轮状态、正式终局、固定UI种子/地图/死亡事件/累计事件均核对，解析或审计失败0、扫描安全问题0。每场我方匿名header唯一`botId=15719`，并由冻结UI确认平台v14/Guard v66；不能按UI列序或龙ID奇偶推队伍。对手匿名header不证明其提交或私有源码。

根代理在官方Submissions页观察Active v14与完整Download v14 Guard v66链接，再下载[提交15719源码ZIP](https://game.battlecode.au/submissions/15719/download)。ZIP SHA256 `c8d6920ebadf25d30b94786fc441770bcd9df2e7a644897c3315e08befb0149a`；八个成员均与已存档v66同字节，源码包SHA256 `42162e3c924cb13407aa7810c8f8d1fbe7f9a06ae77514ef47804bda2c4a4f61`。仅读ZIP成员并哈希，未解压执行、上传或把源码内容加入此证据。线上提交二进制SHA仍未独立取得。

原始回放约238.8MB，保留在忽略目录`test-results/online100-raw`，不入Git。该清单只保存来源、哈希和统计，没有cookie、token、API key、认证头或下载URL查询参数。下载文件名提供系列来源；官方可见UI下载行为由根代理记录，哈希负责字节复现，不把文件名当身份的唯一依据。

## 直接结果和新观测

- 正式结果仍为46W54L；54败局直接判负：Longest 26/54（48.15%），消灭20/54（37.04%），Queen长度8/54（14.81%）。这不是候选胜率。
- Queen存活25/100。75次Queen死亡：51头碰头、14墙/海带、10其他身体；51次头碰头中10次友军（19.61%）、41次敌军（80.39%）。其他身体10次暂未区分友敌。
- 全队头碰头死亡5177次：友军2168（41.88%）、敌军3009（58.12%）。这是死亡事件数，一次友军相撞会计两条死亡，不能叫2168次碰撞。总分裂19119次。
- Queen有正增长update的局数86/100，净update增长中位2；47/100局Queen分裂，197次分裂累计转给子龙398长度。分裂守恒，不能计作收珠或自主增长，也不能由此判定喂养意图。
- 100/100全队身体守恒残差为0。收珠/付费完整账只有73/100；另外27场含不支持的记录action kind，严格拒绝gross，保留净身体账。73场Queen收珠中位9、实际付费损耗中位6，全队收珠中位354、付费中位8；该分母不可外推到100场。请求MOVE、UI sprint尝试不当作真实付费。
- 当时唯一Longest单位死亡308次（78/100局）：头碰头253、自撞30、墙/海带15、其他身体10；其中54条在死亡瞬间把原比较优势反转给对方。可能同局多次，不能等同54个直接败因。
- 54敗局中53/54曾在完整轮末比较领先，49/54曾连续至少10轮领先。领先按消灭→Queen→Longest→总长度计算；仍只称轮末连续，不能声称每个轮内时刻。
- 70/100局实际历史Longest峰值高于终局值，差值中位3。26个Longest败局终局落后中位13.5；其中实际峰值大于对方终局5局、相等1局、仍小于20局。故既有保不住已经长出的单位，也有从未长到足够长度的失败。峰值含初始/分裂继承长度，不等同自主增长。

UI的Longest so far取初始与轮末峰值；逐事件实际峰值可更高。例如M1238557我方轮末15、轮内17；M1237739对方轮末14、轮内15。这属于明确采样口径，并非身份或引擎核对错误。

## 地图分组（发现样本）

| 地图 | W–L/局数 | 消灭败局 | Queen存活 | 终局Longest中位 | 友军头死亡 | 自身体死亡 |
| --- | --- | --- | --- | --- | --- | --- |
| Around UNSW | 4–0/4 | 0 | 0/4 | 30 | 326 | 7 |
| Australia | 3–3/6 | 0 | 0/6 | 25.5 | 72 | 0 |
| Autarky | 5–2/7 | 1 | 5/7 | 17 | 24 | 6 |
| Default | 1–3/4 | 1 | 0/4 | 8 | 38 | 0 |
| Devil | 2–6/8 | 5 | 0/8 | 0 | 444 | 0 |
| Islands | 4–5/9 | 0 | 0/9 | 22 | 194 | 5 |
| Maze | 0–4/4 | 0 | 0/4 | 14 | 136 | 5 |
| Portals | 2–3/5 | 0 | 0/5 | 14 | 96 | 132 |
| Prisoners Dilemma | 6–3/9 | 0 | 8/9 | 13 | 12 | 0 |
| Queen Of Spades | 3–4/7 | 3 | 2/7 | 4 | 46 | 51 |
| Schooltime | 4–4/8 | 0 | 8/8 | 20.5 | 156 | 3 |
| Slithery Fight | 1–4/5 | 0 | 0/5 | 23 | 402 | 1 |
| Stripes | 0–3/3 | 3 | 0/3 | 0 | 0 | 0 |
| Tower Defense | 2–2/4 | 0 | 0/4 | 19.5 | 120 | 0 |
| Trauma | 2–1/3 | 0 | 2/3 | 6 | 4 | 0 |
| Trophy | 1–7/8 | 7 | 0/8 | 0 | 10 | 0 |
| weakhold | 6–0/6 | 0 | 0/6 | 10 | 88 | 0 |

## 54个败场：判负与观测分离

回合采用网页1起算。`Q峰`为实际观测峰值；`Q转`为Queen分裂转走总长度；`L峰→末/敌末`是全队历史峰值、终局Longest与敌方终局Longest。`独L死`是当时唯一最长单位死亡条数。友头为全队友军头死亡条数。碰撞原因和此前增长不是自动确定的根本策略因果。

| Match | 对手 / 地图 | 直接规则 | Queen死亡 | Q峰 / Q转 | L峰→末/敌末 | 独L死 / 友头 | 连续领先轮数 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| [M1239660](https://game.battlecode.au/battles/1239660) | Just Reboot Normalize / Devil | 消灭 | r32 头碰头（友军） | 5 / 0 | 13→0/5 | 2 / 10 | 30 |
| [M1238556](https://game.battlecode.au/battles/1238556) | Eric Allen Le / Islands | Longest | r91 头碰头（敌军） | 13 / 0 | 22→22/25 | 7 / 24 | 65 |
| [M1238559](https://game.battlecode.au/battles/1238559) | Eric Allen Le / Maze | Longest | r187 墙/海带 | 37 / 42 | 37→15/67 | 2 / 22 | 228 |
| [M1238557](https://game.battlecode.au/battles/1238557) | Eric Allen Le / Devil | 消灭 | r29 头碰头（敌军） | 5 / 2 | 17→0/4 | 6 / 46 | 67 |
| [M1238558](https://game.battlecode.au/battles/1238558) | Eric Allen Le / Trophy | 消灭 | r161 头碰头（敌军） | 3 / 0 | 12→0/5 | 4 / 2 | 109 |
| [M1237742](https://game.battlecode.au/battles/1237742) | Citadel Insecurities / Slithery Fight | Longest | r108 头碰头（敌军） | 25 / 20 | 29→23/29 | 3 / 48 | 106 |
| [M1237739](https://game.battlecode.au/battles/1237739) | Citadel Insecurities / Default | 消灭 | r160 头碰头（敌军） | 7 / 2 | 12→0/9 | 6 / 4 | 129 |
| [M1237741](https://game.battlecode.au/battles/1237741) | Citadel Insecurities / Portals | Longest | r77 其他身体 | 3 / 0 | 15→14/21 | 4 / 22 | 184 |
| [M1237740](https://game.battlecode.au/battles/1237740) | Citadel Insecurities / Prisoners Dilemma | Queen长度 | 存活 | 13 / 2 | 13→13/14 | 0 / 2 | 449 |
| [M1237743](https://game.battlecode.au/battles/1237743) | Citadel Insecurities / Devil | 消灭 | r33 头碰头（友军） | 7 / 4 | 7→0/4 | 5 / 6 | 32 |
| [M1234879](https://game.battlecode.au/battles/1234879) | waddledee / Stripes | 消灭 | r120 头碰头（敌军） | 3 / 0 | 3→0/3 | 1 / 0 | 38 |
| [M1234876](https://game.battlecode.au/battles/1234876) | waddledee / Tower Defense | Longest | r131 头碰头（敌军） | 4 / 0 | 19→17/18 | 1 / 20 | 81 |
| [M1234020](https://game.battlecode.au/battles/1234020) | 404 Not Found / Maze | Longest | r37 其他身体 | 6 / 4 | 15→13/45 | 1 / 46 | 3 |
| [M1234018](https://game.battlecode.au/battles/1234018) | 404 Not Found / Prisoners Dilemma | Queen长度 | r174 头碰头（友军） | 3 / 0 | 13→13/27 | 0 / 2 | 0 |
| [M1233049](https://game.battlecode.au/battles/1233049) | ASI / Australia | Longest | r262 其他身体 | 4 / 2 | 20→18/19 | 5 / 10 | 277 |
| [M1233047](https://game.battlecode.au/battles/1233047) | ASI / Schooltime | Longest | 存活 | 4 / 6 | 30→20/35 | 7 / 6 | 33 |
| [M1233048](https://game.battlecode.au/battles/1233048) | ASI / Trauma | Longest | r253 墙/海带 | 4 / 2 | 6→6/13 | 0 / 4 | 169 |
| [M1233050](https://game.battlecode.au/battles/1233050) | ASI / Stripes | 消灭 | r97 头碰头（敌军） | 5 / 2 | 5→0/5 | 2 / 0 | 50 |
| [M1230141](https://game.battlecode.au/battles/1230141) | wawow830 / Schooltime | Longest | 存活 | 4 / 4 | 30→21/40 | 4 / 32 | 249 |
| [M1230140](https://game.battlecode.au/battles/1230140) | wawow830 / Default | Longest | r484 墙/海带 | 10 / 8 | 57→7/11 | 2 / 6 | 483 |
| [M1228212](https://game.battlecode.au/battles/1228212) | combilove / Islands | Longest | r142 墙/海带 | 4 / 2 | 27→27/50 | 9 / 10 | 160 |
| [M1228210](https://game.battlecode.au/battles/1228210) | combilove / Queen Of Spades | 消灭 | r81 头碰头（敌军） | 8 / 0 | 8→0/4 | 4 / 6 | 65 |
| [M1225881](https://game.battlecode.au/battles/1225881) | risq-v / Australia | Longest | r97 头碰头（敌军） | 6 / 0 | 33→33/46 | 3 / 2 | 96 |
| [M1225880](https://game.battlecode.au/battles/1225880) | risq-v / Prisoners Dilemma | Queen长度 | 存活 | 7 / 0 | 13→13/19 | 0 / 0 | 3 |
| [M1225501](https://game.battlecode.au/battles/1225501) | wawow830 / Default | Longest | r279 头碰头（敌军） | 5 / 0 | 15→9/12 | 2 / 12 | 175 |
| [M1225499](https://game.battlecode.au/battles/1225499) | wawow830 / Devil | 消灭 | r134 头碰头（敌军） | 6 / 4 | 8→0/9 | 7 / 20 | 133 |
| [M1225502](https://game.battlecode.au/battles/1225502) | wawow830 / Trophy | 消灭 | r91 头碰头（敌军） | 4 / 0 | 8→0/5 | 5 / 0 | 28 |
| [M1225050](https://game.battlecode.au/battles/1225050) | Nexus Lab / Queen Of Spades | 消灭 | r177 头碰头（敌军） | 4 / 0 | 4→0/4 | 1 / 0 | 56 |
| [M1225049](https://game.battlecode.au/battles/1225049) | Nexus Lab / Islands | Longest | r103 头碰头（敌军） | 8 / 0 | 18→12/31 | 4 / 4 | 112 |
| [M1223837](https://game.battlecode.au/battles/1223837) | unemployed / Slithery Fight | Longest | r171 墙/海带 | 25 / 40 | 25→23/37 | 3 / 82 | 101 |
| [M1220727](https://game.battlecode.au/battles/1220727) | WaterCandle / Trophy | 消灭 | r41 头碰头（敌军） | 8 / 0 | 13→0/6 | 2 / 2 | 19 |
| [M1220726](https://game.battlecode.au/battles/1220726) | WaterCandle / Schooltime | Longest | 存活 | 4 / 2 | 26→26/41 | 0 / 12 | 305 |
| [M1220730](https://game.battlecode.au/battles/1220730) | WaterCandle / Devil | Longest | r28 头碰头（友军） | 6 / 0 | 28→26/67 | 5 / 54 | 21 |
| [M1220729](https://game.battlecode.au/battles/1220729) | WaterCandle / Tower Defense | Longest | r205 墙/海带 | 8 / 6 | 21→13/20 | 0 / 28 | 367 |
| [M1220728](https://game.battlecode.au/battles/1220728) | WaterCandle / Autarky | 消灭 | r236 头碰头（敌军） | 6 / 0 | 16→0/4 | 2 / 2 | 235 |
| [M1220246](https://game.battlecode.au/battles/1220246) | vom / Schooltime | Longest | 存活 | 4 / 2 | 16→13/18 | 3 / 10 | 67 |
| [M1220243](https://game.battlecode.au/battles/1220243) | vom / Trophy | 消灭 | r87 头碰头（敌军） | 3 / 0 | 5→0/4 | 6 / 0 | 8 |
| [M1219139](https://game.battlecode.au/battles/1219139) | canDid / Portals | Queen长度 | r134 其他身体 | 3 / 0 | 23→16/7 | 9 / 14 | 17 |
| [M1215720](https://game.battlecode.au/battles/1215720) | That's That, and This is This / Maze | Queen长度 | r298 头碰头（敌军） | 12 / 0 | 17→17/18 | 2 / 38 | 168 |
| [M1215723](https://game.battlecode.au/battles/1215723) | That's That, and This is This / Trophy | 消灭 | r80 头碰头（敌军） | 24 / 0 | 24→0/8 | 8 / 0 | 38 |
| [M1215722](https://game.battlecode.au/battles/1215722) | That's That, and This is This / Devil | 消灭 | r50 头碰头（敌军） | 9 / 0 | 11→0/7 | 11 / 42 | 49 |
| [M1215362](https://game.battlecode.au/battles/1215362) | Martin Shkreli’s Defense Team / Islands | Longest | r42 头碰头（敌军） | 4 / 0 | 35→35/38 | 3 / 4 | 68 |
| [M1215364](https://game.battlecode.au/battles/1215364) | Martin Shkreli’s Defense Team / Queen Of Spades | Longest | r395 其他身体 | 6 / 4 | 7→4/40 | 3 / 0 | 330 |
| [M1215363](https://game.battlecode.au/battles/1215363) | Martin Shkreli’s Defense Team / Portals | Longest | r77 其他身体 | 3 / 0 | 26→20/39 | 3 / 16 | 160 |
| [M1215366](https://game.battlecode.au/battles/1215366) | Martin Shkreli’s Defense Team / Trophy | 消灭 | r58 头碰头（敌军） | 3 / 0 | 4→0/3 | 2 / 0 | 4 |
| [M1214259](https://game.battlecode.au/battles/1214259) | Squishy / Slithery Fight | Longest | r94 头碰头（敌军） | 25 / 20 | 25→25/56 | 7 / 68 | 93 |
| [M1214263](https://game.battlecode.au/battles/1214263) | Squishy / Queen Of Spades | 消灭 | r150 头碰头（敌军） | 3 / 0 | 4→0/4 | 2 / 0 | 58 |
| [M1214260](https://game.battlecode.au/battles/1214260) | Squishy / Stripes | 消灭 | r74 头碰头（敌军） | 4 / 0 | 4→0/3 | 1 / 0 | 43 |
| [M1211144](https://game.battlecode.au/battles/1211144) | WaterCandle / Islands | Longest | r100 头碰头（敌军） | 5 / 0 | 33→33/58 | 4 / 16 | 349 |
| [M1211142](https://game.battlecode.au/battles/1211142) | WaterCandle / Autarky | Queen长度 | r66 头碰头（敌军） | 3 / 0 | 26→26/4 | 1 / 2 | 24 |
| [M1211146](https://game.battlecode.au/battles/1211146) | WaterCandle / Trophy | 消灭 | r80 头碰头（敌军） | 4 / 0 | 10→0/7 | 5 / 2 | 53 |
| [M1210923](https://game.battlecode.au/battles/1210923) | Hydra / Slithery Fight | Queen长度 | r156 墙/海带 | 25 / 36 | 25→23/20 | 2 / 94 | 154 |
| [M1210922](https://game.battlecode.au/battles/1210922) | Hydra / Maze | Queen长度 | r214 头碰头（友军） | 20 / 16 | 20→9/22 | 3 / 30 | 213 |
| [M1210919](https://game.battlecode.au/battles/1210919) | Hydra / Australia | Longest | r76 头碰头（敌军） | 4 / 0 | 15→15/26 | 5 / 10 | 67 |

## 待验证机制与限制

Trophy 7/8败且全部被消灭、Devil 6/8败其中5次消灭；Devil有444条友军头死亡且Queen存活0/8。Portals的132条自撞占全部210条的62.86%。这支持优先检查狭道/出口容量、友军时序、门户后的真实身体与路径承诺；但没有证明对手故意围堵，或每条死亡由同一种代码缺陷造成。

Queen增长、付费与分裂同时存在，净长度兑现不足。可检验的通用机制是Queen独立保留资源与退路、关键长单位减少接触损失、分裂数量受可用空间和交通约束。当前表仅给假说和可观测验收项，没有从对手计数逆推出私有算法，也不能证明新候选已经改进。

匿名对手提交未验证；当前冻结100场只用于发现。对手无效动作场仍完整保留在这100场中，不能因失去gross账就删局。离线全图仅用于审计，不得给bot提供隐藏信息。

## 离线复现

取得相同官方ZIP/replay后：

```powershell
.venv\Scripts\python.exe tools\import_online_replays.py --download-dir '<下载目录>' --source-zip '<官方下载源码ZIP>' --archive-source opponents\v66-queen-threat-buffer --source-link-confirmed
.venv\Scripts\python.exe tools\report_online_raw.py
.venv\Scripts\python.exe -m unittest tests.import_online_replays_test tests.online100_evidence_test tests.online_raw_replay_test
```

`--source-link-confirmed`仅在有可信官方可见链接记录时使用。导入器拒绝路径穿越、嵌套成员、符号链接、超大成员和不同字节重复；单场解析失败记录原ID并继续，不用其他比赛替换。单场缓存由原回放/UI/源包/分析器/官方decoder哈希绑定。上述重建不启动任何比赛；原始回放缺失时实回放集成检查显式skip。
