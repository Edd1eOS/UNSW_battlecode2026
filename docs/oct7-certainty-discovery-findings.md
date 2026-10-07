# Certainty V1完整发现：候选级深度优先与保护代价

2026-10-07主发现88全部完成。固定对手、22张地图、种子2026100701和两侧与V5配对；没有自己版本相互对战。Queen终局存活由25/47增至28/47是正向观察，但新增一场消灭败局、同Q达到Longest判定的相对长度下降及资源代价，使H3全场保护方向仍混合，**目前未支持采用或开启独立留出**。没有以单一负收入或绝对Longest均值作为自动否决规则，也没有以86W自动晋升。

## 冻结、范围与分母

| 项目 | V5 | Certainty V1 |
| --- | --- | --- |
| 源包SHA256 | `39cbf8c74f2d514ea5c0cb0b3b46fa16ef554486863427f0ebb8966f73b4c7fa` | `01621a5fcfc6e55493a2a8003b73eb317e3b6f6ce7a4ce32be8e920695ac0e7c` |
| WASM SHA256 | `7b2dd8a38996a93c5c3bf45526d74a366409072916000b9d2c169200d4fed40b` | `22dfd8df1d90445d1ee9405fb62b8a0c9a495097859c5bb40ab9ba17e89a180f` |
| 已计划／实际完成 | 88/88 | 88/88 |
| 全部正式结果 | 87W1L | 86W2L |
| 各自运行有效 | 47：46W1L | 47：45W2L |
| 各自不适格 | 41 | 41 |

匹配88、全程环境／回放核验88；双方有效交集47，双方有效且gross账可证交集47。缺配0、重复冲突0、strict分析失败0、评分context问题0。我方runtime、基础设施和90M余量失败均0，候选实际peak21,753,536 points。对手无效运行事件2201保留正式结果，41不适格不进入机制交集；不能借对手故障推断资源为0或天梯强度。候选在06:06:58.971 UTC正式冻结，完整比较于06:15:45.154 UTC生成；独立176留出尚未开启，候选线上比赛0。

仅protected grade2候选在原contact→grade→birth之后增加现有depth优先，其余政策复制V5；没有与投资、allocation、探索或合作模块合并。[实现及局部Trauma说明](generalist-certainty-v1.md)和[审计读者说明](oct7-certainty-audit-reader.md)分别记录功能和证据边界。

## 固定47对的资源、执行与资本

下表差值均为候选减V5；“+/0/−”是47个配对方向数，非独立统计显著性。全程比较各自实际终局；共同前缀截止两臂较早终局。gross food/paid、身体更新、死亡资本和分裂转移经过原始事件账校验。死亡资本负值表示减少损失，不与收入正向混称；split转移守恒而不是增长。覆盖只计实际已执行头位置或合法观测窗口，不能当可得资源。

| 指标 | 全程：中位/均值/+/0/− | 共同前缀：中位/均值/+/0/− |
| --- | --- | --- |
| 收珠 | -2 / -26.85 / 13/9/25 | 0 / -23.04 / 17/9/21 |
| 实际付费损耗 | 0 / -1.3 / 17/9/21 | 0 / -0.11 / 17/12/18 |
| 净收入/身体更新 | -4 / -25.55 / 14/8/25 | 0 / -22.94 / 16/8/23 |
| 实际成功步 | 0 / 90.89 / 16/8/23 | 0 / 142.17 / 17/8/22 |
| 每千成功步收珠 | 0 / 1.68 / 21/8/18 | 0 / -3.19 / 19/8/20 |
| 每千成功步净收入 | 0 / 1.67 / 21/8/18 | 0 / -4.09 / 19/8/20 |
| 实际头位置覆盖 | 0 / 30.57 / 18/10/19 | 0 / 34.74 / 19/10/18 |
| 合法观测窗口覆盖 | 0 / 15.19 / 10/33/4 | 0 / 15.19 / 10/33/4 |
| 死亡资本 | 0 / -22.38 / 16/8/23 | 0 / -19.68 / 17/8/22 |
| 净保有资本 | 0 / -3.17 / 19/9/19 | 0 / -3.26 / 18/9/20 |
| Queen终局/截点长度 | 0 / 2.47 / 10/26/11 | 0 / 1.77 / 10/24/13 |
| Longest终局/截点 | 0 / -8.43 / 15/9/23 | -2 / -9.38 / 13/8/26 |
| Queen自主净更新 | 0 / 2.11 / 15/17/15 | 0 / 2.64 / 14/19/14 |
| Queen转出资本 | 0 / -1.04 / 14/19/14 | 0 / -0.15 / 16/20/11 |
| 分裂次数 | -1 / -11.17 / 13/10/24 | 0 / -10.38 / 14/11/22 |
| 唯一Longest死亡即时评分损失 | 0 / 1.47 / 3/43/1 | 0 / 1.89 / 3/43/1 |
| 唯一Longest死亡领先反转 | 0 / 0.04 / 2/45/0 | 0 / 0.04 / 2/45/0 |
| 领先回合数 | 0 / -12.11 / 8/31/8 | 0 / -0.85 / 2/42/3 |
| 最长连续领先回合 | 0 / -7.02 / 8/31/8 | 0 / 2.26 / 2/42/3 |

终局Queen存活25→28/47；Q长度中位数3→3，Longest中位数36→32。新增Queen死亡3、避免终局Queen死亡6，不能把净存活+3描述为没有新风险。全程净保有均差−3.17：净更新−25.55与死亡损失−22.38相抵后的真实资本差；共同前缀同样为−3.26。全程每千成功步收入效率均值略正，但前缀为负，实际覆盖正均值而中位数0；没有稳定普遍的保护／吞吐结论。

## 正式评分语境

按消灭→Queen→Longest→Total解释资本。固定47对的轴转移：消灭→消灭10、消灭→Longest2、Longest→消灭3、Longest→Longest9、Queen→Longest2、Queen→Queen13、消灭→Queen2、Longest→Queen4、Total→Total1、Queen→消灭1。Q关系20对均我方更长、18对均相等、3对我方更长→相等、6对相等→我方更长；没有“我方更长→对方更长”关系转移。

双方均存活、两臂Q相等且实际达到Longest判定的10对，相对Longest margin（own−rival）差值中位−3.5、均−12.5，2升3平5降。这是后果条件下的描述子集，不替代47主分母。两臂均Queen判定13对，Q margin差值中位0、均+2.38，1升7平5降；均值被正例拉高而多数变化并不正向。Q升级时绝对Longest下降可能是合理资本交换，必须分别保留。

正式轴或Queen关系改变的16对（其余31对仍保留主分母）：

| 地图/侧 | 正式轴 V5→候选 | 结果 V5→候选 | Q我方/对方 V5→候选 | L margin Δ |
| --- | --- | --- | --- | --- |
| Colosseum A | 消灭→Longest | W→W | 0/0→0/0 | -5 |
| Colosseum B | Longest→消灭 | W→L | 0/0→0/0 | -46 |
| arena A | 消灭→消灭 | W→W | 36/0→0/0 | -13 |
| arena B | 消灭→消灭 | W→W | 0/0→27/0 | 6 |
| australia B | Queen→Longest | W→W | 24/0→0/0 | 3 |
| autarky A | Queen→Longest | W→W | 7/0→0/0 | 2 |
| default B | 消灭→Queen | W→W | 8/0→5/0 | 19 |
| default_small A | Longest→消灭 | W→W | 0/0→0/0 | -29 |
| devil A | 消灭→Longest | W→W | 0/0→0/0 | -3 |
| devil B | Longest→消灭 | W→W | 0/0→0/0 | -17 |
| islands A | Longest→Queen | W→W | 0/0→44/0 | 2 |
| queen_of_spades B | Longest→Queen | W→W | 0/0→4/0 | -10 |
| slithery_fight A | Longest→Queen | W→W | 0/0→19/0 | -7 |
| stripes A | 消灭→Queen | W→W | 0/0→18/0 | 14 |
| stripes B | Queen→消灭 | W→W | 7/0→9/0 | 2 |
| unsw A | Longest→Queen | W→W | 0/0→16/0 | -3 |

## 新直接败局与死亡链

SAS Colosseum B由V5 r499 Longest获胜变为候选r82消灭判负。V5终局Q0/L45/T91，对手Q0/L3/T28；候选Q/L/T均0，对手Q0/L4/T77、31units。全程净收入差−481受提前终局影响，因此同时报告r82共同前缀：净收入−6、死亡损失+32、保有资本−38。新败局不能只用时长较短解释。

候选只有两条生命周期：Queen id1初始4，吃31、支付0、分裂转出2，r73死亡33；worker id16出生资本2，吃1、支付1，r82死亡2。全队初始4+food32−paid1−death35=0。Queen实际最后E步从(2,7)经门户到(13,7)，全球实际事后状态显示目标为敌id9第2节身体；该目标在原7×7视野外，官方死亡O。最后indicator为depth0/outside1、food0、direct/birth contact0，**并未证明helper在死亡当回合选择更深错误路线**。最后worker官方H死亡，fallback S；该死亡后的目标占有重建为空，不能据此否认头撞或指定碰撞者。直接原因与未知上游策略因果分开。

Colosseum B result SHA`187d4313d53e231c694fe2fbc3ba99b1a6ef56bba2b5942c9025a5315c0dcdc4`，raw SHA`34ef3826ad99d95fc22a2da813832c058433e6d1f20d9405ca434f20ca176925`。事后归因记录`test-results/oct7-certainty-colosseum-death-attribution.json` SHA`fbc63b512fb052c4d59dca26332be6aa6fae34c82d237752b11f94e876f2b9ce`；全局数据只用于死亡诊断，没有作为策略输入。

另一有效败局SAS Portals B未变：双方r499均Q3/L3，Total9<11判负，配对资源／资本差均0。本轮主Trauma两侧的配对汇总同样未变；原allocation Trauma r370局部排序证明不能冒充真实V5→certainty整局救活证明。

新增Queen终局死亡发生在SAS arena A、australia B、autarky A。arena A是V5 r74提前终局后、候选r103才H死，不是同一时间前缀退化；australia B r460 S死、双方均r499；autarky A r310 H死、双方均r499，最后正常MOVE为depth8。避免终局Q死亡的6对是arena B、islands A、queen_of_spades B、slithery_fight A、stripes A、unsw A；arena B更早终局，stripes A更晚终局，不能把不同长度的生存暴露视作同一因果效果。

## 地图与资本解释

资源及保护代价不是门户单图效应。以下均保留在主47，无倒选分母：

- Big Empty A两臂r499，Q28→92、L126→95，净收入−18、死亡资本+100、保有−118。Queen首项增强，不能因Longest下降直接判更弱；B侧Q38→21、L140→120且保有−133，又是相反资产方向。
- Maze A/B两臂Q均0，Longest157→63／152→125，实际Longest判定；A净收入+166且保有+102，说明更高总资源仍可能没有保留评分champion，B保有+4也未挽回champion下降。
- Schooltime A/B净收入+89／−128、L169→83／191→141；双方我方Q3、对手Q0，仍是Queen首项胜利。不能把这里的绝对L下降混入实际Longest败局。
- Slithery A/B净收入−615／−238，死亡资本−665／−301，保有+50／+63；A Q0→19。少吃也少死而留下更多资本，不能只按收入负值称为饥饿。
- Colosseum B新消灭败局是明确全局失败；Portals A/B配对指标均0。保护改善与新资本风险跨多个地图存在，尚无一项总体稳定的方向。

## continuation聚合证书边界

最大`Future.depth`及匹配的`next_food`来自被选中的深分支，但`outside/portal/exhausted`在分支间OR。`depth6/outside1`只表示候选级已搜索前缀最大6及某分支未知，不证明同一条路走6步后接到未知出口。新增生产函数构造把“有限已知6步”和“立即未知0步”置于不同支，返回同一aggregate，官方PASS；原冻结helper、源及proof均不修改。见`tests/certainty_branch_semantics_test.cpp`，stage`bf19c5477d24451938f440a8`，源码SHA`290cd394910f2565c04f4dd12f086433addaeb7dc55ee5e2895e8b812f0479b1`，log SHA`9d8cd1c9d47d4223bb03e8407c5f6613260fdf8c2c1cd8dd0105b375e4414aad`。

这不推翻Trauma同状态WSSS→S、0→6的排序观测；它限制了“更长前缀连接未知出口”这个尚未证明的解释。深度从动作终点计数，偏好短MOVE可能损失当前免费步吞吐；beam/top8之前筛候选也未改。所有这些均为可检验风险，当前完整数据没有证明哪个上游机制独自造成新败局。

## 数据来源与限制

严格比较`test-results/oct7-certainty-discovery-compare.json` SHA`94b8065964edeeeaf8f50036a3f9cf195cb5179f0fe765b01ba29799c6aebc30`；评分context SHA`f0a35f2b2c5353fc1b8342176a9077cea0fb19f5a04b98f4bcabb32114ab3fbf`。每对result/replay/candidate/environment哈希由比较记录绑定；冻结比较器SHA`62546124105aa0a075a1c21eac9f0f23d51a5f218ba5b738b6048e10fd638250`，评分工具SHA`19834f94e080eada024f5dc9bce45e7fb28f32828684e364323203e101af2eec`。重新核查26个冻结源文件、源快照与WASM均一致，原Trauma proof不变。

Root首次run调用在freeze编译结束前，missing-freeze预检失败，0 job；随后正式freeze确认后才启动完整88。这是调用顺序问题，不计入88败局、runtime失败或删掉的比赛。证据重建及新增语义检查命令没有启动比赛、上传或运行下载源码；本轮Root实际运行88比赛另外明确计数。弱公开基准、同一已见discovery和条件子集不能证明天梯升级或换算Elo；未开启留出且未上线验证，不以deadline豁免采用门槛。

## 全部47有效配对资产附表

各格为V5→候选，net差为候选−V5。正式结果保留先后手及地图，不按结果挑选。

| 对手/地图/侧 | r终局 | 正式结果 | Q | L | T | 全程net Δ | 前缀net Δ |
| --- | --- | --- | --- | --- | --- | --- | --- |
| official-murder/Colosseum/A | 53→53 | W/消灭→W/消灭 | 36→35 | 36→35 | 36→35 | 1 | 1 |
| official-murder/queen_of_spades/A | 323→273 | W/消灭→W/消灭 | 5→17 | 12→17 | 73→68 | -4 | 8 |
| official-murder/queen_of_spades/B | 186→186 | W/消灭→W/消灭 | 0→0 | 20→20 | 37→37 | 0 | 0 |
| sas-987/Colosseum/A | 396→499 | W/消灭→W/Longest | 0→0 | 29→26 | 140→111 | -78 | -260 |
| sas-987/Colosseum/B | 499→82 | W/Longest→L/消灭 | 0→0 | 45→0 | 91→0 | -481 | -6 |
| sas-987/arena/A | 74→103 | W/消灭→W/消灭 | 36→0 | 36→23 | 80→70 | 68 | -7 |
| sas-987/arena/B | 105→36 | W/消灭→W/消灭 | 0→27 | 21→27 | 69→77 | -81 | 23 |
| sas-987/australia/A | 499→499 | W/Longest→W/Longest | 0→0 | 66→55 | 564→604 | 61 | 61 |
| sas-987/australia/B | 499→499 | W/Queen→W/Longest | 24→0 | 41→43 | 557→524 | -31 | -31 |
| sas-987/autarky/A | 499→499 | W/Queen→W/Longest | 7→0 | 37→40 | 202→173 | -43 | -43 |
| sas-987/autarky/B | 499→499 | W/Queen→W/Queen | 7→7 | 36→34 | 221→188 | -23 | -23 |
| sas-987/big_empty/A | 499→499 | W/Queen→W/Queen | 28→92 | 126→95 | 1320→1202 | -18 | -18 |
| sas-987/big_empty/B | 499→499 | W/Queen→W/Queen | 38→21 | 140→120 | 1131→998 | -207 | -207 |
| sas-987/default/A | 499→499 | W/Queen→W/Queen | 9→6 | 89→32 | 230→204 | 65 | 65 |
| sas-987/default/B | 434→499 | W/消灭→W/Queen | 8→5 | 31→53 | 161→213 | 149 | 76 |
| sas-987/default_small/A | 499→302 | W/Longest→W/消灭 | 0→0 | 45→14 | 97→92 | -47 | 55 |
| sas-987/default_small/B | 154→124 | W/消灭→W/消灭 | 8→7 | 16→18 | 66→72 | -11 | 4 |
| sas-987/devil/A | 309→499 | W/消灭→W/Longest | 0→0 | 32→32 | 190→201 | 489 | -28 |
| sas-987/devil/B | 499→362 | W/Longest→W/消灭 | 0→0 | 49→29 | 240→205 | -176 | 94 |
| sas-987/dilemma/A | 499→499 | W/Queen→W/Queen | 15→14 | 15→14 | 45→45 | -2 | -2 |
| sas-987/dilemma/B | 499→499 | W/Queen→W/Queen | 7→7 | 11→11 | 43→43 | 0 | 0 |
| sas-987/islands/A | 499→499 | W/Longest→W/Queen | 0→44 | 47→49 | 428→491 | -5 | -5 |
| sas-987/islands/B | 145→145 | W/消灭→W/消灭 | 21→21 | 30→30 | 170→170 | 0 | 0 |
| sas-987/maze/A | 499→499 | W/Longest→W/Longest | 0→0 | 157→63 | 228→330 | 166 | 166 |
| sas-987/maze/B | 499→499 | W/Longest→W/Longest | 0→0 | 152→125 | 247→251 | -22 | -22 |
| sas-987/portals/A | 499→499 | W/Longest→W/Longest | 3→3 | 5→5 | 8→8 | 0 | 0 |
| sas-987/portals/B | 499→499 | L/Total→L/Total | 3→3 | 3→3 | 9→9 | 0 | 0 |
| sas-987/queen_of_spades/A | 442→480 | W/消灭→W/消灭 | 10→25 | 16→26 | 89→134 | -67 | -94 |
| sas-987/queen_of_spades/B | 499→499 | W/Longest→W/Queen | 0→4 | 32→22 | 117→130 | -9 | -9 |
| sas-987/schooltime/A | 499→499 | W/Queen→W/Queen | 3→3 | 169→83 | 516→519 | 89 | 89 |
| sas-987/schooltime/B | 499→499 | W/Queen→W/Queen | 3→3 | 191→141 | 622→549 | -128 | -128 |
| sas-987/slithery_fight/A | 499→499 | W/Longest→W/Queen | 0→19 | 39→32 | 348→398 | -615 | -615 |
| sas-987/slithery_fight/B | 499→499 | W/Longest→W/Longest | 0→0 | 68→61 | 374→437 | -238 | -238 |
| sas-987/stripes/A | 246→499 | W/消灭→W/Queen | 0→18 | 20→38 | 43→79 | 58 | -17 |
| sas-987/stripes/B | 499→155 | W/Queen→W/消灭 | 7→9 | 10→9 | 81→17 | -150 | 4 |
| sas-987/stronghold/A | 499→499 | W/Queen→W/Queen | 14→3 | 34→26 | 149→134 | 14 | 14 |
| sas-987/stronghold/B | 499→499 | W/Longest→W/Longest | 0→0 | 15→17 | 104→114 | 8 | 8 |
| sas-987/tower_defense/A | 499→499 | W/Longest→W/Longest | 0→0 | 43→30 | 120→89 | -39 | -39 |
| sas-987/tower_defense/B | 499→499 | W/Longest→W/Longest | 0→0 | 7→7 | 25→25 | 0 | 0 |
| sas-987/trauma/A | 499→499 | W/Queen→W/Queen | 8→8 | 14→14 | 38→38 | 0 | 0 |
| sas-987/trauma/B | 499→499 | W/Queen→W/Queen | 15→15 | 15→15 | 32→32 | 0 | 0 |
| sas-987/trophy/A | 431→413 | W/消灭→W/消灭 | 0→0 | 50→75 | 287→242 | -97 | -72 |
| sas-987/trophy/B | 383→437 | W/消灭→W/消灭 | 0→0 | 51→59 | 290→280 | 65 | -20 |
| sas-987/unsw/A | 499→499 | W/Longest→W/Queen | 0→16 | 71→69 | 732→826 | 78 | 78 |
| sas-987/unsw/B | 499→499 | W/Longest→W/Longest | 0→0 | 57→83 | 609→631 | 94 | 94 |
| sas-987/weakhold/A | 499→499 | W/Queen→W/Queen | 4→4 | 34→37 | 91→97 | -6 | -6 |
| sas-987/weakhold/B | 499→499 | W/Queen→W/Queen | 4→3 | 34→44 | 97→106 | -28 | -28 |
