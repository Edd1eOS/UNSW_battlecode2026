# Oct7 资源密度导航v1：完整发现集

两组各88场完整终局已到齐，严格报告生成于2026-10-07 04:55:41 UTC，`actual_scope=complete`。密度导航没有稳定增加整场资源吞吐：双方运行有效的44个配对中，整场净收入均差−23.91、共同前缀−18.93；终局保有总长均差−17.55。Queen存活23→26是正向观测，但它不能替代Queen长度、正式判定与资源账。当前不支持将该单独政策作为已通过采用的候选，保留为设计发现。

方法先声明于[本轮计划](oct7-hypothesis-validation-plan.md)。冻结v5与导航v1分别对相同外部对手、22张地图、种子`2026100701`及A/B側比赛，没有自家版本互战。仅替换资源导航不证明后果只发生在采集：它改变身体、后续控制及对手反应。以下差值均为导航减基线。

## 身份与不同分母

| 范围 | 冻结v5 | 资源密度导航v1 |
| --- | --- | --- |
| 全部正式88场 | 87W1L | 86W1L1D |
| 各自双方运行有效，独立分母 | 47：46W1L | 47：45W1L1D |
| 两臂有效交集，配对分母 | 44：43W1L | 44：42W1L1D |
| 交集Queen终局存活 | 23/44 | 26/44 |
| 交集Queen中位长度 | 3 | 3 |
| 交集Longest中位 | 36 | 31.5 |
| 我方运行／基础设施／预算余量失败 | 0 / 0 / 0 | 0 / 0 / 0 |

88场初始身体、地图/环境、回放SHA与官方终局核验通过；44对双方eligible且gross账可证，0未匹配、0重复键冲突、0分析失败。44对全部为sas-987；故障对手的正式结果仍保留，资源不自动填0。official-murder的资格变化也不删样本：Colosseum A、Queen of Spades A/B仅基线有效；Arena B、Stripes A、Trophy B仅导航有效。

基线源包`39cbf8c74f2d514ea5c0cb0b3b46fa16ef554486863427f0ebb8966f73b4c7fa`，WASM`7b2dd8a38996a93c5c3bf45526d74a366409072916000b9d2c169200d4fed40b`。导航源包`8735deddb3b034bc9d771ea7ef26ef9dbecab08a826761956598259607836691`，WASM`35bacafa16b66fcd522a50d4f973bf25a74e769a353cf9f8d6c3a692cdb9604a`；冻结于04:44:53 UTC。每场原始result/replay及依赖哈希在完整报告中保留。

## 全程资源与资本

完整比赛用各自终局；共同前缀是较早终局的同一完整轮末。支付与死亡增量是成本；绝对Longest的下降不越过Queen与消灭判定自动表示整体变弱。

| 指标（44对） | 整场中位差 | 整场均差 | 整场正／零／负 | 前缀中位差 | 前缀均差 |
| --- | ---: | ---: | --- | ---: | ---: |
| 收珠 | -7.50 | -23.23 | 18 / 0 / 26 | -6.00 | -18.84 |
| 支付长度 | -0.50 | +0.68 | 17 / 5 / 22 | 0 | +0.09 |
| 净收入 | -9.50 | -23.91 | 18 / 1 / 25 | -5.50 | -18.93 |
| 每千成功步净收入 | +1.51 | -1.88 | 24 / 0 / 20 | +1.43 | -0.34 |
| 已执行头位置并集 | -2.50 | -68.27 | 18 / 3 / 23 | -15.00 | -69.68 |
| 7×7 turnStart窗口并集 | 0 | -40.50 | 10 / 20 / 14 | 0 | -41.89 |
| 保有总长 | -1.00 | -17.55 | 22 / 0 / 22 | -5.50 | -16.14 |
| Queen长度 | 0 | +1.75 | 15 / 18 / 11 | 0 | +2.25 |
| Longest | -1.00 | -9.39 | 20 / 2 / 22 | -2.00 | -8.95 |
| 死亡带走的长度 | -5.00 | -6.36 | 19 / 0 / 25 | -2.00 | -2.80 |

采集效率的中位差为正，但它没有兑现为整场或前缀净收入提升；减少步数或集中路线也可能提高这个比值。实际视野窗口并集是合法turnStart几何覆盖，不能称作有用食物覆盖或真正可达区域。44对身体账净收入减死亡损失等于保有变化，分裂守恒不算收入。Queen自主净update均差−0.32、转出−1.82、Queen收珠−0.36与存活增加同时存在，不能只用“多活3条Queen”支持增长。

## 正式判负与可核实事件

两个独立有效非胜均为sas-987 Portals，且均进入44配对。

| 场景 | 正式终局与变化 | 直接事件与解释边界 |
| --- | --- | --- |
| Portals A | 基线win→导航draw，r499两队Q3、L3、T9，三轴全相等；基线我方Q3/L5/T8 | 我方净收入2→0、死亡3→0、split均0。不能归因于普通分裂增多；资源导航后未形成原来的Longest优势 |
| Portals B | 仍loss，但total判负→Queen判负；导航我方Q0/L6/T13，对手Q3/L3/T11 | Queen id1吃5/付费0、峰值8；r388/389/390依次分出2，8→6→4→2。r391長2执行N撞墙W，最后indicator为`FALLBACK loss_min no_confirmed_escape`。食物与L/T更高仍不能越过敌Queen优势。末局近因确定，身体拥堵／导航改变风险的根因尚待合法局部重放证伪 |

Queen三次分裂共转出6，净update+5，死亡帶走2，初始3+5−6−2=0，严格守恒；没有把继承资本当增长，也没有用末局总量猜付费。

## 地图机制与反例

每图只有同一新种子换边，不能视作多次独立随机重复；下列全部是sas-987直接观测，不是对手意图推测。

| 场景 | 净收入／保有差 | 计分语境或风险 |
| --- | --- | --- |
| Schooltime A/B | −198／−271；保有−41／−284 | 我方Queen均3、敌Queen均0，两臂均Queen胜且主margin保持3；Longest169→88、191→85是集中资本下降，不能称该局主判定退化 |
| Maze A/B | −94／+131；保有+55／+31 | 两队Queen均0且正式Longest判定；我方Longest157→119、152→101。更多保有总长并未形成同样的冠军集中资本 |
| Big Empty A/B | +23／+50；保有+85／−13 | 我方Queen28→3、38→7，正式仍Queen胜。Queen判定margin減少25／31，Longest下降不是该局的直接判负项 |
| Default A | +17，保有+15 | 我方Queen9→4，敌Queen均0，正式Queen胜但主margin减5；Longest89→104不抵消该Queen资产变化 |
| Australia B | −221，保有−133 | Queen24→0而Longest41→66；正式Queen→Longest胜，避免将L上升写成所有评分资产提升 |
| Devil B | +249，死亡多285，保有−36 | Longest49→15；更多收入被死亡吞掉，具体评分axis见终局语境附表 |
| Islands B | +229，保有+204 | 基线r145、导航r336終局；不同总时长，不能把整场增量直接当同时间效率。Queen21→0同时保留为资产代价 |
| Queen of Spades A | −203，保有−72 | 导航r174通过消灭获胜、基线到r442也消灭胜；更早消灭可以解释更低全场收入，不能将这项单独归为采集失败 |

全图资源下降不是只有Portals。Schooltime两侧收入与集中最长资本下降，但Queen主判定margin保持；Maze两侧Queen相等、相对Longest margin确实下降；Big Empty两侧收入增加却减少Queen margin。当前H2的普遍吞吐命题未获支持；需要把导航目的、资源分配与实际计分资本的保存连接起来。它并不证明所有更短比赛或任何Longest下降都更弱。

## 证据与限制

完整严格报告`test-results/oct7-foraging-discovery-compare.json`，SHA256`4ce39fb0a132ec48ae1b4c49515f144c4625aa94e3c68ff81b549de278697dd3`。冻结比较器`62546124105aa0a075a1c21eac9f0f23d51a5f218ba5b738b6048e10fd638250`没有为本候选改动。12项比较器离线检查包含真实官方回放与严格资源账；评分语境工具另有6项离线检查。

本页是发现集，不是天梯升级、最终新留出或Elo证明。单种子换边有相关性，公开实现较弱，对手运行失败单列。完整全图回放只用于离线审计，不作为候选隐藏信息输入。证据导入和重建命令不会启动比赛、上传或执行下载源码；本轮比赛由Root独立运行并记录实际完成范围。

## 终局评分语境附表

消灭优先，随后Queen、Longest、Total；只有两队仍有龙且Queen相等，Longest才参与。绝对我方Longest的变化与相对Longest margin（我方减敌方）分开。以下是对已结束比赛的描述分层，不改变预声明主分母或采用门槛；同轴subset按终局筛选，不能作为独立强度试验。

| 分母 | 基线正式axis数量 | 候选正式axis数量 | 两臂均Q相等且Longest参与 |
| --- | --- | --- | ---: |
| 全部正式88对 | 消灭32、Queen26、Longest29、Total1 | 消灭34、Queen31、Longest22、全轴平手1 | 15 |
| 有效配对交集 | 消灭11、Queen16、Longest16、Total1 | 消灭13、Queen20、Longest10、全轴平手1 | 7 |

有效交集中，两臂均达Longest规则的7对：相对Longest margin差中位-26、均值-20.00，2升／0同／5降。两臂均Queen主判定的13对：Q margin差中位+0、均值-1.46，4升／4同／5降。这些数字保留计分上下文，不否定其他Queen升级的样本。

| 有效交集：主判定转移 | 对数 |
| --- | ---: |
| 消灭→Longest | 2 |
| Longest→消灭 | 4 |
| 消灭→消灭 | 8 |
| Longest→Queen | 5 |
| Queen→Longest | 2 |
| Queen→Queen | 13 |
| 消灭→Queen | 1 |
| Longest→Longest | 6 |
| Longest→全轴平手 | 1 |
| Total→Queen | 1 |
| Queen→消灭 | 1 |

| 有效交集：Queen关系转移 | 对数 |
| --- | ---: |
| Q相等→Q相等 | 14 |
| 我方Q高→我方Q高 | 17 |
| Q相等→我方Q高 | 8 |
| 我方Q高→Q相等 | 4 |
| Q相等→敌方Q高 | 1 |

以下21对的Queen关系或正式axis发生变化，逐对保留；列中“是／否”表示该臂两队Queen是否相等。其他配对及无效对手的全部正式结果仍在88行JSON中。

| 对手／地图／我方侧 | 基线axis；Q相等；Q/L margin | 候选axis；Q相等；Q/L margin | 正式结果 |
| --- | --- | --- | --- |
| sas-987／Colosseum／A | 消灭；是；Q差+0；L差+29 | Longest；是；Q差+0；L差+25 | win→win |
| sas-987／Colosseum／B | Longest；是；Q差+0；L差+42 | 消灭；是；Q差+0；L差+19 | win→win |
| sas-987／australia／A | Longest；是；Q差+0；L差+63 | Queen；否；Q差+15；L差+107 | win→win |
| sas-987／australia／B | Queen；否；Q差+24；L差+37 | Longest；是；Q差+0；L差+63 | win→win |
| sas-987／default／B | 消灭；否；Q差+8；L差+31 | Queen；否；Q差+20；L差+30 | win→win |
| sas-987／default_small／A | Longest；是；Q差+0；L差+43 | 消灭；是；Q差+0；L差+17 | win→win |
| sas-987／islands／A | Longest；是；Q差+0；L差+44 | 消灭；否；Q差+30；L差+34 | win→win |
| sas-987／islands／B | 消灭；否；Q差+21；L差+30 | 消灭；是；Q差+0；L差+52 | win→win |
| sas-987／portals／A | Longest；是；Q差+0；L差+2 | 全轴平手；是；Q差+0；L差+0 | win→draw |
| sas-987／portals／B | Total；是；Q差+0；L差+0 | Queen；否；Q差-3；L差+3 | loss→loss |
| sas-987／queen_of_spades／A | 消灭；否；Q差+10；L差+16 | 消灭；是；Q差+0；L差+9 | win→win |
| sas-987／slithery_fight／A | Longest；是；Q差+0；L差+35 | Queen；否；Q差+15；L差+49 | win→win |
| sas-987／slithery_fight／B | Longest；是；Q差+0；L差+64 | Queen；否；Q差+7；L差+40 | win→win |
| sas-987／stripes／A | 消灭；是；Q差+0；L差+20 | Longest；是；Q差+0；L差+9 | win→win |
| sas-987／stripes／B | Queen；否；Q差+7；L差+7 | 消灭；否；Q差+12；L差+12 | win→win |
| sas-987／stronghold／A | Queen；否；Q差+14；L差+30 | Longest；是；Q差+0；L差+16 | win→win |
| sas-987／tower_defense／A | Longest；是；Q差+0；L差+41 | 消灭；是；Q差+0；L差+16 | win→win |
| sas-987／tower_defense／B | Longest；是；Q差+0；L差+4 | Queen；否；Q差+24；L差+21 | win→win |
| sas-987／trophy／A | 消灭；是；Q差+0；L差+50 | 消灭；否；Q差+20；L差+32 | win→win |
| sas-987／trophy／B | 消灭；是；Q差+0；L差+51 | 消灭；否；Q差+21；L差+30 | win→win |
| sas-987／unsw／B | Longest；是；Q差+0；L差+54 | Queen；否；Q差+19；L差+57 | win→win |

附表完整来源`test-results/oct7-foraging-scoring-context.json`，SHA256`a55048bf5bd083e6dd8f2becc23019707d1ab26561db55823ad7214daa6b5ac1`；0终局评分核验issues。新增只读工具`tools/oct7_scoring_context.py` SHA256`19834f94e080eada024f5dc9bce45e7fb28f32828684e364323203e101af2eec`，6项离线检查通过。冻结比较器及其缓存均未改动。
