# UNSW Battlecode 2026 — 资源争夺与安全扩张

我们在 `main` 分支工作。主程序用 C++20；Python 用来运行官方工具和批量测试。

## 当前线上版：v35 资源优先（平台编号 v10）

2026-10-03 14:52（北京时间）上传，submission **15621**；15:48 验证后切回。
`bot/` 与 `opponents/v35-colony-economy/` 内容一致；上传包为本地 `dist/v35-colony-economy.zip`。
源码 SHA256：`ae3e00f65f366537d1cf40acc02e8d3a778f96e9644166c5b0eb007cbbc56ce4`。
官方本地引擎 **unswbc 1.2.7**，地图在 `maps/current/`。结束前核对 PyPI 1.2.9：包内仅版本号与回放插件变化，引擎和地图文件一致。
本轮两小时目标1700 **未达到**：开始1493，最高1642，最终观察 **1588**（+95）。保留 v35；截至结束，该提交79局41胜38负，包含4局非排位和5局官方测试队对战。完整证据见 [本轮记录](tests/fixtures/iteration-2026-10-03.json)。

### 四个决策部分

1. **找资源：记忆地图 + BFS。** 从自己见过的格子中选择珍珠和资源密集区，再计算路线。降低无目的探索的吸引力；长度3、差一颗珍珠就能分裂的工兵更重视吃食。没有全图透视或队友共享地图。
2. **走得安全：身体模拟 + 短期 DFS。** 工兵枚举最多四个免费步，检查身体增长和后续退路，再比较食物、距离、敌头、空间与绕圈。敌人的冲刺范围从可见身体估计，断链时保留不确定性。
3. **持续扩张：短工兵繁殖。** 前220回合或全队不足10条时，长度4即可尝试分裂；否则门槛7。仍检查头尾空间、合法性和阶段限制。Queen 保留基础生存逻辑，不采用 v55 的提前派工。
4. **按机会调整：侦察与交换。** 已知传送门出口在视野外时，短龙可以侦察穿门；明确可达时尝试换掉敌方 Queen，或以短龙换长敌龙。每回合根据新视野重算。

**没有启用自动喂养、共享地图或完整 Minimax。** 实验快照中的功能不等于线上功能。

### 实测依据

- v30 的本地优势没有完全迁移到线上：34局12胜22负，最后观察1448。
- v35 加强吃食与低数量重建；首次上线49局27胜22负、当时最高观察1635分（含4局非排位）。回切时平台显示1597；激活导致的分数变化不记为新赢来的分数；随后复测 Quaker Qubits 4胜1负，升到本轮峰值1642。
- v35 最后两组对 code matters 为1胜4负、对 Shannon 为0胜5负，说明跨对手稳定性仍不足，不能用1642峰值代替长期水平。
- v54 对 v35 本地36胜24负，但上线25局12胜13负、最后1587，未保留。
- v55 对 v35 两批共34胜26负，第二批单独16胜18负；上线10局2胜8负、最后1530，已撤下。
- 最后用新种子6023复测 v35 对 v27：21胜13负，最高4890万 points；本轮累计50组、908局本地对照，无超时或无效行动。
- 所有已完成的本地对照、源文件哈希、地图、种子和逐局结果保存在 [本轮记录](tests/fixtures/iteration-2026-10-03.json)。完整大日志留在忽略目录 `test-results/`。
- 当前资源决策和传送门场景有回归检查；未采用候选的 Queen 逃生与分裂出口测试明确引用各自快照。

### 阅读与复现

- `bot/main.cpp`：读取局面、更新记忆、选择行动、输出。
- `bot/forage.hpp`：目标 BFS、威胁估计、工兵行动与分裂。
- `bot/navigation.hpp`：地图记忆与传送门配对。
- `bot/strategy.hpp`：身体模拟、短期生存检查和兜底。
- `tests/queen_escape_test.cpp`：未采用 v54 的三面夹击与付费身体记忆回归，明确引用快照。
- `tests/split_exit_test.cpp`：未保留 v55 的出生出口检查，明确引用实验快照。

```powershell
g++ -std=c++20 -O2 tests/forage_test.cpp -o tests/forage_test.exe
.\tests\forage_test.exe
g++ -std=c++20 -O2 tests/queen_escape_test.cpp -o tests/queen_escape_test.exe
.\tests\queen_escape_test.exe
.\.venv\Scripts\python.exe tests/portal_regression.py --compiler g++
.\.venv\Scripts\python.exe tools/compare.py --candidate bot --opponent opponents/v27-portal-scout --maps default devil queen_of_spades trophy australia islands portals dilemma --seeds 5209 --name colony-recheck
```

`portal_regression.py` 默认检查当前策略在固定观察局面的穿门选择；`--historical` 保留 v27 的原始行动前缀一致性检查。改变寻食策略后不能继续声称旧前缀不变。

### 本轮未采用的方向

Queen 额外逃生、无限制未知门先锋、更多免费步、近距离喂养、资源目标认领、长期采集角色等保存为独立快照。部分只在某批测试中占优，部分几乎不触发；未经验证的改动没有直接合并。

### 剩余问题与下一步依据

- Islands 对官方测试队的回放 `944358`：两边 Queen 都死亡，最终最长14对17、总长度68对355；我们已经分裂280次，对手329次。因此不能再把所有败因归为“不分裂”。
- 同局我们113次撞 kelp、135次头碰头；对手分别0和149。需要从死亡前局面区分被堵死、未知出口和攻击路径问题，再针对原因修改，不能只增减一个总风险权重。
- 对 NUSW 的 Islands 回放 `941377`，对手有大量自撞并留下40长度长龙，可能涉及资源集中。但只凭回放不能认定其实现了喂养，更没有拿到其私有源码。
- v54/v55 的本地提升没有稳定迁移到线上。下一轮应保留强对手与不同地图的检验，再研究资源集中和地图特定困境；不能仅凭战胜旧版就发布。

上一轮 v27 的传送门修复和1490结束分数见 [10月2日记录](tests/fixtures/iteration-2026-10-02.json)。本轮开始时，v27 已经自动对战到1493。

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
