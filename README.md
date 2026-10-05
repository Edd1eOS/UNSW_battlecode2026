# UNSW Battlecode 2026 — 资源争夺与安全扩张

在 `main` 分支工作。主程序为 C++20，Python 负责官方引擎批量对照。

## 10月5日：分段诊断与反制实验

21:45核实线上 **v66、1557分、144名**，本轮没有上传或发起排位。
主要瓶颈是接触消耗与资源集中：弱图Queen频繁死于头碰撞，数量和峰值长度未稳定转为终局计分。

已写出可达目标选择、资源竞争偏好和后行动头部出口比较，完整方案保存在 `opponents/counterplay-prototype/`。
冻结组合32场对v66 **14–18**，Queen终局存活 **7对9**，暂不采用；含局部修复的当前完整原型另外16场 **8–8**。
本地主线仅为v66加“传送门侦察拒绝记忆中自身占据出口”，源码哈希
`7210b8d11bf7bbc08cdeaa7817b3d8c69549787dca24a80f010cbb1f87951337`。
单独修复16场 **7–9**，只证明固定错误已修复，未证明强度提升；**线上仍是原v66**。

对手行为分类、条件克制链、源码与结果对应关系见 [反制报告](tests/COUNTERPLAY.md)，
136场逐局数据见 [本轮记录](tests/fixtures/counterplay-2026-10-05.json)。
没有完整对手分类器或主动喂Queen。下文各轮数据为历史记录，不代表当前新增或上线功能。

## 10月3日第三轮记录（19:05–21:05）

目标1800，起点1661。最终保留 **v66 / 平台v14 / submission15719，1588分**（21:01核实100局48胜52负）。本轮净变化 **−73**，目标未达到。
本轮最高观察到1740（v99），之后跨对手复测回落；恢复提交已有积分不算赢回的分数。
当轮结束时 `bot/` 与冻结 v66 字节一致，哈希 `42162e3c924cb13407aa7810c8f8d1fbe7f9a06ae77514ef47804bda2c4a4f61`。
逐局地图、种子、源码哈希、Queen存活/增长、长龙死亡和线上编号见 [第三轮记录](tests/fixtures/iteration-2026-10-03-round3.json)。

### 本轮已确认的结论

- **Queen并非每局必死，但死亡率仍高。** 对上一轮110局候选v66的审计，24局Queen活到终局、86局死亡；62次死于头碰撞。这是本地样本，不能当作线上死亡率。
- **长龙长过，不等于最后留下。** v99本地Schooltime有工兵观察到108节，386回合头碰撞死亡，终局最长龙19对38。峰值包含初始/分裂继承长度，不代表独立吃了108颗珍珠。
- **只保护长龙不分裂不足以补Queen。** v101本地对v66为15–9，压力对手8–0；上线26局12–14、1579，已回切。Dilemma输在Queen6对30，而非工兵长度。
- **Queen局部活动范围也未证明线上稳定。** v99从继承1639到1740（pizza4–1、Shannon5–0），再对BambooCode0–5、code matters1–4、Quaker1–4，结束1594。确认排位25局11–14；总35局17–18还包含Atlas非排位10局6–4。
- **空圈保命会牺牲增长。** v106两种子对v66合计28–29–1，Queen存活22/58对12/58；其中独立17图为14–19–1。能留下更多短Queen，但对手Queen也活着时会输长度，暂未上线。

实验编号是冻结算法快照，不是一次编辑一次上线。不同对手、地图、种子的胜率不能直接拼成稳定强度；当前规则先比较Queen长度，双方Queen死亡时才更多依靠最长龙。

### 本轮实验进展

| 快照 | 主要假设 | 对v66结果 | 采用情况 |
|---|---|---:|---|
| v97 | 预留更远的Queen威胁缓冲 | 13–11 | 对v35退化，未采用 |
| v98 | 长工兵提前转采集，降低分裂 | 7–17 | 扩张不足，未采用 |
| v99 | Queen以局部区域为偏好，见敌解除 | 12–12 | 上线复测后回切 |
| v100 | 修复首批工兵保长度被上层分裂绕过 | 12–12 | 无明确收益 |
| v101 | 10节工兵停止普通扩张分裂 | 15–9 | 上线复测后回切 |
| v102 | Queen与未知视野边界保留间距 | 12–12 | 无明确收益 |
| v103 | 先比较低即时威胁，再比较静态续路 | 12–12 | 局面回归改善，整体无收益 |
| v104 | 局部Queen与长工兵保护组合 | 10–14 | 未采用 |
| v105 | 可见Queen附近食物优先留给Queen | 14–10 | 地图集有差异；压力5–3，未采用 |
| v106 | 全身/全环可见的循环，逐回合重验 | 28–29–1 | 生存上升，增长下降，未采用 |
| v107 | Queen避开全部已建模敌头冲刺可达格 | 11–13 | 未采用 |
| v108 | 采集龙无低威胁免费路线时付费逃生 | 对v99为3–5 | 最长龙中位数13对19，未采用 |
| v109 | 扩大增长循环、可见刷新偏好与友军首格检查 | 13–11 | Queen8/24对6/24；压力5–3，未采用 |

本轮完成 **13个冻结实验、2个上线试验、28组532场**官方引擎对照，0运行错误，实验最高68.4M points。保留主线v66的7项核心/地形/付费逃生/传送门检查全部通过。

收尾v66对Bamboo为2–3（本组−3），同期Check Raise为0–5（−21）、Deep Sea Dragons为1–4（−27）；最新1588。两个失败上线版本均已回切，尚无可靠的新主线。

新增遥测记录Queen观察到的毛增长、请求的付费步数、工兵观察峰值及死亡轮/原因。付费请求可能在死亡中途未全部执行；未观察到下一回合时，最后一步增长可能没有计入峰值。
[官方评分规则](https://game.battlecode.au/docs/elo)说明每个源码提交独立计分，分数包含各地图偏移；新提交继承当前分数但不确定性较大，旧提交激活则恢复自己的分数。

当轮没有启用主动喂Queen、共享食物协议，也没有合入v95的隐藏己身传送门修复。

公开策略阅读仅作设计参考：[the-loong-game的移动安全分层](https://github.com/overyonder/the-loong-game/blob/main/examples/repertoire/games/loong/movement.nim)。没有取得线上对手私有源码，不能声称复原了对方算法。

## 上一轮记录：1850±50目标（16:13–18:13）

本轮时间：2026-10-03 北京时间 **16:13–18:13**；目标 **1850±50**，开始 **1588**。
最终保留 **v66 / 平台 v14 / submission 15719**；北京时间18:10核实 **1641**，65局34胜31负。
本轮 **1588 → 1641（+53）**，最高观察到 **1679**，未达到1800–1900目标。评分会继续随自动对局变化。
回切 v80 → v66 时从1582恢复1666，是恢复该提交已有积分，不是新增胜场。
当轮 `bot/` 与 `opponents/v66-queen-threat-buffer/` 字节一致，源码哈希为 `42162e3c924cb13407aa7810c8f8d1fbe7f9a06ae77514ef47804bda2c4a4f61`。

完整逐局数据、版本哈希、地图、种子及线上比赛链接编号见 [本轮记录](tests/fixtures/iteration-2026-10-03-round2.json)。
上一轮1700目标未达到：1493 → 1588，最高1642，最终保留v35；见 [上一轮记录](tests/fixtures/iteration-2026-10-03.json)。

## 当前决策逻辑

1. **找食物：地图记忆 + BFS。** 在已见地形中比较可达珍珠、资源密度和探索边界，再逐回合重新规划；没有全图透视。
2. **避免堵死：地形末端检查 + 身体模拟。** 从已知地形中剥离封闭末端分支，不为了珍珠继续深入；未知区域和未解析传送门保留不确定性。动作模拟包括吃食增长和移动身体，Queen看8步、工兵看6步，并限制搜索节点。
3. **Queen 保长度与逃生。** 主动找食物，更重视敌头可达范围。必要时支付长度额外走最多两步；模拟与身体记忆同时扣除成本。仍不能保证动态对手下绝对安全。
4. **扩张与育长。** 普通工兵优先繁殖；达到一定轮数和数量后，一部分转为保留长度的采集角色，队伍衰退时恢复扩张。紧急分裂仍作为逃生手段。

线上当前**没有启用共享食物线索或主动交付**。这些系统虽已实现并有局部收货记录，整体收益仍不足以替换主线。

### 为什么还没有达到1800

安全搜索回答“这一步之后还能不能走”，资源策略回答“这条龙最终能不能长大”。本轮改善了前者，但后者仍弱：Queen与采集龙没有稳定的资源供给，普通工兵大量繁殖后也可能被对手逐步消耗。
例如线上 Islands 951910，v95没有自撞，但Queen在119回合死亡；最后本方3条龙、总长度10，对手42条、总长度348。不能仅凭自撞减少就认定整体变强。

下一轮应将资源集中作为独立假设验证：记录每次交付的实际收货、Queen/采集龙增长、牺牲掉的采集能力，并与不交付版本在相同地图、种子和双方位置比较。回放中的死亡和声呐数量本身不能证明对手的具体协调协议。
截至60局的v66地图样本：Tower Defense为6–0，Maze为1–4，Islands为0–3，Schooltime为3–4。每张地图样本量有限，不能把单图评分当作已经稳定达到该分段；逐图记录保存在本轮JSON中。

## 本轮关键证据

- v64：手动排位对 Shannon 2–3、code matters 2–3、Quaker Qubits 3–2；对1863分SilverSamurai的Maze/Schooltime/weakhold非排位0–3。
- v66：首轮手动排位对 Shannon 2–3、code matters 3–2、Quaker Qubits 4–1、BambooCode 4–1，达到1666。统计还包含自动或其他队发起的比赛，不能只报告手动胜率。
- v66收尾复测：BambooCode 3–2、Quaker 3–2、1844分Lozer 1–4、1722分Shannon 2–3。最高观察到1679分；目标1800–1900未达到。
- v80：修复已知传送门出口撞到自身隐藏身体。真实观察回归中，旧版第107回合输出致死回门动作，修复版拒绝该动作。相同Portals种子6331、双方换边两局，非计划自撞61 → 2；独立全地图对v35为22–12。
- v80上线后25局9胜16负、1582，已回切。正确修复局部错误不等于已证明整版在线更强；后续以更小范围补丁继续验证。
- v95将修复缩小到侦察传送门分支，42局本地对旧版/压力对手为26–16；另对v66的16局传送门地图为7–9。线上15局6–9，1659 → 1601，已恢复v66的1664分。**因此当前线上仍未采用该传送门修复**，复现用例与修复快照保留，不能把实验修复写成线上已解决。
- v96仅在缺乏低威胁免费路线或能获得更多净长度时允许Queen付费移动。专项检查通过，对v95为8–8、对v66为9–7、压力对手7–1；未采用。
- `tests/fixtures/portal-self-body-round107.json` 保存真实观察前缀；它验证固定局面的选择，不冒充整场反事实胜负。
- Atlas的weakhold回放945347确实出现短龙死亡后Queen吃掉其珍珠；SilverSamurai/Lozer也有大量短龙周转和长存活者，但没有取得对方私有代码，不能声称完整复原了策略。

## 实验与验证

`opponents/v60-*` 起的目录是冻结实验快照，不代表已经上线。终止的编译/算法草稿保留在忽略目录 `test-results/`，不计入完成比赛数。
主要实验包括资源回访、目标停滞切换、Queen威胁梯度、工兵冲刺、采集角色时机、末期留长、尾部连通性、声呐食物提示、收货确认和长身体交付。

官方本地引擎为 **unswbc 1.2.7**、地图为 `maps/current/`。此前核对PyPI 1.2.9，包内引擎和地图与1.2.7一致。
本轮完成 **58组、1054场**官方引擎对照，记录中没有运行错误。另有17项核心/实验回归，收尾对当前v66重新运行7项核心、地形与逃生检查，全部通过；这些检查不等于保证比赛不死亡。当前v66的已测最高计算消耗为66.1M points，低于100M预算。
源码哈希包含所有 `.cpp/.hpp/.toml` 文件名和原始字节，编译缓存与头文件一起失效；`.gitattributes` 保留提交包字节。

```powershell
.\.venv\Scripts\python.exe tools/compare.py --candidate bot --opponent opponents/v35-colony-economy --maps default devil portals maze --seeds 6373 --name local-check
.\.venv\Scripts\python.exe tools/collect_benchmarks.py --record tests/fixtures/iteration-2026-10-03-round2.json --prefix r2-
.\.venv\Scripts\python.exe tests/portal_regression.py --compiler g++
g++ -std=c++20 -O2 -DCURRENT_BOT tests/terrain_exit_test.cpp -o test-results/terrain-current.exe
.\test-results\terrain-current.exe
g++ -std=c++20 -O2 -DCURRENT_BOT tests/paid_escape_test.cpp -o test-results/escape-current.exe
.\test-results\escape-current.exe
```

核心文件：`bot/main.cpp` 是回合入口，`forage.hpp` 选择目标和行动，`strategy.hpp` 模拟身体，`navigation.hpp` 保存观察和传送门配对，`terrain.hpp` 检查已知末端分支。
回归测试明确区分当前主线与实验快照；例如交付、声呐、末期育长的测试通过，不表示这些功能已经合入线上版。

## 历史实验：v5 协作交付（未采用）

设计见 [COOPERATION_V5.md](tests/COOPERATION_V5.md)。官方引擎曾验证长度4工兵牺牲，Queen 收到2颗珍珠，从9增长至11；普通地图未观察到有效触发或胜率收益，因此当前主程序不启用此系统。源码仍保留以便后续研究。

## v4 Queen 实验版说明

`opponents/v4/` 按 2026-10-01 Queen 更新修改，使用 `unswbc==1.2.3` 测试。
这版于2026-10-02上传过比赛平台，随后被更强实验替换。旧 Sprint 版已经推送 GitHub：提交 `4884d21`，标签
[`sprint-2026-v3`](https://github.com/Edd1eOS/UNSW_battlecode2026/tree/sprint-2026-v3)。
`opponents/v3` 保留原版，不能拿旧规则的胜率直接比较新规则。

500 回合后先比较 ID 0/1 的 Queen 长度（死亡算 0），再比较最长龙、总长度。
普通龙吃到的珍珠不会自动加到 Queen 身上。详见 [官方公告](https://game.battlecode.au/updates)。

### 决策分成四层

1. **分工**：Queen 负责活着增长；早期有余量且队中尚无工兵时派出长度 3 的工兵，
   自己至少留 8 节。工兵长度至少 8、头尾有空间时主动分裂。
   第一批工兵繁殖一次后保留自身长度，作为第二判定的后备。
   普通扩张有冷却、数量和阶段限制；应急救援不受这些软限制约束。
2. **导航**：`bot/navigation.hpp` 保存亲眼见过的地形及传送门配对，BFS 搜已发现的地图，
   每个候选至多展开 2048 格。未见过的地图仍未知；当前视野仍是 7×7。
   旧珍珠最多信任 12 回合且降低权重；旧单位位置不保存成永久障碍。
3. **保命**：当前可见范围的 BFS 估算空间，带自身身体移动的 DFS 最多试走 8 步。
   每回合重新规划。Queen 不随意向未知门冒险；工兵在无食物绕圈时可以探门。
   已知门按真实出口检查，不能把入口旁的格子当出口。
4. **免费多步**：新规则免费步数为 `ceil(回合开始长度 / 4)`。
   当前最多规划三步，只在身体完整、每步可见且额外吃到珍珠、末端有短期续路时使用；
   同时记住中间身体变化，不能只记最终头位置。

Queen 被堵时通常只切出最小子体来等待；若能严格确认四周全是固定墙或自己的脖子，
合法分裂无法让 Queen 脱身，此时保留长子体争取第二判定。
`Dilemma` 的初始 Queen 通道实际触发过这种情况。

### 如何读代码和验证

- 主流程：`bot/main.cpp`。
- 地图记忆与 BFS：`bot/navigation.hpp` 中 `observe_map`、`destination`、`route_value`。
- 分工和分裂：`bot/strategy.hpp` 中 `choose_action`。
- 身体模拟与免费多步：`simulate_step`、`search_survival`、`plan_moves`。
- 新规则检查：`tests/queen_test.cpp`；基础场景：`tests/strategy_test.cpp`。
- 新规则实测：`tests/QUEEN_V4.md`；完整日志和回放保存在本地 `test-results/`。

```powershell
g++ -std=c++20 -O2 -Wall -Wextra -pedantic tests/queen_test.cpp -o tests/queen_test.exe
.\tests\queen_test.exe
.\.venv\Scripts\python.exe tools/compare.py --candidate opponents/v4 --opponent opponents/v3 --maps default portals dilemma queen_of_spades slithery_fight --seeds 17 29 --name queen-v4-check --replays
```

局限：尚无声呐共享和工兵送资源方案；每条子龙的地图记忆独立。
敌人/队友威胁只覆盖后行动头部的一步移动，未完整建模冲刺攻击。
其他身体仍按当前占位近似；未来刷新、未知出口和对手变化无法保证安全。
更多龙和更多总长度不等于必胜，不能宣称已经比线上强队更强。

## 以下为 Sprint v1–v3 的历史说明

Sprint 期间 `bot/` 是 v3 自适应探索版。用户手动上传后，平台激活过 `Refined`（提交 13667，平台编号 v3）；v2.2 未单独上传。
v3 快照在 `opponents/v3`，上传包 `dist/sprint-v3.zip`。旧的 `v3-experimental` 是不同的已弃用方案，不要混用。
`opponents/v1` 和 `opponents/v2` 保留版本快照，`opponents/v3-experimental` 是尚未通过升级标准的实验版。
`opponents/v2.1` 是当前稳健基线快照，`opponents/v2-safety-only` 保存只改退路优先级的中间版本以便比较。
v2/v3 历史对比见 `tests/BENCHMARKS.md`，v2.1 的真实失败局面分析和验证见 `tests/STABILITY.md`。

## 先读这两个文件

- `bot/main.cpp`：每回合读取局面、选择方向、输出行动。
- `bot/strategy.hpp`：真正的策略，有中文注释。

`bot/helper.hpp` 来自 unswbc 1.2.2 官方协议库；协议接口仍可用于 1.2.3，已更正新版免费步数注释。
`opponents/starter` 保留未修改的官方随机避障 bot，作为测试对手。

## 一个回合怎样决定

1. 枚举北、东、南、西。排除经过海带边或撞上身体的普通移动，自己的尾巴也不能撞。
2. 假设走到候选位置，进行 BFS（广度优先搜索）：先看距离 0，再看距离 1、2……
3. 在当前 7×7 视野中统计可达空格、最近珍珠距离、下一步出口和通向未知区域的距离。
4. 给空间不足、死胡同和敌方头部威胁扣分；给附近珍珠加分；重复走最近走过的位置扣分。
5. v2 再向前试走最多 8 步，每个候选方向最多展开 384 个搜索节点。
   模拟自己的身体移动和已存在珍珠带来的增长；在简化模型里找不到退路的方向重罚。
   遇到未知格子或搜索预算耗尽，标记为不确定，不宣称确定安全或必死。
6. v2.1 先比较是否找到完整短期续路、仅找到未知续路、还是模型内无续路；同类再比较深度和评分。
7. 没有普通安全路时先尝试合法应急分裂；不能分裂时才使用原来的传送门/移动兜底。
   v2.2 在此处改为母体留 2 节、其余交给从旧尾巴反向出发的子体，争取保存一条长龙。
8. v3 无食物时按长期访问次数减少绕圈；反复绕圈时，允许经过至少三步探索后进入未知区域的候选竞争。
   这不代表未知路线已验证安全。头部仅剩一步死路、尾部有空间时，可以提前反向救援。
   尾部信息完整且空间明显更好时，也允许通过反向分裂跳出无食物循环；不盲目扩大龙数量。

例如东边有一颗珍珠，但进去以后没有出口；北边没有立刻能吃的珍珠，却有大片空间。
死胡同的惩罚大于这颗珍珠的奖励，所以先向北。权重是经验值，不是安全保证。

## 从 C 迁移到 C++

| 代码 | 可以怎样理解 |
| --- | --- |
| `struct Evaluation` | 和 C 的结构体一样，把几个有关的数放在一起 |
| `const Controller& ct` | 只读引用；使用原对象而不复制，函数里像普通对象一样用 |
| `const auto* tile` | 编译器推断指针类型；可以先当作 `const Tile*` |
| `std::vector<int>` | 自动管理内存、长度可变的整数数组 |
| `std::queue` | 先进先出队列；BFS 用它保证近的格子先检查 |
| `std::deque` | 两端都方便增删的序列；保存最近 24 个位置 |
| `nullptr` | C++ 的空指针，类似 C 中表示空指针的 `NULL` |

第一遍只需要理解 `main.cpp` 的循环和 `choose_move()`，随后再读 `evaluate()`。

v2 的关键区别：BFS 统计当前的空间；`simulate_step()` 更新假想身体；
`search_survival()` 用深度优先搜索检查是否有一条短期可行路线。
只输出第一步，下一回合用最新信息重算，不盲目执行整个预测路线。

## 在 Windows 运行

环境已在本目录的 `.venv` 安装，版本固定在 `requirements.txt`。
新机器先执行：

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

打一场使用比赛计算预算的对战：

```powershell
.\.venv\Scripts\unswbc.exe run maps/arena.map bot opponents/starter --sandbox --seed 17
```

批量跑 6 张地图、交换双方位置，共 12 场：

```powershell
.\.venv\Scripts\python.exe tools/smoke.py
```

日志和汇总在 `test-results/`。普通比赛生成的回放在 `replays/`，可以用官方网页 visualiser 打开。

新版对旧版的沙箱比较（6 张地图、两个种子、双方换边）：

```powershell
.\.venv\Scripts\python.exe tools/compare.py --candidate bot --opponent opponents/v1 --name v2-v1
```

这个工具会对包括头文件在内的源码计算哈希、构建一次后重复对战，并保存版本哈希。
unswbc 1.2.2 的编译缓存只计算源文件；改过头文件后优先使用此工具避免旧缓存。
`--maps`、`--seeds` 可指定测试集，`--replays` 保存回放。

运行规则检查：

```powershell
g++ -std=c++20 -O2 -Wall -Wextra -pedantic tests/strategy_test.cpp -o tests/strategy_test.exe
.\tests\strategy_test.exe
```

## 第一版的边界

2026-09-30 验证：7 个策略场景检查通过。官方沙箱中，6 张地图各交换位置一次、
固定 seed 17，对未修改的 starter 共 12 局，10 胜 2 负，没有无效行动错误。
失败为 Arena 的 B 方、Stronghold 的 A 方，均出现自困后撞身体。
我们的回合消耗在该测试中最高约 4.1M points（预算 100M 的 4.1%）。
这组地图和种子数量有限，结果不代表对真实参赛队伍的胜率。

以上是 v1 的历史结果。v2 增加了自身身体模拟，完整身体尚未知时保守保留未知身体障碍。
基础 BFS 仍是静态空间估计；短期模拟只处理当前已有珍珠，不预测未来珍珠刷新。
其他 dragon 暂时当作静态障碍，因此搜索结果不是对真实未来的保证。
敌人威胁只估计后行动敌人的普通一步碰撞，不覆盖冲刺或传送门攻击。
有被困时的应急分裂，没有主动扩张、冲刺、声呐协作和可靠的传送门出口定位。
对 starter 的结果不能当作排行榜胜率。Sprint 上传版为 `Refined`（v3），首次五图真人不计分赛 1 胜 4 负；原版现已归档到远程标签。

## 参考规则

- https://game.battlecode.au/docs/quickstart
- https://game.battlecode.au/docs/movement
- https://game.battlecode.au/docs/vision
- https://game.battlecode.au/docs/kelp-and-portals
- https://game.battlecode.au/docs/timeouts

Sprint 截止：2026-10-01 09:00 AEST，即北京时间 07:00。以主办方最新公告为准。
