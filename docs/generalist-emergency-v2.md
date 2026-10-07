# Emergency V2：远端起点证据修复

独立复制冻结 Emergency V1，候选仅 `emergency.hpp` 一处变化：两层出生/亲体续路搜索中，起点不在当前 `ct.tiles` 时返回 `unknown=true`。历史 Atlas 知道地形仍不足以满足旧步进模拟器的输入契约；不再将它的直接失败误当没有移动出口。已知当前封闭、未解析门、预算耗尽各自的原语义不变。

没有改变分裂大小、普通扩张、食物/支付、评分常数、Queen 保长、最后单位保护或全局排序。长子体出生免费额度仍为官方 `ceil(起始L/4)`；这里只搜至少一条免费首步。亲体/子体两 L2 且两边均无未知首步的原硬排除条件保持。其他龙会动、长体可再分裂和两层模型不能保证未来执行这些限制继续保留。

V1 的 88 场证据保留：14 次报告子体无 MOVE 却有出生轮实际成功 MOVE（其中有效配对 3 次）；硬排除计数为 0。V2 只修复证据语义，不据此宣称胜率、Queen 存活或资产收益改善。

回归场景：历史已知远端子头、当前可见合法首步返回 unknown；当前可见完整封闭仍可证；亲体等待子体移走仍保留；未知 portal 与预算耗尽不称死路。复用完整身体、old-tail、支付额度、出生头、普通 portal 等冻结场景，并用官方 WASM 执行。

冻结前通过 5 个 CPP 场景套件、35 个协议场景/38 帧（峰值 9,302,494 CPU 点）；8 个合法合成完整历史 Atlas/当前 49 格计量单元峰值 12,810,496。压力场景包含额外独立 assessment+实际 choose，不能称生产的普遍上界或真实完整观察路径。没有运行强度比赛。

源码 SHA256：`507e9256720be3f709aee98dae73e5d69729ddd7efb3700142382fa780953409`。

证据：[CPP](../test-results/emergency-v2-cpp-checks.log)、[协议](../test-results/emergency-v2-final-protocol.json)、[预算](../test-results/emergency-v2-history-budget.json)、[V1 发现集](oct7-emergency-discovery-findings.md)。
