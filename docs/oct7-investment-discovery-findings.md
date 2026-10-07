# Oct7 联合投资v1：完整发现集与资本兑现

投资v1的88场于04:45:17 UTC完成；严格配对报告04:46:04 UTC，`actual_scope=complete`。更多整场收入没有稳定兑现为保有资本：有效交集45对的净收入均差+23.07，死亡长度均差+57.91，终局总长均差−34.84，Longest均差−8.33。共同前缀净收入均差−8.67。当前不支持采用该冻结政策，保留为设计发现：H1的前缀净收益与死亡资本证据不稳。绝对Longest下降只是资产变化，不能越过Queen优先级直接判为整体变弱；例如Default A的Queen判定优势反而增加。

方法先声明于[本轮计划](oct7-hypothesis-validation-plan.md)，家族与cohort定义见[资本对齐方法](oct7-family-capital-audit.md)。两个版本各自对相同外部对手、22地图、A/B侧和种子`2026100701`比赛，没有自家版本相互对战。

## 分母及身份

| 范围 | 冻结v5 | 投资v1 |
| --- | --- | --- |
| 全部88正式结果 | 87W1L | 84W3L1D |
| 各自双方运行有效，独立分母 | 47：46W1L | 48：46W1L1D |
| 两组有效交集，配对分母 | 45：44W1L | 45：44W1L |
| 交集Queen存活 | 24/45 | 24/45 |
| 交集Queen中位长度 | 3 | 3 |
| 交集Longest中位 | 36 | 31 |
| 我方运行／基础设施／预算余量失败 | 0 / 0 / 0 | 0 / 0 / 0 |
| 全部比赛我方最高points | 27,476,943 | 57,634,445 |

88匹配、88回放/初始/环境/终局核验通过；45双方eligible且45双方gross可证；0缺失、0重复键冲突、0分析失败。投资单独48有效场没有缩成45：其他三场保留独立正式结果及单侧联合兑现账，不能参加跨版本资源差值。

资格变化来自official-murder：Colosseum B、Stripes A、Trophy B仅投资侧双方有效；Queen of Spades A/B仅基线侧双方有效。行动改变对手轨迹及其无效事件，不能凭有利一侧选择分母。全部无效场仍留正式结果，投资的两个Arena消灭败局包含对手无效动作，同样不删掉。

投资唯一独立有效败局是sas-987 Portals A：r499双方Queen3、Longest3，total5对9，直接判负项为total。独立有效draw是official-murder Colosseum B：r39双方全部消灭。该draw因基线侧对手有无效动作，未进入45配对，仍进入投资48。

基线源包`39cbf8c74f2d514ea5c0cb0b3b46fa16ef554486863427f0ebb8966f73b4c7fa`，WASM`7b2dd8a38996a93c5c3bf45526d74a366409072916000b9d2c169200d4fed40b`。投资源包`7ebeb53a460cdeea3dfea402c365d579aa026f28cd079b81384a1186caf00409`，WASM`ef2a3df83770807943fd3ceb5d44077a89f4e0542d0f7166a4d675b12c8a34ba`。每场来源、原回放及分析依赖哈希保存于报告。

## 整场与共同前缀

差值均为投资减基线，仅45有效配对；支付、死亡损失、分裂增加不是收益。

| 指标 | 整场中位差 | 整场均差 | 正／零／负 | 共同前缀中位差 | 前缀均差 | 前缀正／零／负 |
| --- | ---: | ---: | --- | ---: | ---: | --- |
| 收珠 | +7 | +46.69 | 28 / 0 / 17 | −11 | +9.00 | 21 / 0 / 24 |
| 支付长度 | +2 | +23.62 | 25 / 3 / 17 | 0 | +17.67 | 21 / 4 / 20 |
| 净收入 | +3 | +23.07 | 26 / 0 / 19 | −15 | −8.67 | 19 / 0 / 26 |
| 每千成功步净收入 | −1.56 | −5.37 | 21 / 0 / 24 | −1.28 | −0.76 | 21 / 0 / 24 |
| 已执行头位置并集 | 0 | +17.33 | 22 / 3 / 20 | −3 | −11.71 | 18 / 2 / 25 |
| 7×7 turnStart窗口并集 | 0 | +17.40 | 14 / 22 / 9 | 0 | +11.16 | 13 / 22 / 10 |
| 保有总长 | −3 | −34.84 | 19 / 2 / 24 | −17 | −45.96 | 16 / 2 / 27 |
| Queen长度 | 0 | +1.31 | 16 / 20 / 9 | 0 | +1.80 | 17 / 19 / 9 |
| Longest | −3 | −8.33 | 20 / 0 / 25 | 0 | −8.47 | 22 / 1 / 22 |
| 死亡长度 | +4 | +57.91 | 26 / 0 / 19 | −2 | +37.29 | 21 / 1 / 23 |
| 分裂次数 | +4 | +9.24 | 24 / 2 / 19 | −2 | −1.53 | 17 / 4 / 24 |

45对总量的身体账：额外净收入+1038，额外死亡长度+2606，保有差−1568，完全守恒。不能把额外出生长度或请求MOVE步数当收入。Queen另有自主净update均差+5.98、转出+2.67、死亡资本+2.00，最终只保留+1.31；同样的24/45存活不能代替长度与资本流向。

唯一最长单位死亡造成的评分损失均差+5.69，16对增加、3对减少、26不变，但它不是全部Longest退化的解释。部分家族从未形成相同的大单位。共同前缀是到较早终局的同一完整轮末，不能代替完整终局；每臂另保存Queen状态阶段，但其时长和转变时刻不同，不盲减两个不等时阶段。

## 关键地图及家族

以下均为sas-987相同种子换边的直接观测，根本策略原因另列为假说。

| 场景 | 收入与死亡 | 终局评分资产／家族证据 |
| --- | --- | --- |
| Around UNSW A | 净收入+628，死亡长度+904，保有−276 | Longest71→31。founder6家族152 net−57 death+初始2=97，投资61−63+2=0；其他家族虽扩张，死亡与分散仍吞掉资本 |
| Around UNSW B | 净收入+600，死亡长度+711，保有−111 | Longest57→34；原founder17家族活216→10。founder13新增活177，终局37条中家族最长26，无法替代原冠军集中资本 |
| Slithery Fight B | 净收入+53，死亡长度+186，保有−133 | Longest68→18。基线founder7家族90 net−24 death+2=68；投资该founder215次无食成功步、0 split，r215以other-body死亡，家族资本0。不是“分裂吞了一个已有68冠军” |
| Schooltime A | 净收入−232，死亡少119，保有−113 | Longest169→100。原founder4家族净354→180、死亡125→18、活233→166；更少损失仍不足抵消少174收入 |
| Default A | 净收入−24，死亡多97，保有−121 | Longest89→17。基线founder4家族活139；投资该初始龙只吃1、0 split，r22 head-to-head死亡，indicator为`QUEEN_TRADE`，家族活0。双方正式均以Queen获胜：我方Queen9→17、敌Queen均0，主判定margin增加8；不能因Longest下降72否定这项评分升级，也不能从indicator证明全部反事实因果 |
| Big Empty B | 净收入−613，死亡少114，保有−499 | Queen38→0，Longest140→151；一个轴上升掩盖其他资产损失 |
| Portals A | 净收入+1、死亡多4、保有−3 | Queen3不变、Longest5→3，正式win→total败；没有普通split，不能归因于该局复制数量增加 |
| Autarky两侧 | 净收入均差−48、保有−8.5 | Queen均差+21，但Longest均差−4；资源份额与保有仍需分开 |

上述死亡原因及最后动作是直接事件／近因；“食物竞争、长期路线被改变、联合预测未被后续控制器执行”需要合法观察重放或新构造分离。初始founder对齐、资本账守恒提供可证资产链，不能重建对手意图或未执行的反事实。

## 联合预测与实际两轮兑现：独立48场

单独核对投资48场双方运行有效比赛，0家族／账目失败，保留46W1L1D；它与45配对比较的分母不同。共有5763次split，其中5745个完整两轮cohort、18末局截断。两轮父体+新子及后继的净保有为1337正、2424零、1984负。cohort重叠，**不可把这些事件相加成全队收入或当5745个独立试验**。它们包含不同类型的分裂，不能都称作有完整联合预测的普通投资。

其中1383个同turn自报`joint_complete=1`且窗口完整的预测：实际net update低于预测580、相等737、高于66；实际减预测均值−0.4765。该子集只有81个两轮净保有负，因此预测偏差不能单独解释全队额外死亡与Longest损失。其余未报告完整预测的分裂及整体移动／trade／风险决策需要单独解释。

| complete预测的搜索flags | 次数 | 实际低／同／高 | 实际net−预测均值 | 两轮净保有负 |
| --- | ---: | --- | ---: | ---: |
| unknown1、pruned1、budget0 | 980 | 421 / 516 / 43 | −0.495 | 48 |
| unknown0、pruned1、budget0 | 218 | 101 / 108 / 9 | −0.546 | 19 |
| unknown1、pruned0、budget0 | 120 | 36 / 73 / 11 | −0.267 | 8 |
| unknown0、pruned0、budget0 | 61 | 19 / 39 / 3 | −0.311 | 6 |
| budget1的其余两层 | 4 | 3 / 1 / 0 | −1.000 | 0 |

unknown/pruned描述整个有限搜索遇到的分支，不表示选中的路径一定未知或非法；complete表示找到该调度，不能说穷尽搜索或保证后续行动。Slithery B的142预测中80低、59同、3高，均差−0.725；UNSW A151中67低78同6高，均差−0.550；B85中37低45同3高，均差−0.459。即使全flags0仍有偏差，不能只禁止某个flag就声称已解决兑现。

源码明确的结构边界：`investment.hpp::evaluate_split`模拟`{child,parent,child}`三次动作，但`World.records`仅用于评分；最终planner只发送本次SPLIT。后续父/子各自重新choose，没有计划承诺、通信或records继承；也没有从这三次之后继续验证每个actor的终端续路。因此“联合优化机会”不是“已实现的联合控制”。实际后续行动、其他头、刷新与视野变化均能改变收入。这是下一次设计可证伪的机制假说，不是本报告已证明每次低估差的唯一原因。

## 当前结论与证据文件

H1“复制机会兑现为新增覆盖、净收入和终局资本”未得到稳定支持：前缀收入多数下降，整场收益更多被死亡吞掉。H3必须按终局判定语境解释：Default A的Queen优势提升是真实正例，而两臂Queen相等且Longest均参与的12对中，相对Longest margin多数下降。当前拒绝依据是收入兑现与死亡成本，不能凭Queen同样存活、更多food或绝对Longest下降单独判定。下一版应验证短期终端续路与实际父子控制策略的一致性、机会是否被后续动作兑现、已经形成的家族资产如何保留，保留未分裂、trade及长期停滞作为独立原因。修改后重新冻结，不继承本发现集独立性。

| 忽略目录中的完整报告 | SHA256 |
| --- | --- |
| `oct7-investment-discovery-compare.json` | `ba72ec8a128d06e98cbf32b9cc4a366b9b2d9a2ce7ac60c4c9e85c5913bcb40d` |
| `oct7-investment-family-capital.json`（45配对） | `000ab88e26e577402584dce0ff7809cf8558d6b32d4b789157a2f8b24c70d7c1` |
| `oct7-investment-joint48-summary.json`（独立48） | `0433dd748cab13fb952ec67d0e10aceb1acf4c0f70563faae25ba50ae249f0ef` |
| `oct7-investment-forecast-strata.json` | `16ac5d2f1d9901707919b5e4458a561b37ca6b4a0c53aafadd38efe7ef295c67` |

比较器仍为冻结`62546124105aa0a075a1c21eac9f0f23d51a5f218ba5b738b6048e10fd638250`，家族工具`28611740198b0827d887085042a0a7ff8cef7f5bb39da14de9c41084ccb1105e`。23项离线检查通过，包括实际官方回放与body/gross账集成。所有报告绑定原始回放与依赖，不把未知付费补成0；原始raw不入git。

本页是机制发现，不是成熟线上对手验收或Elo换算。证据导入与重建命令不会开启比赛、上传或执行下载源码；本轮比赛由Root另行运行并保留实际完成日志。

## 终局评分语境附表

消灭优先，随后Queen、Longest、Total；只有两队仍有龙且Queen相等，Longest才参与。绝对我方Longest的变化与相对Longest margin（我方减敌方）分开。以下是对已结束比赛的描述分层，不改变预声明主分母或采用门槛；同轴subset按终局筛选，不能作为独立强度试验。

| 分母 | 基线正式axis数量 | 候选正式axis数量 | 两臂均Q相等且Longest参与 |
| --- | --- | --- | ---: |
| 全部正式88对 | 消灭32、Queen26、Longest29、Total1 | 消灭33、Queen30、Longest23、Total1、全轴平手1 | 18 |
| 有效配对交集 | 消灭12、Queen16、Longest16、Total1 | 消灭10、Queen19、Longest15、Total1 | 12 |

有效交集中，两臂均达Longest规则的12对：相对Longest margin差中位-24.5、均值-25.33，1升／0同／11降。两臂均Queen主判定的13对：Q margin差中位+8、均值+8.38，7升／4同／2降。这些数字保留计分上下文，不否定其他Queen升级的样本。

| 有效交集：主判定转移 | 对数 |
| --- | ---: |
| 消灭→消灭 | 7 |
| 消灭→Longest | 2 |
| Longest→Longest | 11 |
| Queen→Queen | 13 |
| Queen→Longest | 2 |
| 消灭→Queen | 3 |
| Longest→消灭 | 2 |
| Longest→Total | 1 |
| Total→Queen | 1 |
| Queen→消灭 | 1 |
| Longest→Queen | 2 |

| 有效交集：Queen关系转移 | 对数 |
| --- | ---: |
| 我方Q高→我方Q高 | 16 |
| Q相等→Q相等 | 16 |
| 我方Q高→Q相等 | 6 |
| Q相等→我方Q高 | 7 |

以下18对的Queen关系或正式axis发生变化，逐对保留；列中“是／否”表示该臂两队Queen是否相等。其他配对及无效对手的全部正式结果仍在88行JSON中。

| 对手／地图／我方侧 | 基线axis；Q相等；Q/L margin | 候选axis；Q相等；Q/L margin | 正式结果 |
| --- | --- | --- | --- |
| sas-987／Colosseum／A | 消灭；是；Q差+0；L差+29 | Longest；是；Q差+0；L差+37 | win→win |
| sas-987／arena／A | 消灭；否；Q差+36；L差+36 | 消灭；是；Q差+0；L差+14 | win→win |
| sas-987／big_empty／B | Queen；否；Q差+38；L差+128 | Longest；是；Q差+0；L差+123 | win→win |
| sas-987／default／B | 消灭；否；Q差+8；L差+31 | Queen；否；Q差+12；L差+31 | win→win |
| sas-987／default_small／A | Longest；是；Q差+0；L差+43 | 消灭；否；Q差+26；L差+26 | win→win |
| sas-987／default_small／B | 消灭；否；Q差+8；L差+16 | 消灭；是；Q差+0；L差+31 | win→win |
| sas-987／devil／A | 消灭；是；Q差+0；L差+32 | 消灭；否；Q差+9；L差+31 | win→win |
| sas-987／dilemma／A | Queen；否；Q差+15；L差+12 | Longest；是；Q差+0；L差+15 | win→win |
| sas-987／islands／A | Longest；是；Q差+0；L差+44 | 消灭；是；Q差+0；L差+44 | win→win |
| sas-987／islands／B | 消灭；否；Q差+21；L差+30 | 消灭；是；Q差+0；L差+78 | win→win |
| sas-987／portals／A | Longest；是；Q差+0；L差+2 | Total；是；Q差+0；L差+0 | win→loss |
| sas-987／portals／B | Total；是；Q差+0；L差+0 | Queen；否；Q差+3；L差+3 | loss→win |
| sas-987／queen_of_spades／A | 消灭；否；Q差+10；L差+16 | Longest；是；Q差+0；L差+44 | win→win |
| sas-987／stripes／A | 消灭；是；Q差+0；L差+20 | Queen；否；Q差+2；L差+8 | win→win |
| sas-987／stripes／B | Queen；否；Q差+7；L差+7 | 消灭；否；Q差+12；L差+12 | win→win |
| sas-987／stronghold／B | Longest；是；Q差+0；L差+12 | Queen；否；Q差+8；L差+33 | win→win |
| sas-987／tower_defense／B | Longest；是；Q差+0；L差+4 | Queen；否；Q差+23；L差+20 | win→win |
| sas-987／trophy／B | 消灭；是；Q差+0；L差+51 | Queen；否；Q差+5；L差+58 | win→win |

附表完整来源`test-results/oct7-investment-scoring-context.json`，SHA256`61ba955cc7b2ec5f92a350cf29c0b2462ff6c65bd20e803ba24d8790e81c3df3`；0终局评分核验issues。新增只读工具`tools/oct7_scoring_context.py` SHA256`19834f94e080eada024f5dc9bce45e7fb28f32828684e364323203e101af2eec`，6项离线检查通过。冻结比较器及其缓存均未改动。
