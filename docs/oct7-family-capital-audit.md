# Oct7 家族资本对齐与联合投资兑现审计

这份方法在投资v1的88场发现面板尚未完成时写入。它是[资源假说验证计划](oct7-hypothesis-validation-plan.md)的辅助账目，不改变主指标或独立强度分母。家族账可解释收入怎样变成计分资产，不能从一次分裂的后续收益证明“当时不分裂会更差”。

## 跨版本的对齐对象

两次外部比赛必须先由冻结比较器核验相同phase、对手、地图/引擎字节、种子、A/B侧和完整初始身体。相同初始`team/id/body`才是跨版本可对齐的founder。后续子体编号取决于全场出生顺序，不能以相同child ID配对两个版本。

每个初始龙自成一个家族，所有后继递归继承它的founder。家族互不重叠，所有活体及死亡体各归属一次；初始工龙不会被推测成Queen更早生出的子体。Queen家族总收入含其后继工龙收入，不等于Queen本体收珠，Queen个人账仍以主比较报告为准。

每次分裂另外核对实际身体：父体保留原前段，子体为原尾段反向；分裂前后合计长度不变。继承资本和历史peak不记作新收入。

## 逐轮守恒与阶段

对每个家族、每个完整轮末验证：

`当前活长度 = 初始资本 + 实际身体update净变化 − 死亡带走长度`。

全部家族求和后，Queen、Longest、total、活体数必须逐轮等于冻结`trajectory_metrics`重建；update和死亡累计必须等于冻结`panel_trajectory.executed_details`的轮末账。每个生命周期的终局长度、实际net update和父ID也再次核对。这里测量body变化，不另写一套由请求MOVE步数猜费用的算法。

整场家族food/paid只从冻结strict生命周期gross账聚合，且只有完整gross可证时提供。共同前缀、Queen状态阶段和分裂后cohort的gross不能从现有逐生命周期总数切分，保持unknown；净身体账、死亡成本和保有资本仍可证。

分阶段采用实际轮末Queen存活状态，转变轮包括在它结束时的状态阶段。双方转换时刻可能不同，按相同状态名称盲减两个不等长阶段不能成为因果证据；整场与双方较早终局的共同轮末仍是主比较。最长单位占总长比例及平方长度份额只描述集中度，不是新的加权评分，也不要求集中度越高越好。

## 每次分裂的后续父子cohort

cohort起点是分裂时的父体及该次新子体，纳入这两者之后产生的后继，排除父体在该次分裂之前产生的旧子系。这样其起始资本恰为本次分裂前父体长度，无额外继承收入。

预定两个观察终点：出生轮及下一轮均结束后的两轮窗口，以及该局实际终局。短局无法覆盖下一轮时明确标truncated，短期统计不将它冒充完整两轮。两个终点分别校验：

`cohort活资本 = 分裂前父体资本 + 分裂后实际net update − 分裂后死亡资本`。

这是实际父子合计兑现，不只看子体出生peak、子体数量或父体单独缩短。不同分裂的cohort常重叠，同一个收入可能出现在祖先与后代cohort中，所以这些cohort不可相加为全队收入，也不能把数百次cohort当独立随机样本。两个版本出生时刻和分裂数量不同，cohort分布是单侧描述，不能逐个child或排序序号硬配对。

若本次同一turn的bot indicator提供`joint_food_est`、`joint_paid_est`且`joint_complete=1`，另输出其预测净收入和实际两轮净update。它是已观察的bot自报预测，不是引擎资源、收入或保证；实际对手行动、刷新与后续父子策略可能改变。缺字段、不同turn旧indicator或不完整预测保持unknown。没有从预测倒填真实费用。

## 工具、测试与实际范围

新工具`tools/oct7_family_capital.py` SHA256 `28611740198b0827d887085042a0a7ff8cef7f5bb39da14de9c41084ccb1105e`。缓存绑定result与replay实际SHA、工具和三个冻结分析依赖、官方viewer包；读取缓存前仍核对raw字节。比较报告中的provenance必须与重新分析一致；改过result/raw或不同版本账本不能混用。

11项离线检查通过，包含真实Slithery官方回放逐轮／完整账集成、分裂转移、旧子系排除、后继纳入、窗口之后死亡、末轮截断、缺gross、预测与收入分离、初始founder对齐而不同child ID不对齐、非法身体分割、缓存字节变更。与原配对比较器12项合计23项PASS，约1.99秒，没有启动引擎。

工具以既有严格配对报告为输入，只为其中双方eligible的配对生成资本比较；其他正式结果留在主报告，本辅助报告亦保存其key/outcome/核验问题。单场失败保留，不中断后续也不换样本。输出保留输入报告的actual_scope和SHA，不能将部分比赛标成complete。

```powershell
.venv\Scripts\python.exe tools\oct7_family_capital.py --comparison '<既有严格配对报告.json>' --out '<忽略目录中的家族资本报告.json>' --cache test-results\oct7-family-audit-cache
.venv\Scripts\python.exe -m unittest tests.oct7_family_capital_test tests.oct7_compare_external_test
```

该命令只导入、重建与归属证据，不启动候选比赛、不上传、不执行下载的源码。投资发现结果完成后另写实际分母、源包/WASM与结论，本文不预报88场已经完成或机制已经改善。
