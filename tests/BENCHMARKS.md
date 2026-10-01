# v2 / v3 验证记录（2026-10-01）

全部对战使用 unswbc 1.2.2 官方沙箱，未修改规则。每个地图、种子组合交换双方位置。
结果中的胜负均从候选版本角度计数。每组源码 SHA-256 和逐局输出保存在对应 summary.json / log。

| 候选 | 对手 | 测试集 | 胜 / 负 / 平 | 候选最高 points |
| --- | --- | --- | --- | --- |
| v2 | v1 | 6 张地图 × seed 17、29 × 双方 | 13 / 7 / 4 | 5.8M |
| v2 | v1 | 新增 autarky、Colosseum × seed 101、202 × 双方 | 3 / 5 / 0 | 4.8M |
| v3 实验版 | v2 | 同一组 6 张地图 × seed 17、29 × 双方 | 8 / 12 / 4 | 6.3M |
| v2 | 官方 starter | 6 张地图 × seed 17 × 双方 | 10 / 2 / 0 | 4.6M |

6 张基础地图：arena、default、portals、big_empty、stronghold、dilemma。
最高 points 来自官方 CLI 四舍五入的摘要；每回合预算 100M。
共 68 局均无测试工具检测到的程序错误、无效行动或超预算错误；碰撞死亡仍会发生。

## 决策

- 本地主版本保留 v2；平台 Active 保持 v1，未做新的上传。
- v2 对 v1 合计 16 胜、12 负、4 平；在新增地图上反而 3 胜 5 负，不能宣称稳定全面提升。
- v2 对 starter 仍有 Arena B 方、Stronghold A 方失败。Arena B 方仍在 round 38 自碰死亡；短期搜索没有解决原来的全部缺陷。
- v3 的资源争夺折扣没有取得更好的头对头结果。保留实验代码，不因为版本号更高就自动升级。
- 下一步应检查自困前更早的决策和资源争夺回放，不能只凭这些小样本继续调权重。

## 模块与假设

1. **静态 BFS**：测当前视野内的空间和珍珠距离。
2. **v2 深度优先试走**：最多 8 步 / 每方向 384 节点，记录自身身体位置，先判碰撞再移动尾巴；吃现有珍珠时增长，同一颗不能重复吃。
3. **v3 敌方到达估计**：从可见敌方头部做多源 BFS。如果敌方普通路径不比我方长，珍珠奖励降为四分之一。

v2 不预测其他 dragon 移动、未来珍珠刷新、分裂、冲刺和传送门出口；未知区域及搜索截断作为不确定处理。
v3 只比较当前路径距离，不代表敌人真的会争抢，也未精确比较每条 dragon 的行动时序。这可能导致过于保守，但需要更具体的回放证据来验证原因。

## 场景检查

`strategy_test.cpp`：13 个场景，包括墙、身体、地图环绕、死胡同、传送门兜底、敌方头部威胁、尾巴先判碰撞、吃珍珠后不移尾、已吃珍珠不重复增长、未知身体处理、搜索截断。

`v3_experiment_test.cpp`：以上场景加敌方争夺和无敌人时的资源评分，共 15 个场景。

## 复现

```powershell
.\.venv\Scripts\python.exe tools/compare.py --candidate opponents/v2 --opponent opponents/v1 --name v2-v1
.\.venv\Scripts\python.exe tools/compare.py --candidate opponents/v2 --opponent opponents/v1 --maps autarky Colosseum --seeds 101 202 --name v2-v1-heldout
.\.venv\Scripts\python.exe tools/compare.py --candidate opponents/v3-experimental --opponent opponents/v2 --name v3-v2
.\.venv\Scripts\python.exe tools/compare.py --candidate opponents/v2 --opponent opponents/starter --seeds 17 --name v2-starter --replays
```
