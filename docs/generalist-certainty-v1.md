# 现有不确定续路证据排序 V1

候选`opponents/generalist-certainty-v1`独立复制冻结V5。唯一政策变化发生在Queen、reserve或最后单位的两个grade2候选之间：contact、continuation grade、birth-contact三层完全相同时，先比较已有`future.depth`，更长者优先，深度相等再用原utility。原普通worker排序、完整已知grade3、有限已知grade1/0、候选枚举、beam、搜索预算、支付、食物奖励、地图与分裂策略均保留。没有合并allocation、投资、合作或探索模块。

## 范围与可证伪风险

`certainty.hpp`中的`comparable_unknown_depth`及`prefer_after_birth`被生产`choose`直接调用。grade2仍表示离开当前视野、未解析门户或预算耗尽之一；深度只是已经验证的续路长度，不证明跨过未知处后能生存，也不把搜索截断当不可达。grade1短有限路径仍保持原评分；这个候选不会自动修复所有已知死端、紧急分裂或友军堵路。更长的不确定续路可能牺牲当前食物或产生无效绕行，必须检查全场与共同前缀的Queen／Longest主评分资本、死亡及资源成本，不能只看wins或某帧深度增加。

方法在Root的[Oct7计划](oct7-hypothesis-validation-plan.md)追加H3预声明后实现。当前0候选比赛、0上传；功能正确不等于通过机制或强度采用门槛。后续若Root开启已声明外部发现面板，保持全部正式结果与各自eligible、有效配对交集分母，修改后不继承已见发现种子的独立性。

## 实际Trauma证据：不进行反事实续局

固定allocation发现集的SAS Trauma A实际回放SHA`9f29df6ed935051dd6bb2b520d9c8fb8da44c523f4253b69a97c3da94841ca99`。离线从初始身体与官方事件重建Queen id0每一回合的合法7×7观测，只把可见身体、边、珠和countdown放进协议；拒绝需要sonar/inbox重建的流。连续Controller、Memory和State推进375帧，原allocation完整动作375/375、indicator375/375都匹配；r360–374的完整记忆身体15/15与实际身体相等。原源码哈希全部保持冻结。这里的全图状态仅用于筛出合法输入与事后死亡核验，没有提供给策略。

| 实际输入回合 | 原选择与证据 | 全部生成候选中可证事实 |
| --- | --- | --- |
| r369 | NWWW，grade3、depth8 | 终点(12,8)的8步已知续路证书为(12,9)→(12,10)→(13,10)→(13,9)→(14,9)→(14,10)→(15,10)→(16,10)。是当前局部模型证书，不能保证下一轮仍选择该路 |
| r370 | WSSS，food2、grade2、depth0、outside1 | 全部10候选均grade2，没有被排序隐藏的grade3。S仍在被评估集合，food0、depth6、outside1；两个候选contact/birth/risk均相同。旧utility选即时食物更高的WSSS，深度较长的S未被beam丢弃 |
| r371 | SS，food2、grade1、depth2 | 仅S／SS／SSS／SSSE四个前向候选，深度3／2／1／0，均outside0、portal0、budget0。此时已可见有限尽头；没有已知8步或未知高等级替代 |
| r372 | SE，food2、grade0、depth0 | 只有S depth1与SE depth0，均grade0、完整body、contact0、birth0。不存在更高已知生存等级的候选被即时食物压过 |
| r373–374 | SPLIT29留Queen2；下一轮fallback N；死亡code W（撞墙） | SPLIT合法，父无首步确认出口；最后直接原因是Queen撞墙。Queen初始4+food27−转出29−死亡2=0，付费0。增长和Longest资本转移未保住主评分资产 |

上述原轨迹检视为两次独立官方WASM协议调用，stage`a0c86624cc01`、`0285dff61a45`；0引擎比赛。小证据记录[inspection proof](../tests/fixtures/oct7-allocation-trauma-inspection-proof.json) SHA`21c34375678abc1f59ab86816c590d3ce2f1f183d5f9b8a22080b2280188369d`。它是绑定执行与输入哈希的观测记录，不冒充新的回归用例或比赛胜率；连续合法输入及诊断stdout保存在ignored `test-results/inspect_allocation_trauma/`。

随后在新隔离诊断副本中保持实际allocation历史r0–369：370个动作与完整indicator全匹配，只在r370调用同一个新排序helper；此时`allocation_active=0`。局部选择由WSSS(depth0/outside1)变为S(depth6/outside1)。随后立即结束输入，没有r371以后帧，没有模拟或声称Queen获救。这个诊断隔离当前排序机制；真正候选复制V5、不继承allocation的历史政策。较早的V5历史替代尝试r76有一次动作不一致，明确弃用，未纳入证明。

该局部证据`test-results/certainty-v1-trauma-local-proof.json` SHA`1ad1f29e25eb540deba70b8c93b06426172d5120bd73cb4b1f877458dc8d2e28`，stage`e9562b56ac42`。新规则确实改变被识别的末级选择，但不知道不同完整对局会怎样；更早的竞价因果与总体拓扑风险没有被这个局部调用证明。

## 功能、协议与冻结绑定

官方metered生产协议检查全部31个场景、34帧通过，峰值8,414,677 points，0matches。这是既有协议／合法输出场景的实测，不是全局最坏预算上界。三个官方C++检查通过：

- `tests/certainty_physics_test.cpp`：protected unknown0 vs6、相等证据保留原score/strict tie、普通worker、known3、finite1/0、实际exhausted depth不虚构horizon；stage`e7200ace236d`。
- `tests/certainty_inherited_physics_test.cpp`：原V5身体/paid/tail、pending portal body、capital dominance、protected last survivor及新生旧颈回归；stage`a1b81b709351`。
- `tests/certainty_closed_route_test.cpp`：known8保持优先于known2死端，即使有可能出生头风险，原contact→grade→birth顺序保留；stage`d546d4458f89`。

相对V5仅`planner.hpp`与新增`certainty.hpp`不同，其余冻结源文件逐字相等。候选源包SHA256`01621a5fcfc6e55493a2a8003b73eb317e3b6f6ce7a4ce32be8e920695ac0e7c`，官方生产WASM`22dfd8df1d90445d1ee9405fb62b8a0c9a495097859c5bb40ab9ba17e89a180f`。完整源文件/检查哈希记录`test-results/certainty-v1-correctness.json` SHA`26dbc2d7bbc6b261b1470e6fe4a9539c178fafda74db3faa9794b01feb350a02`；Root的面板freeze另外记录正式开始时间与同字节核对。

重建和检查命令没有启动比赛、上传或执行对手源码。与旧V5、allocation及原审计proof互不修改。当前状态仅为功能READY，尚无采用依据。

## 06:24 UTC追加：深度语义与完整发现结果

`Future.depth`是该候选各已搜索分支中最大的已确认续路前缀；`outside`、`portal`、`exhausted`在分支间分别取OR。因此`depth6/outside1`不保证同一路线先走6步再到未知处，也可能是一支已知有限6步和另一支立即到未知处。helper比较的是候选级最大已确认前缀，未新增未知出口的路径证书。Trauma r370的0→6排序证明仍成立，但不能据此描述S有“走6步后才进入未知”的生存合同。r369明确列出的完整已知8步路线不受这项更正影响；尚未额外验证r370 S的深分支与未知出口是否相连。

新增隔离构造`tests/certainty_branch_semantics_test.cpp`直接调用冻结生产`continuation`，令一支有限6步、另一支立即视野外，实测返回`depth6/outside1/portal0/exhausted0`，末端有限支没有可走出口；官方C++检查PASS，stage`bf19c5477d24451938f440a8`。源码SHA`290cd394910f2565c04f4dd12f086433addaeb7dc55ee5e2895e8b812f0479b1`，stdout SHA`9d8cd1c9d47d4223bb03e8407c5f6613260fdf8c2c1cd8dd0105b375e4414aad`。这是冻结后的语义边界检查，0matches，原三项功能proof与候选源/WASM均不改写。

Root运行的主发现已完整88：正式86W2L，独立47有效45W2L、41对手无效；与V5的有效及gross交集均47。Queen终局存活25→28，但新增Colosseum B消灭败局、同Q达到Longest判定的10对相对长度margin均差−12.5，全局保护与资本代价仍混合。完整计分／资源／死亡报告见[Certainty发现结果](oct7-certainty-discovery-findings.md)。独立留出0、无候选线上强度确认；当前不支持采用，不因86W或Queen存活增加自动晋升。
