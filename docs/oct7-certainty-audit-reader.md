# Certainty发现审计读者说明

Root于2026-10-07 06:06:58.971 UTC正式冻结certainty V1；源包`01621a5fcfc6e55493a2a8003b73eb317e3b6f6ce7a4ce32be8e920695ac0e7c`、WASM`22dfd8df1d90445d1ee9405fb62b8a0c9a495097859c5bb40ab9ba17e89a180f`与功能检查一致。完整主发现88由Root运行；本页只说明证据层级及预先固定的读法，未读取运行中结果或预报结论。

## 三种证明分别回答什么

| 证据 | 可支持 | 不能支持 |
| --- | --- | --- |
| 原allocation Trauma连续375帧，动作和indicator全部匹配、近死15帧body匹配 | r370现有unknown depth0与6选择合同，r371开始完全已知有限续路，r372无更高已知等级候选；末局合法split后Queen撞墙 | 竞价在某个最早回合造成必死；另一动作整场获胜；V5在这份allocation历史中必定执行同一动作 |
| 保持370帧实际allocation历史，仅r370启用新的生产helper | 同一个合法局部状态下排序确实把WSSS改为S，depth0改为6，二者均未知续路 | Queen后来被救活、资本或资源全程改善。没有提供r371之后的反事实输入 |
| 将完成的新V5与certainty各自对固定外部对手88场配对 | 正式评分及全程／共同前缀资源、死亡、覆盖变化；适格交集的机制方向 | 公开弱基准证明天梯强度、将双方不同运行资格混成同一分母、修改后继承新留出独立性 |

原[Trauma inspection proof](../tests/fixtures/oct7-allocation-trauma-inspection-proof.json)为已捕获诊断与输入的哈希绑定，未修改；不是新增比赛或把运行中结果当作验证。局部冷调用尝试中，先用V5替代allocation历史在r76有一次动作不一致的版本已弃用，不能借它声明原状态准确。正式局部证明用原allocation历史370个动作及完整indicator全部匹配，当前分工未激活；只隔离排序helper效应。[候选说明](generalist-certainty-v1.md)保留具体边界。

## 实现及冷启动风险

新helper只在已有contact、grade、birth三层相等的protected grade2内比较现有`future.depth`，然后用原utility。Queen、reserve和最后单位的保护条件沿用V5；普通worker、known horizon grade3及有限已知grade1/0的排序没有新优先层。

冷启动或新生长单位可能仅见部分自体。初始模拟以记忆链长和实际L是否相等决定`complete`；不完整时，`simulate_step`仍阻断当前可见的所有自身节，不会把未见尾巴补造出来。未解析门户、视野外或耗尽预算只保留已有grade2与实际搜索深度。未知动作仍只提交允许的那个未知步骤，pending body等待实际头与长度后校验。这些基础规则均未修改，继承功能检查通过；单帧或有限历史检查不构成所有实际冷启动路径的证明。

主要实验代价有两项。第一，深度从当前动作终点计数；同一路线的一步MOVE可能比多步MOVE保留更长的后续前缀，所以该规则可能减少免费步吞吐、延缓探索或选择重复路线。它约束当前承诺，不是在最大化“动作已走步数＋未来深度”。第二，现有utility beam与top8先筛候选，helper仅排序已评估集合，不能保证所有可能更深路线都被纳入。搜索耗尽取得的深度是下界证据，不能保证没有更好分支。完整面板应检查这些成本，不用某帧“选更深”替代全程保护结论。

## 结果分母与调用顺序

完成通知后使用冻结`oct7_compare_external.py`比较V5与certainty完整discovery88；严格`panel_trajectory`核对初始、全程身体/gross账、原始哈希及官方终局，再由冻结`oct7_scoring_context.py`解释消灭→Queen→Longest→Total。全部88正式结果、各自运行有效分母、双方有效交集和gross可证交集分列。主交集不因坏图或负资源而改样本；时长分层与同Q相对Longest仅作描述，不能成为新的采用分母。

Root记录首次`run`调用发生在freeze编译进程尚未结束时，缺少freeze而预检失败，0 job启动；随后确认正式freeze完成才开始主88。这是调用顺序失败，必须在最终限制中单列，不能记成88中的候选败局、runtime错误或被丢弃的比赛。冻结runner的`run_panel`先调用`candidate_record`，再构造pending和启动`run_game`，源码顺序与这一边界一致。本页没有尝试重启或补跑该调用。

重新核查V5八个、allocation九个、certainty九个冻结源文件、各自源快照与实际WASM字节均相等；冻结比较器、评分工具及原Trauma proof哈希保持。新只读检查记录`test-results/certainty-v1-reader-freeze-check.json`。这一核验没有启动引擎比赛或改变源／工具／proof；后续完整报告另外绑定它读取的实际完成范围。

## 06:24 UTC追加：分支聚合的语义限制

续路搜索的最大`depth`及随它更新的`next_food`属于一个被选中的深分支，但`outside`、`portal`、`exhausted`是所有搜索分支的OR。`depth6/outside1`只能读为“至少有一个已确认前缀6，以及某分支触及未知”，不能读为同一条路可先走6步再进入未知。新helper只给这个候选级最大前缀排序，不保证未知出口可接到深前缀，也不能把budget耗尽推断为安全或不可达。

隔离的生产函数构造已证实这个区别：一支已知有限6步、另一支立即未知0步，结果仍为`depth6/outside1`。`tests/certainty_branch_semantics_test.cpp`官方PASS，stage`bf19c5477d24451938f440a8`；0matches，原proof未修改。Trauma r370的同状态helper选择由WSSS→S可以保留，但S深分支通向未知的相连证书尚未知，不能从aggregate flags补造出来。

主88已完整核验，正式86W2L；有效／gross配对47，0strict失败。具体发现、所有47评分资产与正式axis语境由[完整发现报告](oct7-certainty-discovery-findings.md)另外记录。本页开头和三层证明表描述的是冻结时的读法；这一追加区分后续已完成范围，不把功能检查升级为全场保护或天梯强度通过。
