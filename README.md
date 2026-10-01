# UNSW Battlecode 2026 — 稳健增长 bot

我们在 `main` 分支工作。主程序用 C++20；Python 用来运行官方工具和批量测试。

当前本地 `bot/` 是 v3 自适应探索版。用户手动上传后，平台已激活 `Refined`（提交 13667，平台编号 v3）；v2.2 未单独上传。
v3 快照在 `opponents/v3`，上传包 `dist/sprint-v3.zip`。旧的 `v3-experimental` 是不同的已弃用方案，不要混用。
`opponents/v1` 和 `opponents/v2` 保留版本快照，`opponents/v3-experimental` 是尚未通过升级标准的实验版。
`opponents/v2.1` 是当前稳健基线快照，`opponents/v2-safety-only` 保存只改退路优先级的中间版本以便比较。
v2/v3 历史对比见 `tests/BENCHMARKS.md`，v2.1 的真实失败局面分析和验证见 `tests/STABILITY.md`。

## 先读这两个文件

- `bot/main.cpp`：每回合读取局面、选择方向、输出行动。
- `bot/strategy.hpp`：真正的策略，有中文注释。

`bot/helper.hpp` 是 unswbc 1.2.2 生成的官方协议库，暂时不需要逐行学习。
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
对 starter 的结果不能当作排行榜胜率。平台当前激活 `Refined`（v3），首次五图真人不计分赛 1 胜 4 负；未推送远程。

## 参考规则

- https://game.battlecode.au/docs/quickstart
- https://game.battlecode.au/docs/movement
- https://game.battlecode.au/docs/vision
- https://game.battlecode.au/docs/kelp-and-portals
- https://game.battlecode.au/docs/timeouts

Sprint 截止：2026-10-01 09:00 AEST，即北京时间 07:00。以主办方最新公告为准。
