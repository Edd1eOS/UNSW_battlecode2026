# Oct7 Active v14参照：提前停止的17场

该补充面板预登记88场，实际只完成17场，剩余71场pending。冻结driver因90M points预算余量检查失败自动停止；Root没有重启、跳过或补做。它是开发参照，不替代完整V5主基线，也不能作为完整88场基准或新候选强度验收。

全部17正式结果为17W；其中11场双方运行有效，6场有对手运行无效。11中有1场预算余量不通过，因此同时满足运行有效及90M余量的独立分母是10。我方实际运行错误0、基础设施失败0、预算余量失败1；“余量失败”不等于实际引擎超时。

停止的第17场为`discovery/sas-987/big_empty-2026100701-A`。实际我方peak **99,736,301 points**、720,896 bytes；高于90M预声明余量线，仍低于100M实际动作预算。r499 roundLimit结束，我方Q0/L44/T931，对手Q0/L4/T147，正式Longest胜。双方invalid runtime事件均0，`runtime_errors=[]`；我方死亡原因161 head-to-head、125 other-body、1 self，没有timeout死亡。原始result与完整回放已严格重建，不能将这次停止写成超时判负。

源包`7b34540202f70a60c6ddaacfdfe9ab19cc4e6aec222e3d11f6459b415b5fc4ee`，WASM`4d4f0ddc5e73a0340db5b4835f909e708da83273d2f45df8f6a46eeec830d583`，freeze04:59:51 UTC。这是本地面板重编译身份，官方Active v14来源证明仍保留在此前导入证据，不能用重编译WASM冒充官方平台WASM字节证明。

## 与完整V5的部分配对

冻结比较器保留17匹配、17回放/环境/初始/终局核验通过、71缺配、0冲突、0分析失败，`actual_scope=partial`。其中9对双方运行有效且gross账可证；预算余量flag另列，9中含停止那场，只有8对同时预算通过。比较器的历史runtime eligibility定义没有为本参照改动，**不能把9称作9个预算安全配对**。

9对描述性整场差值（Active减V5）为：净收入中位−100／均值+1、死亡长度中位+69／均值+114.78、保有总长中位−83／均值−113.78、Queen长度中位−3／均值−10.56。它们既包括预算失败场，又只覆盖计划顺序的开头，不能推广至其余地图或当作全场新版本优越性证明。两臂均Queen相等且两队存活、Longest参与的只有1对，相对Longest margin差−42，样本过少不做概括。

停止是预算规则触发的非随机截断。虽然没有按胜负选17场，也不能把已完成的有利开头当成无偏完整面板。71个原计划缺配键逐项保留，不换种子补齐，也不与V5完整88的胜率简单相减。

## 可复现来源

| 文件 | SHA256 |
| --- | --- |
| `test-results/oct7-active-v14-discovery-compare-partial.json` | `7f1f436c36d34893ed4ac93c11a338ef37afed18cfd3256425a202a8d7031210` |
| `test-results/oct7-active-v14-scoring-context-partial.json` | `6e80b8617ba21a0e48bd17f228d47793b3bedc58818c02e1d8cf8040a3ef6f23` |
| 停止场raw replay | `8255a3ea83a32c85ceadfdf8ce2d8e7c605e911b3cef6dea7f320572cdbaa587` |
| 停止场原始log | `c0ca089e8116569348f7f07b650d62b4561d3ff88774b17377e8340bc9af3855` |

完整报告保留所有正式结果、预算flag、单侧无效和缺配键。评分语境报告0issues，区分消灭／Queen／Longest／Total。冻结比较器SHA`62546124105aa0a075a1c21eac9f0f23d51a5f218ba5b738b6048e10fd638250`及只读评分工具`19834f94e080eada024f5dc9bce45e7fb28f32828684e364323203e101af2eec`均未改动。离线导入与重建不会开启比赛或上传；Root独立运行的17场才是实际完成范围。
