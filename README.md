# UNSW Battlecode 2026 — Queen 分工与交付实验

我们在 `main` 分支工作。主程序用 C++20；Python 用来运行官方工具和批量测试。

## 当前线上版：v27 传送门侦察修复（平台编号 v8）

2026-10-02 22:27（北京时间）上传并激活，submission **15014**。
`bot/` 与 `opponents/v27-portal-scout/` 内容一致。上传包为本地 `dist/v27-portal-scout.zip`。
源码 SHA256：`89d7f26ba0123eca19938b39869703edd13fa6363d43b295ee7e8fbcab131f68`。
官方本地测试引擎升级为 **unswbc 1.2.7**，当前地图在 `maps/current/`。

### 先理解四个决策部分

1. **去哪里：食物目标 + BFS。** 每条龙记住自己见过的地图。给珍珠、附近资源密度和未知边界评分，再用 BFS 找路线；珍珠记忆会过期。不是全图透视，也没有队友共享地图。
2. **怎么走：身体模拟 + 短期 DFS。** 枚举当前免费步数内的路线，模拟身体和增长，检查后续退路，再比较吃食、距离、危险、绕圈和空间。工兵最多规划四步；Queen 保留更保守的生存逻辑。
3. **何时扩张：早期短工兵繁殖。** 普通工兵前180回合长度4即可尝试对半分裂，之后门槛7；还要求头尾安全、冷却和数量条件。后期减少常规分裂，保留长身体。Queen 不跟着无条件分裂。
4. **何时冒险：有条件的工兵交换与探门。** 至少有四条己方单位时，工兵才考虑可确认路径上的敌方 Queen；很短工兵也可换掉明显更长的敌龙。已知传送门出口虽不在当前视野，长度不超过6的工兵可沿正确目标路线穿门；Queen 和长工兵不使用这个探门分支。

### 修复了什么，有多少证据

- 原来 BFS 能算出穿门路线，行动模拟却因出口不在当前视野而拒绝执行，导致门口折返。
- 保存的 Queen of Spades 开局中，前18次决策不变；第18回合原本向东折返，修复后向西穿门。完整引擎运行中，初始工兵第一次分裂从第35回合提前到第19回合。
- v17 对 v13 两批本地对照共 **25胜11负**。
- v27 对 v17 两批、换边、不同地图/种子的本地对照共 **15胜13负**，最大实测单回合53.6M points；优势很小，不能宣称全面更强。
- 线上从本轮开始约1233，到 v17 结束确认1449，v27 最后确认 **1490（35局15胜20负）**。本轮未达到1500目标；手动请求的30局为13胜17负，另5局来自平台其他排位对战。最终结果见 `tests/fixtures/iteration-2026-10-02.json`。随机地图和对手不同，线上胜率不是严格控制实验。

### 阅读入口和复现

- `bot/main.cpp`：读局面、更新记忆、选行动、输出。
- `bot/forage.hpp`：当前工兵目标、路径评分、分裂与战术。
- `bot/navigation.hpp`：已知地图与传送门连接。
- `bot/strategy.hpp`：身体模拟、Queen 生存与兜底。
- `tests/forage_test.cpp`、`tests/portal_regression.py`：当前策略与已记录的传送门回归。
- `tests/threat_model_test.cpp`：未上线 v23 的威胁模型实验，明确引用其快照，不代表当前策略。

```powershell
g++ -std=c++20 -O2 tests/forage_test.cpp -o tests/forage_test.exe
.\tests\forage_test.exe
.\.venv\Scripts\python.exe tests/portal_regression.py --compiler g++
.\.venv\Scripts\python.exe tools/compare.py --candidate bot --opponent opponents/v17-worker-trades --maps default queen_of_spades maze portals islands devil --seeds 3433 --name portal-recheck
```

局限：没有完整对手搜索或 Minimax；未见过的地图和传送门出口仍有风险。当前敌头威胁近似遗漏部分较早行动的敌人；修正后的实验版在部分测试中损失增长，未直接替换线上版。声呐协作、主动喂食和 Queen 早育均未纳入最终策略。

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
