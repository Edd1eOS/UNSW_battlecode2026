# 协作消融：拆开两个机制验证

Cooperation V1的88场没有证明普遍Queen保命。原候选、面板、测试报告保持冻结；新建两个独立源码目录，仅在main.cpp顶部加一条编译开关，其他源码文件字节与原V1相同。

| 独立候选 | 开启机制 | 关闭机制 | 源码包SHA256 | WASM SHA256 |
| --- | --- | --- | --- | --- |
| generalist-cooperation-egress-v1 | 可见Queen出口保护及条件静止分裂救援 | 未观察门户到达风险 | c7af166ae53adc3118936d6e43a031d7598e56c36fb329dbadba00104029b9d9 | c9d0e1c1727fcd47b78fc555377009a589af66386b0edfc8aec091c6bbb6c19a |
| generalist-cooperation-arrival-v1 | Queen对未观察门户到达的软风险 | 出口保护及救援 | 72c6f6fe8436d8e2c547f9b2cb9a71eeab6f2fa07d466f04c2bb376055b3f5a1 | b92d9a2c8f2cfc08f057b7dbcd3f30a09c17d31adf8bbdb1d38468c3025020ce |

每份35协议场景42帧通过，包括实际门户身体追踪、升级与子进程；峰值分别8,670,060及8,664,599计算点。原V1的单机制C++消融已分别验证，不能将这些构造检查算成外部胜场。

两份新面板在05:15 UTC冻结后，各自对相同两个冻结外部程序、22地图、2026100701种子、A/B侧跑88场；没有自家版本互战。源代码只开关机制，没有据已见地图调参或加特殊分支。源码与WASM冻结记录分别在test-results/oct7-cooperation-egress-panel及oct7-cooperation-arrival-panel。

这属于已看discovery上的原因分解，仍是发现证据；不能变成独立留出。继续核对完整比赛与共同前缀、Queen资源/死亡、死亡资本及实际计分轴。当前视野下的空出口、可选子体首步及可能到达，都不是未来执行承诺，限制继承[原设计](oct7-cooperation-design.md)。结果公布后再决定是否保留机制，不默认合并。
