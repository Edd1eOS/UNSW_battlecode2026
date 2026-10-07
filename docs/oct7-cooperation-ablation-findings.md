# Oct7 合作两功能消融：终局与完整行为复核

出口保护egress-only与门户到达风险arrival-only各88场完整发现集已经到齐。**arrival-only不等于完整合作版，egress-only也不等于V5**：官方完整动作、身体update、出生、死亡、资源及轮次事件逐项比较，两个比较各只有80/88场完全相同。不能因为正式胜负总数相同就认为出口分支从未改变选择。

方法延续[预声明计划](oct7-hypothesis-validation-plan.md)：各版分别对同外部对手、22地图、种子`2026100701`及A/B侧，没有自家版本互战。拆功能是开发消融，已看过的发现集不成为新独立强度样本。完整合作报告见[合作v1](oct7-cooperation-discovery-findings.md)。

## 独立结果与主配对分母

| 范围 | V5 | egress-only | arrival-only | 完整合作 |
| --- | --- | --- | --- | --- |
| 全部正式88 | 87W1L | 87W1L | 87W1D | 87W1D |
| 各自双方运行有效 | 47：46W1L | 47：46W1L | 46：45W1D | 46：45W1D |
| 各自与V5有效交集 | — | 47 | 46 | 46 |
| 交集Q终局存活：V5→候选 | — | 25→25 /47 | 24→25 /46 | 24→22 /46 |
| 交集Q中位长度：V5→候选 | — | 3→3 | 3→3 | 3→0 |
| 交集L中位：V5→候选 | — | 36→36 | 35→37.5 | 35→37.5 |

两份主报告均88回放/初始/地图/环境/终局核验、0缺失、0冲突、0分析失败；各自有效交集gross均可证。运行/基础设施/90M余量失败均0。无效对手的所有正式结果保留且资源不自动归零。分母不同的两列不能直接当同样47个样本相减。

| 候选源包与WASM SHA256 | 身份 |
| --- | --- |
| egress-only源包 | `c7af166ae53adc3118936d6e43a031d7598e56c36fb329dbadba00104029b9d9` |
| egress-only WASM | `c9d0e1c1727fcd47b78fc555377009a589af66386b0edfc8aec091c6bbb6c19a` |
| arrival-only源包 | `72c6f6fe8436d8e2c547f9b2cb9a71eeab6f2fa07d466f04c2bb376055b3f5a1` |
| arrival-only WASM | `b92d9a2c8f2cfc08f057b7dbcd3f30a09c17d31adf8bbdb1d38468c3025020ce` |

每场地图/对手/原raw/result与依赖哈希均保留。V5与完整合作身份见各自主报告。

## 整场与共同前缀的资源权衡

以下为候选减V5的配对均差；所有列的配对中位差为0。整场用各自终局，共同前缀用较早终局的同一完整轮末。支付和死亡是成本，分裂守恒不算收入。

| 指标 | egress整场（47） | egress前缀 | arrival整场（46） | arrival前缀 | 完整合作整场（46） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 收珠 | +3.87 | +2.79 | −4.83 | −0.70 | −3.00 |
| 支付 | −0.45 | −0.60 | −2.96 | −2.46 | −3.04 |
| 净收入 | +4.32 | +3.38 | −1.87 | +1.76 | +0.04 |
| 死亡带走的长度 | +4.17 | +3.91 | −6.24 | −2.67 | −2.80 |
| 保有总长 | +0.15 | −0.53 | +4.37 | +4.43 | +2.85 |
| Queen长度 | −0.62 | −0.64 | +1.98 | +1.83 | +0.65 |
| Longest | −0.91 | −0.87 | +2.61 | +2.93 | +1.98 |
| Queen自主净update | −0.02 | −0.04 | −0.70 | −0.59 | −0.87 |
| Queen分裂转出 | −0.04 | −0.04 | −2.85 | −2.54 | −3.04 |

egress的整场净收入47对中3正42零2负，新增收入多数被新增死亡吞掉；保有增量总和仅7。arrival净收入46对中10正19零17负，死亡成本7增20同19减、保有15增20同11减。它减少了部分损失并增加Q保有，但没有证明普遍资源吞吐提升；Q自主净update均差仍负，不能称Q增长算法成功。

egress五个有效场景的资源或Q/L发生变化：Big Empty B净收入+57但Queen38→0，Slithery B净收入+139且Queen0→8，Default B净收入+30且Queen8→13，Stronghold A/B净收入−19/−4。相同的25/47存活掩盖了一次新增和一次避免死亡。arrival在Big Empty B保留Queen38，而完整合作失去该Queen；这是需要局部解释的正例，不能推广为全局保命保证。

Portal两侧arrival与完整合作的正式变化相同：A基线Longest胜→draw，B基线Total败→Longest胜；两侧Queen自主food/paid/net均0。egress两侧与V5轨迹相同，因此Portal收益不是出口保护机制兑现或Queen增长证据。

## 第一处实际选择分岔

arrival与完整合作80场gameplay相同、8场不同；包含诊断字符串的normalized全事件76场相同。原二进制raw SHA全部不同，并不等于全部行为不同：例如相同轨迹的Colosseum A，replay头部botId分别为`Generalist Cooperation V1`和`Cooperation Arrival Only V1`，动作与资源完全相同。逐事件比较没有丢弃动作、身体、回合、SPLIT、死亡或吃珠，只排除indicator/log文本。

以下是8个首个不同的官方dragonAction；“完整→arrival”是实际已执行的请求动作，不能将请求步数直接解释为实际付费。分岔之前的gameplay相同，但后续收益损失仍包括队友/对手响应，不能归因于一条标量罚分。

| 外部对手／地图／侧 | round／actor | 完整合作→arrival-only |
| --- | --- | --- |
| sas-987／Autarky A | r387／356 | MOVE S → S,S,E,E,E,S |
| sas-987／Big Empty B | r343／111 | MOVE S → S,S,S,W,W |
| sas-987／Queen of Spades B | r323／21 | SPLIT2 → MOVE S |
| sas-987／Slithery Fight A | r467／1402 | MOVE E → E,E |
| official-murder／Autarky A | r387／301 | MOVE S → S,S,E,E,E,S |
| official-murder／Devil B | r164／11 | MOVE N → N,E,E |
| official-murder／Islands A | r166／8 | MOVE W → W,N,W,N,N |
| official-murder／Slithery Fight B | r446／486 | MOVE E,N → E |

egress对V5也有8个gameplay分岔：official-murder Devil B、Stronghold A/B，以及sas-987 Big Empty B、Default B、Slithery B、Stronghold A/B。这两套分岔场景不同，说明组件会因其他政策改变前序身体/观察而以不同方式激活，不能把单组件delta简单相加预测组合版。

## 评分层级与采用边界

消灭优先，随后Queen、Longest、Total；Queen不等时不以Longest下降单独否定。两臂Q相等、两队存活且Longest都参与的subset，egress16对相对Longest margin均差+0.125、中位0（1升15同）；arrival12对均差−0.83、中位0（3升7同2降）。两臂均Queen主判定的subset，egress15对Q margin均差−0.27，arrival13对+1.69。subset按终局形成，仅解释评分，不替换主47/46分母。

这些发现支持继续研究到达风险造成的损失抑制，不支持成熟对手强度或Elo提升；arrival比完整合作少失Queen的局部观测也不等于独立采用通过。新最终候选需要冻结后新未开留出和真实对手确认。Active参照仍只有17/88且预算停止，不阻延或替代这些完整V5主分析。

## 证据文件

| 报告（test-results） | SHA256 |
| --- | --- |
| `oct7-egress-discovery-compare.json` | `cb52524837708a43d15ca1992bc90707e7a52fd89a76461d1f2ac9a87ec77fd9` |
| `oct7-arrival-discovery-compare.json` | `be1f25e0f0bb203b28840af9a00dccf7e79f8c07820b81a0997a82c8d7477863` |
| `oct7-arrival-vs-coop-event-equivalence.json` | `9204678fc29adcfc88b45fcb1ef2fa3b0ada15a2aa2f793ef900c209141f775c` |
| `oct7-egress-vs-v5-event-equivalence.json` | `49334fa1fdd2f74f40a699b22c6e145df5c311fb6ebf12a3d9ac7e1e9ea60860` |
| `oct7-arrival-coop-first-choices.json` | `9bd644d357e2c33f65836d15fa285f7f7ddd7f61e3af444f3425bf1bf5a1bcf6` |

全部case绑定原始SHA与冻结身份，评分context两份均0issues；原raw不入git。冻结比较器和候选未改，29项离线检查已通过。证据导入与重建不会开启比赛、上传或执行下载源码；Root独立比赛才计入实际完成数。

## 正式axis及Queen关系变化全表

所有其他样本仍在每份88行JSON中，不因轴变化筛掉；“Q相等”仅指同一臂双方Queen是否相等。

| 候选／范围 | V5正式axis | 候选正式axis |
| --- | --- | --- |
| egress／全部88 | 消灭32、Queen26、Longest29、Total1 | 消灭31、Queen27、Longest29、Total1 |
| egress／有效交集 | 消灭14、Queen16、Longest16、Total1 | 消灭13、Queen17、Longest16、Total1 |
| arrival／全部88 | 消灭32、Queen26、Longest29、Total1 | 消灭31、Queen27、Longest29、全轴平手1 |
| arrival／有效交集 | 消灭13、Queen16、Longest16、Total1 | 消灭11、Queen17、Longest17、全轴平手1 |

### egress：全部3个有效配对评分语境转移

| 对手／地图／侧 | V5 axis；Q相等；Q差；L差 | 候选axis；Q相等；Q差；L差 |
| --- | --- | --- |
| sas-987／big_empty／B | Queen；否；+38；+128 | Longest；是；+0；+98 |
| sas-987／default／B | 消灭；否；+8；+31 | Queen；否；+13；+25 |
| sas-987／slithery_fight／B | Longest；是；+0；+64 | Queen；否；+8；+56 |

评分附表SHA`ee73e5a51b6fe77e5eb7a05947ea98a4008cb347cbae472b978fe734938ce36e`；0issues。

### arrival：全部15个有效配对评分语境转移

| 对手／地图／侧 | V5 axis；Q相等；Q差；L差 | 候选axis；Q相等；Q差；L差 |
| --- | --- | --- |
| sas-987／Colosseum／B | Longest；是；+0；+42 | 消灭；是；+0；+45 |
| sas-987／australia／A | Longest；是；+0；+63 | Queen；否；+28；+47 |
| sas-987／autarky／A | Queen；否；+7；+34 | Longest；是；+0；+41 |
| sas-987／default／B | 消灭；否；+8；+31 | Longest；是；+0；+91 |
| sas-987／portals／A | Longest；是；+0；+2 | 全轴平手；是；+0；+0 |
| sas-987／portals／B | Total；是；+0；+0 | Longest；是；+0；+2 |
| sas-987／queen_of_spades／A | 消灭；否；+10；+16 | Longest；是；+0；+8 |
| sas-987／queen_of_spades／B | Longest；是；+0；+29 | Queen；否；+16；+29 |
| sas-987／slithery_fight／A | Longest；是；+0；+35 | Queen；否；+7；+45 |
| sas-987／stripes／A | 消灭；是；+0；+20 | 消灭；否；+27；+27 |
| sas-987／stripes／B | Queen；否；+7；+7 | Longest；是；+0；+21 |
| sas-987／stronghold／A | Queen；否；+14；+30 | Longest；是；+0；+39 |
| sas-987／stronghold／B | Longest；是；+0；+12 | Queen；否；+4；+12 |
| sas-987／trophy／A | 消灭；是；+0；+50 | Longest；是；+0；+67 |
| sas-987／trophy／B | 消灭；是；+0；+51 | 消灭；否；+14；+53 |

评分附表SHA`de058cecd10ef7b8742f5c7a546a46ff1194810d2cacd54e4627e4cef5070636`；0issues。
