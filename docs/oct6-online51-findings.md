# 2026-10-06 Generalist-v3：真实外部线上51场

记录UTC `2026-10-06T14:13:39.737431+00:00`。预先计划见[线上外部计划](oct6-online-external-plan.md)，逐场哈希与完整数值见[证据清单](oct6-online51-manifest.json)。原v14的[固定100场发现证据](oct6-online100-raw-findings.md)保留不覆盖；这是新冻结候选对三个真实外部队伍的Unranked系列。

## 证据覆盖与结果

- 实际rendered链接明确选中51个ID，计划分母51；不从series first ID猜连续区间、不按胜负换局。原始回放完整核对51/51，终局UI核对51/51，gross账37/51；分母分开。
- 我方唯一官方回放botId `18674`，来源记录对应平台v19，冻结源码包SHA `cfbc144413bce11a4e65381aabf6d9ce85e653defb42534d05acd878d7a08b43`。根代理官方源码下载记录ZIP SHA `c1d72fff598c6dc6db5f329640631a9e3e353f207020ac29213eab71a6d7b009`，所有下载成员与冻结本地成员哈希一致。源码包哈希为路径/哈希/大小JSON口径，不能与旧compare文件名+字节口径混用。未独立取得平台二进制SHA；匿名对手header不证明其提交或私有源码。
- 正式结果：{'loss': 38, 'win': 13}。败场直接规则：{'longest': 9, 'queen': 9, 'elimination': 20}。我方Queen终局存活16/51；死亡原因代码{'S': 3, 'H': 27, 'W': 4, 'O': 1}，头碰头关系{'enemy': 27}。H=头碰头、S=自身身体、W=墙/海带、O=其他身体。
- 我方记录的无效动作死亡0；该数字不自动等于独立核实全部线上CPU/预算正常。没有完整可证gross的场次保留unknown和原结果，不能用请求步数填付费或删局。

- 对手无效动作死亡共2483条，发生于14场；所有正式胜负保留，但这些场不作为可靠强度证据。双方均无记录此类死亡的37场正式结果为{'loss': 26, 'win': 11}。此分组与gross可证性分别检查；对手无效动作不将其真实净身体或资源自动归零。

| 对手 | 完整回放局数 | 正式结果 | Queen存活 | 终局Longest中位 | 败场直接规则 |
| --- | --- | --- | --- | --- | --- |
| Citadel Insecurities | 17 | {'loss': 14, 'win': 3} | 4/17 | 3 | {'queen': 3, 'longest': 4, 'elimination': 7} |
| STAR | 17 | {'loss': 14, 'win': 3} | 5/17 | 0 | {'elimination': 11, 'queen': 2, 'longest': 1} |
| risq-v | 17 | {'loss': 10, 'win': 7} | 7/17 | 24 | {'longest': 4, 'queen': 4, 'elimination': 2} |

无记录双方No-valid-action死亡的分组：

- Citadel Insecurities：{'loss': 2, 'win': 1}；对手此类死亡2483条/14场。无该记录不等于已独立核验所有运行与预算字段。

- STAR：{'loss': 14, 'win': 3}；对手此类死亡0条/0场。无该记录不等于已独立核验所有运行与预算字段。

- risq-v：{'loss': 10, 'win': 7}；对手此类死亡0条/0场。无该记录不等于已独立核验所有运行与预算字段。

## 全部败场：直接判负与观测分开

回合为网页1起算。Longest峰值含初始/分裂继承；峰值→终局差不自动等于某个单位的死亡损失。`独L死`是当时唯一最长单位死亡条数。没有根据计数倒推对手意图或私有代码。

| Match | 对手 / 地图 | 直接规则 | Queen终局或死亡 | Longest峰→末 / 对方末 | 独L死 | 连续领先轮数 | gross可证 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| [M1249231](https://game.battlecode.au/battles/1249231) | risq-v / Around UNSW | longest | r17 S | 37→30 / 37 | 1 | 151 | 是 |
| [M1249232](https://game.battlecode.au/battles/1249232) | risq-v / Australia | queen | r357 H enemy | 21→19 / 43 | 2 | 352 | 是 |
| [M1249234](https://game.battlecode.au/battles/1249234) | risq-v / Default | longest | r61 H enemy | 16→14 / 20 | 2 | 121 | 是 |
| [M1249235](https://game.battlecode.au/battles/1249235) | risq-v / Devil | elimination | r186 H enemy | 12→0 / 19 | 1 | 185 | 是 |
| [M1249236](https://game.battlecode.au/battles/1249236) | risq-v / Islands | queen | r76 H enemy | 28→21 / 44 | 2 | 72 | 是 |
| [M1249239](https://game.battlecode.au/battles/1249239) | risq-v / Prisoners Dilemma | queen | 活，L4 | 20→19 / 18 | 0 | 221 | 是 |
| [M1249241](https://game.battlecode.au/battles/1249241) | risq-v / Schooltime | longest | 活，L3 | 32→27 / 59 | 3 | 114 | 是 |
| [M1249242](https://game.battlecode.au/battles/1249242) | risq-v / Slithery Fight | longest | r129 O | 29→27 / 70 | 1 | 36 | 是 |
| [M1249245](https://game.battlecode.au/battles/1249245) | risq-v / Trauma | queen | 活，L6 | 20→20 / 17 | 0 | 388 | 是 |
| [M1249246](https://game.battlecode.au/battles/1249246) | risq-v / Trophy | elimination | r32 H enemy | 14→0 / 4 | 3 | 18 | 是 |
| [M1249270](https://game.battlecode.au/battles/1249270) | Citadel Insecurities / Around UNSW | queen | r206 H enemy | 27→5 / 78 | 3 | 157 | 未知 |
| [M1249271](https://game.battlecode.au/battles/1249271) | Citadel Insecurities / Australia | longest | r167 H enemy | 29→9 / 75 | 5 | 152 | 未知 |
| [M1249272](https://game.battlecode.au/battles/1249272) | Citadel Insecurities / Autarky | longest | r286 H enemy | 26→2 / 15 | 2 | 282 | 未知 |
| [M1249273](https://game.battlecode.au/battles/1249273) | Citadel Insecurities / Default | elimination | r133 H enemy | 9→0 / 9 | 3 | 115 | 未知 |
| [M1249274](https://game.battlecode.au/battles/1249274) | Citadel Insecurities / Devil | elimination | r50 H enemy | 10→0 / 4 | 3 | 49 | 未知 |
| [M1249275](https://game.battlecode.au/battles/1249275) | Citadel Insecurities / Islands | elimination | r91 H enemy | 19→0 / 18 | 4 | 87 | 未知 |
| [M1249276](https://game.battlecode.au/battles/1249276) | Citadel Insecurities / Maze | longest | r221 W | 63→18 / 39 | 1 | 423 | 未知 |
| [M1249279](https://game.battlecode.au/battles/1249279) | Citadel Insecurities / Queen Of Spades | elimination | r223 H enemy | 5→0 / 3 | 2 | 175 | 是 |
| [M1249280](https://game.battlecode.au/battles/1249280) | Citadel Insecurities / Schooltime | longest | 活，L3 | 23→3 / 68 | 4 | 104 | 未知 |
| [M1249281](https://game.battlecode.au/battles/1249281) | Citadel Insecurities / Slithery Fight | queen | r186 S | 39→39 / 23 | 3 | 182 | 未知 |
| [M1249282](https://game.battlecode.au/battles/1249282) | Citadel Insecurities / Stripes | elimination | r160 H enemy | 3→0 / 5 | 1 | 8 | 是 |
| [M1249283](https://game.battlecode.au/battles/1249283) | Citadel Insecurities / Tower Defense | elimination | r279 S | 10→0 / 8 | 3 | 231 | 未知 |
| [M1249284](https://game.battlecode.au/battles/1249284) | Citadel Insecurities / Trauma | queen | r468 H enemy | 30→4 / 31 | 1 | 467 | 未知 |
| [M1249285](https://game.battlecode.au/battles/1249285) | Citadel Insecurities / Trophy | elimination | r43 H enemy | 12→0 / 4 | 4 | 34 | 未知 |
| [M1249302](https://game.battlecode.au/battles/1249302) | STAR / Around UNSW | elimination | r31 H enemy | 43→0 / 22 | 3 | 30 | 是 |
| [M1249303](https://game.battlecode.au/battles/1249303) | STAR / Australia | elimination | r119 H enemy | 21→0 / 18 | 4 | 118 | 是 |
| [M1249304](https://game.battlecode.au/battles/1249304) | STAR / Autarky | elimination | r162 H enemy | 23→0 / 18 | 4 | 121 | 是 |
| [M1249305](https://game.battlecode.au/battles/1249305) | STAR / Default | elimination | r206 H enemy | 13→0 / 4 | 3 | 210 | 是 |
| [M1249306](https://game.battlecode.au/battles/1249306) | STAR / Devil | elimination | r79 H enemy | 20→0 / 4 | 2 | 68 | 是 |
| [M1249307](https://game.battlecode.au/battles/1249307) | STAR / Islands | elimination | r86 H enemy | 23→0 / 8 | 2 | 82 | 是 |
| [M1249308](https://game.battlecode.au/battles/1249308) | STAR / Maze | elimination | r133 W | 43→0 / 6 | 2 | 132 | 是 |
| [M1249309](https://game.battlecode.au/battles/1249309) | STAR / Portals | queen | 活，L3 | 3→3 / 16 | 0 | 218 | 是 |
| [M1249310](https://game.battlecode.au/battles/1249310) | STAR / Prisoners Dilemma | queen | 活，L17 | 17→17 / 18 | 0 | 452 | 是 |
| [M1249311](https://game.battlecode.au/battles/1249311) | STAR / Queen Of Spades | elimination | r65 H enemy | 20→0 / 12 | 3 | 4 | 是 |
| [M1249312](https://game.battlecode.au/battles/1249312) | STAR / Schooltime | longest | 活，L3 | 15→3 / 18 | 3 | 203 | 是 |
| [M1249313](https://game.battlecode.au/battles/1249313) | STAR / Slithery Fight | elimination | r126 H enemy | 25→0 / 6 | 5 | 125 | 是 |
| [M1249315](https://game.battlecode.au/battles/1249315) | STAR / Tower Defense | elimination | r278 H enemy | 29→0 / 4 | 3 | 216 | 是 |
| [M1249317](https://game.battlecode.au/battles/1249317) | STAR / Trophy | elimination | r69 H enemy | 25→0 / 3 | 3 | 66 | 是 |

## 解释边界

这是三个对手、每队一次全17地图系列；系列内相关，51局不能当作51个独立成熟对手。平台种子与先后手并非受控配对；与v14发现100场或本地弱基准的胜率不能直接比较来归因改进。Unranked结果不产生可报告的earned Elo升级；初始提交评分也不是提升。

Queen保命、资源兑现和消灭失败都需解释，不能用单一Longest峰值或曾领先掩盖正式终局。具体根本因果需已执行动作、长度账与场景验证；当前清单提供直接规则和观测，策略推断保持假说。没有取得的UI/预算/对手版本字段保持未知。

原始下载仅按明确ID从给定目录安全读取，原始回放与逐轮大型缓存留在忽略目录，不入Git。清单无源码内容、token、cookie、认证头或私密下载参数。

## 复现（仅离线解码）

```powershell
.venv\Scripts\python.exe tools\audit_online_panel.py --manifest test-results\generalist-v3-online51-selection.json --download-dir '<下载目录>' --ui-dir test-results\online51-ui --docs-out docs
.venv\Scripts\python.exe -m unittest tests.audit_online_panel_test
```

## 完成后决策记录

根代理已由可见UI核验回退Active平台v14／Guard v66，恢复显示旧提交原有1532分；这不是本轮earned评分提高。手动Unranked不计rating。上传期间另5场自动比赛只有平台总计56场16W40L减本组51场13W38L的表差3W2L，尚未逐场raw核验，单列未知，不混入本组。回退观察存于本机`test-results/generalist-v3-restored-v14-ui.txt`及对应截图；本组结果未支持长期强度采用。

线上51场边界/实际证据集成与原有相关检查合36项通过。离线证据导入与重建命令不启动比赛或执行下载源码；本轮另实际运行312场独立外部WASM比赛和本组51场手动线上比赛，阶段与源码分开报告。
