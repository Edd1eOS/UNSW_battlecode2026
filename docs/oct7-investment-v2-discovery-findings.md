# Oct7 联合投资v2：合同范围与整场兑现

第二版完整88场于05:15前后到齐，严格配对报告生成于2026-10-07 05:16:00 UTC。它遵守普通投资的最小终端合同，但没有证实全队收入兑现：45有效配对的整场净收入均差−52.76、共同前缀−69.89，死亡成本均差−24仍不足抵消，保有总长均差−28.76。Queen净update与部分Longest提高是真实正例；当前不支持凭局部合同或少死通过H1采用门槛。

V2是在看到V1发现集后修改设计，再分别对相同冻结外部对手、22地图、种子`2026100701`和A/B侧比赛。没有自家版本互战；这是开发配对机制分析，不能继承未开留出的独立性。方法见[预声明计划](oct7-hypothesis-validation-plan.md)，家族定义见[资本审计](oct7-family-capital-audit.md)。

## 分母与身份

| 范围 | 冻结V5 | 投资V2 |
| --- | --- | --- |
| 全部正式88 | 87W1L | 82W5L1D |
| 各自双方运行有效，独立分母 | 47：46W1L | 47：45W1L1D |
| 有效交集配对 | 45：44W1L | 45：44W1L |
| 交集Queen终局存活 | 24/45 | 23/45 |
| 交集Queen中位长度 | 3 | 2 |
| 交集Longest中位 | 36 | 35 |
| 我方运行／基础设施／预算余量失败 | 0 / 0 / 0 | 0 / 0 / 0 |

88回放/初始/地图/环境/终局核验，45双方eligible且gross可证，0缺失、0冲突、0分析失败；家族配对45也0失败，投资独立47另行核对0失败。资格变化来自official-murder：Colosseum B、Stripes A仅投资有效；Queen of Spades A/B仅V5有效。全部正式结果与单侧故障仍保留，故障对手资源不自动记0。

唯一独立有效败局为sas-987 Portals A：r499双方Q3/L3，total5对9，正式Total判负；基线在该侧Longest获胜。有效draw为official-murder Colosseum B：r39双方消灭，不进入45交集。其他4个正式败局是对手存在无效动作的official-murder Arena A/B、Default A、Default Small B；不删除，也不凭对手错误推断失败根因。

投资源包`544d99477b55cb9e07db76a09c6e0483131463e5e56f46a4eebef90ba75e3de7`，WASM`09906063e617fd8ed8d28c1ef160f5a1c2127a2a1bf29f089f27ae5704de053c`；本面板我方最高59,762,894 points。V5源包`39cbf8c74f2d514ea5c0cb0b3b46fa16ef554486863427f0ebb8966f73b4c7fa`，WASM`7b2dd8a38996a93c5c3bf45526d74a366409072916000b9d2c169200d4fed40b`。报告逐场绑定原始result/raw/依赖。

## 整场及共同前缀

差值为V2减V5。完整比赛是各自终局；共同前缀为较早终局的同一完整轮末。支付与死亡增量是成本，出生继承不算收入，绝对Longest不越过Queen主判定直接评价强弱。

| 指标（45对） | 整场中位差 | 整场均差 | 正／零／负 | 前缀中位差 | 前缀均差 |
| --- | ---: | ---: | --- | ---: | ---: |
| 收珠 | −20 | −49.60 | 15 / 0 / 30 | −25 | −67.87 |
| 支付 | −2 | +3.16 | 18 / 3 / 24 | −1 | +2.02 |
| 净收入 | −21 | −52.76 | 15 / 1 / 29 | −24 | −69.89 |
| 每千成功步净收入 | +4.72 | +6.58 | 30 / 0 / 15 | +5.62 | +8.88 |
| 已执行头位置并集 | −3 | −11.89 | 19 / 1 / 25 | −14 | −40.42 |
| 7×7 turnStart窗口并集 | 0 | +2.96 | 12 / 25 / 8 | 0 | −3.29 |
| 死亡带走的长度 | −20 | −24.00 | 17 / 0 / 28 | −11 | −32.11 |
| 保有总长 | −3 | −28.76 | 20 / 1 / 24 | −11 | −37.78 |
| Queen长度 | 0 | +0.91 | 15 / 20 / 10 | 0 | +1.33 |
| Longest | +3 | +1.73 | 26 / 0 / 19 | +4 | +0.07 |
| Queen自主净update | +4 | +7.07 | 27 / 6 / 12 | +4 | +6.18 |
| Queen分裂转出 | 0 | +4.13 | 20 / 11 / 14 | 0 | +2.89 |
| 分裂次数 | −7 | −13.80 | 14 / 2 / 29 | −7 | −17.62 |

45对身体账：净收入差−2374、死亡差−1080，保有差−1294，完全守恒。单位步效率多数提高没有兑现为全队吞吐；覆盖窗口只是几何观察范围，不等于有用或可达食物。Queen增长提高与存活减少同时存在，不能只按一个轴通过增长与保命命题。

Schooltime A/B净收入−514／−381，Longest169→128、191→184；两臂我方Queen3、敌Queen0，正式Queen胜margin保持3，不能把Longest下降写成主判定退化。Big Empty B净收入−735、保有−597、Queen38→0、Longest140→161，正式Queen胜转Longest胜。Around UNSW A净收入−144、保有−43，B净收入+154、保有+56，地图两侧不一致。

Default A与V1相同的QueenTrade观测仍保留：Queen9→17、敌Queen均0，主判定margin提高8；Longest89→17不是该局整体评分退化证明。正式结果、终局选择优先级与额外资源代价分别报告，不从indicator推断对手意图或完整反事实因果。

## 家族与预测：独立47场

独立47场（45W1L1D）包含4723次SPLIT，4691完整两轮cohort、32末局截断。两轮净保有1004正、1861零、1826负；cohort重叠，不能相加成全队收益，也不能当4691独立试验。

完整两轮且自报`joint_complete=1`只有347：实际net低于预测150、同186、高11，实际减预测均值−0.5043、中位0；该347中仅22个净保有负。V1的独立48与V2独立47不同，不能用两组总事件数或均差直接宣称预测改善或退化。

在每个官方split event之前按initial/出生/死亡维护真实存活队伍数量，匹配家族event index、parent/child与indicator；以下是直接范围事实，普通／rebuild／紧急的政策解释来自绑定的冻结源码，不是官方给出的策略标签。

| 观测范围 | SPLIT数 | 完整两轮 | 两轮净保有正／零／负 | 预测实际低／同／高 |
| --- | ---: | ---: | --- | --- |
| complete，split前多于1个我方单位（普通投资） | 344 | 342 | 139 / 181 / 22 | 147 / 186 / 9 |
| complete，split前仅1单位（rebuild豁免） | 5 | 5 | 4 / 1 / 0 | 3 / 0 / 2 |
| 无complete joint（按该冻结源码为emergency） | 4374 | 4344 | 861 / 1679 / 1804 | 无完整预测 |

普通344个选中proposal的已记录终端grade0为0，未发现已知死端穿透合同；普通完整342的实际net减预测均值−0.5088。5个rebuild中有3个端grade0，是源码`rebuild=(unit_count==1)`明确豁免，不能称合同bug。4374次无完整joint占所有split的92.6%，1826个负保有窗口中的1804来自该层；普通合同不能被描述成覆盖这些紧急决策或全队死亡。

资本门槛只针对区域RESERVE：所有完整proposal中，HARVEST324有319次family max下降，源码允许；RESERVE20均未下降；Queen rebuild5有4次下降，仍是豁免。它保住了被选中的区域资本合同，不等于所有已有Longests都受保护。终端grade2表示未知、门户或搜索耗尽的未决延续，仍允许；因此这里是排除已知局部封闭，不能宣称两个actor各有两步完全确认、动态敌头安全或后续计划已承诺。

父/子仍各自重新choose；联合World.records没有作为控制计划继承。普通合同的静态终端可行与真实后续收入是不同证据，不能将22个普通负保有当作全队−2374收入或死亡的唯一解释。分裂后毛收珠/付费阶段未知时保留未知，净update与死亡长度由严格身体账证明。

## 证据、补充参照及结论边界

| 忽略目录中的报告 | SHA256 |
| --- | --- |
| `oct7-investment-v2-discovery-compare.json` | `541c5bae89446e9d88ca0e290d5c7e90948e4e29b39243549681b7accb03266c` |
| `oct7-investment-v2-family-capital.json`（45配对） | `33724bca09aec6099e5133c08de8da66278ef26305a815e1dc0730e5cfeaf131` |
| `oct7-investment-v2-joint47-summary.json`（独立47） | `d5e7daabf15e3b552f6a509e755998bd6d95473792d1c3b2fa4118a26c99151c` |
| `oct7-investment-v2-split-scope.json`（逐事件范围） | `f42c2fe66b5a0a39240c96cf68d3cdc9d9c17a1f907d95f9cfd0fe89a4094528` |

Active v14参照只完成17/88：V2对其补充17匹配、10双方运行有效/gross可证，其中1场Active余量失败，9对预算通过；71缺配保留，不替代V5完整主分析。部分报告`oct7-investment-v2-vs-active-partial.json` SHA`100a92e26203587bbaca042cdca27ecaaa920cb0a727650eef7cdd26835ea4ea`，不作完整强度结论。

当前证据支持“普通局部合同按范围执行”，不支持“合同已解决V1全部死亡或全队资源投资兑现”。修改设计后另行冻结；最终胜者须新未开留出及真实对手确认，弱公开bot胜数不换算Elo。29项离线检查通过，原冻结比较器、家族工具、候选与旧证据均未改动。离线重建不会启动比赛、上传或执行下载源码；Root独立比赛才计入实际完成数。

## 终局评分语境附表

消灭优先，随后Queen、Longest、Total。以下同轴subset为终局解释，不替代45主配对分母，不重新定义采用门槛。

| 范围 | V5正式axis | 投资V2正式axis | 两臂均Q相等、两队存活且Longest参与 |
| --- | --- | --- | ---: |
| 全部正式88对 | 消灭32、Queen26、Longest29、Total1 | 消灭31、Queen26、Longest29、Total1、全轴平手1 | 19 |
| 运行有效45对 | 消灭12、Queen16、Longest16、Total1 | 消灭10、Queen17、Longest17、Total1 | 9 |

两臂Longest规则都参与的9对：相对Longest margin差中位−3、均值−0.78，3升0同6降。两臂Queen主判定的12对：Queen margin差中位+2、均值+9.08，6升4同2降。这些计分改进和代价都保留，不把绝对Longest均值上升当作全评分改善，也不忽略Default A的Queen升级。

| 有效配对axis转移 | 对数 |
| --- | ---: |
| 消灭→消灭 | 5 |
| 消灭→Longest | 6 |
| Longest→Longest | 8 |
| Longest→Queen | 3 |
| Queen→Queen | 12 |
| Queen→Longest | 3 |
| 消灭→Queen | 1 |
| Longest→消灭 | 4 |
| Longest→Total | 1 |
| Total→Queen | 1 |
| Queen→消灭 | 1 |

| 对手／地图／侧（全部Q关系或axis变化23对） | V5 axis；Q相等；Q差；L差 | V2 axis；Q相等；Q差；L差 | 正式结果 |
| --- | --- | --- | --- |
| sas-987／Colosseum／A | 消灭；是；+0；+29 | Longest；是；+0；+50 | win→win |
| sas-987／arena／A | 消灭；否；+36；+36 | 消灭；是；+0；+33 | win→win |
| sas-987／australia／A | Longest；是；+0；+63 | Queen；否；+2；+30 | win→win |
| sas-987／big_empty／B | Queen；否；+38；+128 | Longest；是；+0；+127 | win→win |
| sas-987／default／B | 消灭；否；+8；+31 | Queen；否；+12；+49 | win→win |
| sas-987／default_small／A | Longest；是；+0；+43 | 消灭；否；+12；+24 | win→win |
| sas-987／default_small／B | 消灭；否；+8；+16 | 消灭；是；+0；+32 | win→win |
| sas-987／devil／A | 消灭；是；+0；+32 | Longest；是；+0；+32 | win→win |
| sas-987／devil／B | Longest；是；+0；+46 | 消灭；是；+0；+34 | win→win |
| sas-987／dilemma／A | Queen；否；+15；+12 | Longest；是；+0；+15 | win→win |
| sas-987／islands／A | Longest；是；+0；+44 | 消灭；是；+0；+51 | win→win |
| sas-987／islands／B | 消灭；否；+21；+30 | Longest；是；+0；+75 | win→win |
| sas-987／portals／A | Longest；是；+0；+2 | Total；是；+0；+0 | win→loss |
| sas-987／portals／B | Total；是；+0；+0 | Queen；否；+3；+3 | loss→win |
| sas-987／queen_of_spades／A | 消灭；否；+10；+16 | Longest；是；+0；+66 | win→win |
| sas-987／stripes／A | 消灭；是；+0；+20 | Longest；是；+0；+7 | win→win |
| sas-987／stripes／B | Queen；否；+7；+7 | 消灭；否；+12；+12 | win→win |
| sas-987／stronghold／B | Longest；是；+0；+12 | Queen；否；+3；+49 | win→win |
| sas-987／tower_defense／A | Longest；是；+0；+41 | 消灭；否；+4；+28 | win→win |
| sas-987／tower_defense／B | Longest；是；+0；+4 | Queen；否；+23；+20 | win→win |
| sas-987／trauma／A | Queen；否；+8；+10 | Longest；是；+0；+23 | win→win |
| sas-987／trophy／A | 消灭；是；+0；+50 | Longest；是；+0；+48 | win→win |
| sas-987／trophy／B | 消灭；是；+0；+51 | 消灭；否；+19；+67 | win→win |

完整88行附表SHA`e8e59b630cb1a69c66c2ec4a7d22bac48e12dce62d3980da207b5c7bf4ee6085`，0评分核验issues；只读工具SHA`19834f94e080eada024f5dc9bce45e7fb28f32828684e364323203e101af2eec`。全部正式无效样本仍在JSON中，不因计分axis变化丢样本。
