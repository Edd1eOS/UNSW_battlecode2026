# Oct7 合作保出口v1：完整发现集

合作版完整88场于05:12前到齐，严格报告生成于2026-10-07 05:12:17 UTC。两臂46个有效配对的保有总长均差+2.85、整场净收入均差+0.04、共同前缀净收入+3.67；Queen终局存活24→22，长度中位3→0。当前没有证明“普遍Queen保命与增长”这一采用命题；保留局部有效机制及副作用，不能凭正式败局消失宣称整体成功。

两版本分别对相同冻结外部对手、22地图、种子`2026100701`及A/B侧比赛，没有自家版本互战。预声明方法见[本轮计划](oct7-hypothesis-validation-plan.md)。可见出口、门户到达及必要救援的局部条件可以经构造测试证明；全场后果仍须完整实战账与评分层级核验。

## 身份与不同分母

| 范围 | 冻结V5 | 合作v1 |
| --- | --- | --- |
| 全部正式88场 | 87W1L | 87W1D |
| 各自双方运行有效，独立分母 | 47：46W1L | 46：45W1D |
| 有效交集配对 | 46：45W1L | 46：45W1D |
| 交集Queen终局存活 | 24/46 | 22/46 |
| 交集Queen中位长度 | 3 | 0 |
| 交集Longest中位 | 35 | 37.5 |
| 我方运行／基础设施／预算余量失败 | 0 / 0 / 0 | 0 / 0 / 0 |

88初始/地图/环境/回放/终局核验通过，46双方eligible且gross可证，0缺失、0冲突、0分析失败。唯一资格变化是official-murder Colosseum A：基线对手无无效动作，合作对手出现1次；该正式win仍保留，资源不能自动记0。其余42对不作可靠运行有效胜场。

基线源包`39cbf8c74f2d514ea5c0cb0b3b46fa16ef554486863427f0ebb8966f73b4c7fa`，WASM`7b2dd8a38996a93c5c3bf45526d74a366409072916000b9d2c169200d4fed40b`。合作源包`e4d87b1f2127aa304b01de18493d7072e027830c274db9abef77b7fc8331ad92`，WASM`e1a720e3f8faf6d0504f0b9a6d58910cb0b59cc5dd10a9eb444dfd73d4cce8f7`。各场依赖及raw哈希绑定于完整报告。

## 全程资源与评分资本

差值为合作减V5；完整比赛使用各自终局，共同前缀是较早终局的同一完整轮末。两组终局中位数之差不是配对中位差。死亡与支付增量为成本，分裂继承不算收入。

| 指标（46对） | 整场中位差 | 整场均差 | 整场正／零／负 | 前缀均差 |
| --- | ---: | ---: | --- | ---: |
| 收珠 | 0 | −3.00 | 11 / 17 / 18 | +1.13 |
| 支付 | 0 | −3.04 | 7 / 21 / 18 | −2.54 |
| 净收入 | 0 | +0.04 | 11 / 18 / 17 | +3.67 |
| 每千成功步净收入 | +0.09 | +7.02 | 23 / 17 / 6 | +6.95 |
| 已执行头位置并集 | 0 | −4.93 | 13 / 21 / 12 | −1.26 |
| 7×7 turnStart窗口并集 | 0 | −2.13 | 8 / 34 / 4 | −2.13 |
| 死亡带走的长度 | 0 | −2.80 | 9 / 20 / 17 | +0.76 |
| 保有总长 | 0 | +2.85 | 15 / 19 / 12 | +2.91 |
| Queen长度 | 0 | +0.65 | 9 / 27 / 10 | +0.50 |
| Longest | 0 | +1.98 | 19 / 19 / 8 | +2.30 |
| Queen自主净update | 0 | −0.87 | 11 / 22 / 13 | −0.76 |
| Queen分裂转出 | 0 | −3.04 | 8 / 24 / 14 | −2.74 |

完整Queen收珠均差−1.02、付费−0.15；不能从终局Queen均长增加0.65写成自主增长改善。Queen死亡带走的长度均差+1.52，新增死亡6、避免4，更多保有可来自其他单位。收入每步比值有所改善，但全队净收入没有稳定增加；窗口并集不代表有用可达食物。46对净收入差总和+2、死亡差−129、保有差+131，严格守恒。

## 正式变化与新增Queen死亡

运行有效配对唯一正式win/loss/draw变化是sas-987 Portals：A由Longest胜变draw，r499两队Q3/L3/T9；B由Total败变Longest胜，我方Q3/L5/T8、对手Q3/L3/T9。两侧Queen吃珠/付费/自主净update均0，普通split均0；A净收入−2、死亡−3，B净收入+2、死亡+3，不能把结果变化解释为Queen增长。

以下6局基线Queen终局存活而合作死亡，均是直接事件及最后动作，不能从这些标签单独推断根本拥堵因果。

| 地图／我方侧 | 合作Queen死亡 | 正式评分语境与时间边界 |
| --- | --- | --- |
| Autarky A | r404 W、长3，loss_min fallback N | Queen7→0；Queen胜→Longest胜，Q主优势损失但仍正式win |
| Big Empty B | r485 H、长33，正常MOVE S，`direct_contact=1 possible_birth_contact=1` | Queen38→0；Queen胜→Longest胜。全队净收入+57、死亡多104、保有−47；不能凭收入增加通过保命命题 |
| Default B | r435 O、长2，loss_min fallback N | 基线r434已消灭获胜，合作到r499。新增Queen死亡在共同前缀之后，不是同时间存活退化；终局改为Longest胜且保有+128 |
| Queen of Spades A | r408 W、长2，loss_min fallback N | 基线r442消灭胜、合作r499消灭胜。Q10→0并不改变消灭主判定；作为资本代价保留 |
| Stripes B | r327 W、长2，loss_min fallback N | Queen7→0；Queen胜→Longest胜，收入−27、保有−2 |
| Stronghold A | r95 W、长2，loss_min fallback N | Queen14→0；Queen胜→Longest胜，收入−18、保有−11 |

4个避免终局Queen死亡的场景为Australia A、Stripes A、Stronghold B、Trophy B。Stripes A合作在r208消灭胜、基线到r246，Trophy B在r300消灭胜、基线到r383，未来若比赛继续的风险未知。Australia A Queen0→28同时净收入+29，是正例；Stronghold B Queen0→4但Queen吃食29→8，更多保留而非更多吞吐。所有例子保留完整与共同前缀，不将早结束的死亡机会当作同样时长。

## 可用发现与限制

同图换边每图只有一个新种子，结果有关联。Maze两侧净收入均差+50.5、保有+43且两臂Longest判定，值得进一步检验；Autarky两侧净收入−52.5，Big Empty净收入+28.5但Queen均长−19并增加死亡成本。这是机制分层，不根据有利图重选主分母。合作不能仅因“对手仍弱且赢了”采用；H3的Queen保命命题没有全场证据支持，局部出口约束也不等于全局通行保证。

严格比较报告`test-results/oct7-cooperation-discovery-compare.json` SHA`ac6efa53c43066ed04e43cbd129c2e6612f39d630888e6ea12d51eb314c3c1ff`；逐Queen变更案例及原始身份绑定在`oct7-cooperation-queen-change-cases.json`。原始回放不入git。冻结比较器与旧账本均未修改；29项离线检查通过（比較12、家族11、评分6），包含真实官方回放解码与严格账集成。本页是发现集，不是新留出、天梯强度或Elo证明。

证据导入与重建命令不会开启比赛、上传或执行下载源码；Root独立运行并保留实际完成范围。离线全图信息只用于审计，不能进入候选的合法视野决策。

## 终局评分语境附表

消灭优先，随后Queen、Longest、Total。只有两队仍有龙且Q相等，Longest才参与；以下subset按结果形成，仅解释计分，不替换46主配对分母或预声明采用门槛。

| 范围 | 基线正式axis | 合作正式axis | 两臂Longest均参与 |
| --- | --- | --- | ---: |
| 全部正式88对 | 消灭32、Queen26、Longest29、Total1 | 消灭31、Queen24、Longest32、全轴平手1 | 23 |
| 运行有效46对 | 消灭13、Queen16、Longest16、Total1 | 消灭11、Queen14、Longest20、全轴平手1 | 14 |

两臂Longest均参与的14对：相对Longest margin差中位0、均值+0.93，5升7同2降。两臂Queen主判定的12对：Queen margin差中位0、均值+1.83，3升5同4降。Queen正例和消灭胜转移保留，不将绝对Longest均差当作全部强度判断。

| 有效配对axis转移 | 对数 |
| --- | ---: |
| 消灭→消灭 | 10 |
| Longest→消灭 | 1 |
| Longest→Queen | 2 |
| Queen→Queen | 12 |
| Queen→Longest | 4 |
| 消灭→Longest | 3 |
| Longest→Longest | 12 |
| Longest→全轴平手 | 1 |
| Total→Longest | 1 |

| 地图／侧（Q关系或axis变化全部14对） | 基线axis；Q相等；Q差；L差 | 合作axis；Q相等；Q差；L差 | 正式结果 |
| --- | --- | --- | --- |
| Colosseum／B | Longest；是；+0；+42 | 消灭；是；+0；+45 | win→win |
| australia／A | Longest；是；+0；+63 | Queen；否；+28；+47 | win→win |
| autarky／A | Queen；否；+7；+34 | Longest；是；+0；+25 | win→win |
| big_empty／B | Queen；否；+38；+128 | Longest；是；+0；+98 | win→win |
| default／B | 消灭；否；+8；+31 | Longest；是；+0；+91 | win→win |
| portals／A | Longest；是；+0；+2 | 全轴平手；是；+0；+0 | win→draw |
| portals／B | Total；是；+0；+0 | Longest；是；+0；+2 | loss→win |
| queen_of_spades／A | 消灭；否；+10；+16 | Longest；是；+0；+8 | win→win |
| stripes／A | 消灭；是；+0；+20 | 消灭；否；+27；+27 | win→win |
| stripes／B | Queen；否；+7；+7 | Longest；是；+0；+21 | win→win |
| stronghold／A | Queen；否；+14；+30 | Longest；是；+0；+39 | win→win |
| stronghold／B | Longest；是；+0；+12 | Queen；否；+4；+12 | win→win |
| trophy／A | 消灭；是；+0；+50 | Longest；是；+0；+67 | win→win |
| trophy／B | 消灭；是；+0；+51 | 消灭；否；+14；+53 | win→win |

完整88行评分附表SHA`30e41d3e9452ad931f82ae92155b1693cb202fe4f7df6db39dc35c492adda5ca`，0issues；只读工具`19834f94e080eada024f5dc9bce45e7fb28f32828684e364323203e101af2eec`，冻结比较器未改。

## Active v14的补充部分参照

Active只完成17/88，停止于90M预算余量检查，剩71缺配，见[提前停止说明](oct7-active-v14-partial-reference.md)。合作对Active的补充也只有17匹配、9双方运行有效/gross可证，其中1对Active预算余量失败，8对预算通过；不替代完整V5主比较。所有缺配与预算flag保留，未完成71场不能记为draw、胜或分析失败。
补充报告`test-results/oct7-cooperation-vs-active-partial.json` SHA`3a80350c78dea704573fb064b3d43d6ca91adeccf5926487e762ffdfb5ed8eff`，actual_scope=partial。没有从17场另作全图强度结论。
