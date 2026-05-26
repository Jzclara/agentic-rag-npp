/* ─────────────────────────────────────────────────────────────
   示例数据 / 兜底默认值
   接入真实后端时，App.jsx 启动时会用 fetchPapers() 等覆盖这些。
   ───────────────────────────────────────────────────────────── */

export const PAPERS = [
  {
    id: "p1",
    title: "A condition-informed dynamic Bayesian network framework to support severe accident management in nuclear power plants",
    short: "Condition-informed DBN for severe accident management",
    authors: "Roma, Di Maio, Zio",
    venue: "Reliab. Eng. Syst. Saf.",
    year: 2024,
    pages: 28,
    tag: "DBN · SAM",
    abstract: "Proposes a DBN framework that infers plant state and damage level from sensor data, predicts available buffer time, and evaluates mitigation strategies for severe accidents.",
    selected: true,
  },
  {
    id: "p2",
    title: "A physics-based parametric regression approach for feedwater pump system diagnosis",
    short: "Physics-based regression for feedwater pump diagnosis",
    authors: "Ling et al.",
    venue: "Nucl. Eng. Des.",
    year: 2023,
    pages: 14,
    tag: "Diagnostics",
    abstract: "Develops a physics-informed parametric regression model to diagnose degradation in feedwater pump systems, combining domain knowledge with statistical fitting.",
    selected: true,
  },
  {
    id: "p3",
    title: "Abnormal event detection, identification and isolation in nuclear power plants using LSTM networks",
    short: "LSTM for abnormal event detection in NPP",
    authors: "Yao et al.",
    venue: "Prog. Nucl. Energy",
    year: 2022,
    pages: 17,
    tag: "LSTM · Detection",
    abstract: "Uses LSTM networks to detect, identify, and isolate abnormal events in NPPs from multivariate time-series sensor data.",
    selected: true,
  },
  {
    id: "p4",
    title: "Functional Modelling for Fault Diagnosis and its Application for NPP",
    short: "Functional modelling for fault diagnosis in NPP",
    authors: "Lind, Zhang",
    venue: "Nucl. Eng. Technol.",
    year: 2014,
    pages: 23,
    tag: "MFM · Diagnosis",
    abstract: "Introduces Multilevel Flow Modelling (MFM) to represent plant goals, functions, and components hierarchically, enabling causal reasoning about fault propagation.",
    selected: true,
  },
  {
    id: "p5",
    title: "MFM-based alarm root-cause analysis and ranking for nuclear power plants",
    short: "MFM-based alarm root-cause analysis & ranking",
    authors: "Wu, Lind, Ravn",
    venue: "Prog. Nucl. Energy",
    year: 2021,
    pages: 18,
    tag: "MFM · Alarms",
    abstract: "Applies MFM to trace alarm signals back to root causes and rank them by severity, reducing operator cognitive load during abnormal situations.",
    selected: true,
  },
  {
    id: "p6",
    title: "Possibilities of reinforcement learning for nuclear power plants",
    short: "Possibilities of RL for nuclear power plants",
    authors: "Bae et al.",
    venue: "Ann. Nucl. Energy",
    year: 2023,
    pages: 21,
    tag: "RL",
    abstract: "Reviews potential applications of reinforcement learning in NPP control and operation, discussing feasibility constraints and safety considerations.",
    selected: true,
  },
  {
    id: "p7",
    title: "Robust deep auto-encoding network for real-time anomaly detection at nuclear power plants",
    short: "Robust auto-encoder for real-time anomaly detection",
    authors: "Yong-Kuo Liu et al.",
    venue: "Prog. Nucl. Energy",
    year: 2022,
    pages: 16,
    tag: "Auto-encoder",
    abstract: "Proposes a robust deep autoencoder for real-time anomaly detection, trained on normal operation data to flag deviations without labeled fault samples.",
    selected: true,
  },
  {
    id: "p8",
    title: "System risk quantification and decision making support using functional modeling and dynamic Bayesian network",
    short: "Risk quantification via MFM + DBN",
    authors: "Kim et al.",
    venue: "Reliab. Eng. Syst. Saf.",
    year: 2022,
    pages: 24,
    tag: "MFM · DBN",
    abstract: "Combines MFM with DBN to quantify system risk; MFM provides the causal structure while DBN handles probabilistic inference for decision support.",
    selected: true,
  },
];

export const CHATS = [
  { id: "c-bayes",      title: "用于诊断的贝叶斯网络",            date: "今天 14:22", active: true },
  { id: "c-mfm",        title: "MFM 与故障传播",                    date: "今天 11:04" },
  { id: "c-anomaly",    title: "异常检测：LSTM vs 自编码器",     date: "昨天" },
  { id: "c-rl",         title: "强化学习在 NPP 控制中的适用性",  date: "昨天" },
  { id: "c-realtime",   title: "实时监测的约束条件",                date: "5 月 18 日" },
  { id: "c-overview",   title: "8 篇论文的方法总览",                date: "5 月 18 日" },
];

/* Citation source data — re-used by the demo conversation */
export const SOURCES_BAYES_Q1 = [
  {
    n: 1,
    paperId: "p1",
    fileName: "A condition-informed dynamic Bayesian network framework…",
    page: 2,
    score: 0.864,
    quote:
      "In this work, we address the limitations of the available AMSTs by proposing a framework based on Dynamic Bayesian Networks (DBNs). In all generality, Bayesian Networks (BNs) are probabilistic graphical models whose nodes are connected by edges representing the conditional dependence evaluated through Conditional Probability Tables (CPTs).",
  },
  {
    n: 2,
    paperId: "p8",
    fileName: "System risk quantification and decision making support…",
    page: 6,
    score: 0.829,
    quote:
      "A key gap remains: there is little research regarding how to construct BN structure and how to discretize system space into multiple states. Most of research so far relied on expert knowledge to construct a BN model or did not show how to select relevant nodes of the network.",
  },
  {
    n: 3,
    paperId: "p1",
    fileName: "A condition-informed dynamic Bayesian network framework…",
    page: 6,
    score: 0.819,
    quote:
      "A BN becomes a DBN when such dependence is unrolled in time to account for time-evolving CPTs, making them capable of estimating time-evolving posterior distributions of node values (inferred nodes) when other nodes (evidence nodes) are instantiated by condition-related sensor data values.",
  },
  {
    n: 4,
    paperId: "p4",
    fileName: "Functional Modelling for Fault Diagnosis and its Application for NPP",
    page: 4,
    score: 0.807,
    quote:
      "Functional modelling provides a means-end and part-whole decomposition of plant intentions and processes, supporting causal reasoning about fault propagation across hierarchical levels.",
  },
  {
    n: 5,
    paperId: "p1",
    fileName: "A condition-informed dynamic Bayesian network framework…",
    page: 28,
    score: 0.801,
    quote:
      "Future work will explore Hybrid Bayesian Networks, which can host both continuous and discrete variables, and the integration of unreliable measurements through virtual evidence.",
  },
];

export const SOURCES_BAYES_Q2 = [
  {
    n: 1,
    paperId: "p8",
    fileName: "System risk quantification and decision making support…",
    page: 6,
    score: 0.783,
    quote:
      "There are two challenges in designing a BN: picking variables and specifying the BN structure. While there are many studies on how to learn a BN structure from multidimensional data itself, it requires large data sets and takes significant computational time.",
  },
  {
    n: 2,
    paperId: "p8",
    fileName: "System risk quantification and decision making support…",
    page: 18,
    score: 0.762,
    quote:
      "For a component-level BN construction, a functional hierarchy can derive the causal relations which lead to a component failure. For system-level BN construction, a fault tree analysis has been considered a good option to provide a graphical structure to the BN.",
  },
  {
    n: 3,
    paperId: "p1",
    fileName: "A condition-informed dynamic Bayesian network framework…",
    page: 9,
    score: 0.758,
    quote:
      "Once defined the DBN structure, we proceed with CPT learning by sampling stochastic input values, propagating them through the physical model, and populating the training data matrix.",
  },
  {
    n: 4,
    paperId: "p1",
    fileName: "A condition-informed dynamic Bayesian network framework…",
    page: 7,
    score: 0.754,
    quote:
      "The DBN structure is defined using Bayesian network software GeNIe, whose nodes are identified and whose interdependencies are characterized by expert judgment.",
  },
];

export const SOURCES_BAYES_Q3 = [
  {
    n: 1,
    paperId: "p4",
    fileName: "Functional Modelling for Fault Diagnosis and its Application for NPP",
    page: 1,
    score: 0.853,
    quote:
      "Functional modelling supports systematic identification of relevant variables and causal links by representing the plant as a hierarchy of goals, functions and components — addressing precisely the variable-selection problem in BN design.",
  },
  {
    n: 2,
    paperId: "p4",
    fileName: "Functional Modelling for Fault Diagnosis and its Application for NPP",
    page: 3,
    score: 0.849,
    quote:
      "Multilevel Flow Modelling (MFM) makes the causal structure of the plant explicit. When mapped to a Bayesian Network, MFM provides the topology that would otherwise be elicited from experts or learned from sparse data.",
  },
  {
    n: 3,
    paperId: "p8",
    fileName: "System risk quantification and decision making support…",
    page: 12,
    score: 0.836,
    quote:
      "By using MFM as the backbone, the resulting DBN inherits a domain-grounded structure. This reduces the dependency on large training datasets and yields a model that is interpretable to plant operators.",
  },
];

/* ── The active conversation: 3-turn dialogue based on real run data ── */
export const MESSAGES = [
  {
    id: "t1-u",
    role: "user",
    text: "贝叶斯网络是如何用于核电站故障诊断的？",
  },
  {
    id: "t1-a",
    role: "assistant",
    standalone: "贝叶斯网络在核电站故障诊断中的应用方式",
    timing: { totalMs: 6420, tokens: 312 },
    trace: {
      status: "complete",
      retries: 0,
      grade: "relevant",
      nodes: [
        { id: "rewrite",   name: "rewrite",   tag: "LLM",      ms: 420,
          detail: "首轮问题 —— 问句保持不变。",
          quote: null },
        { id: "retrieve",  name: "retrieve",  tag: "Hybrid",   ms: 1840,
          detail: "在 8 篇文献中混合检索 · BGE-small + BM25 → RRF → 重排序。",
          subnodes: [
            "向量召回 · top-10",
            "BM25 召回 · top-10",
            "RRF 融合 · k=60 · top-10",
            "Cross-encoder 重排 · bge-reranker-base · top-5",
          ] },
        { id: "grade",     name: "grade",     tag: "LLM",      ms: 760,
          detail: "上下文包含相关的 DBN 段落 → 进入生成。",
          verdict: "relevant" },
        { id: "generate",  name: "generate",  tag: "LLM",      ms: 3400,
          detail: "已生成带 5 条内联引用的回答。",
          verdict: "ok" },
      ],
    },
    answer: [
      { p: "根据检索到的上下文，贝叶斯网络（BN）在核电站中主要作为一种 " },
      { p: "概率图模型", b: true },
      { p: " 使用 —— 节点之间的边通过条件概率表编码条件依赖关系", cite: 1 },
      { p: "。当这种依赖关系被展开到多个时间片上时，BN 就变成了 " },
      { p: "动态贝叶斯网络（DBN）", b: true },
      { p: "，随传感器证据的加入可以随时间更新后验分布", cite: 3 },
      { p: "。" },
      { br: true },
      { p: "文献中反复出现两类应用：" },
      { br: true },
      { p: "1. ", b: true },
      { p: "严重事故管理。", b: true },
      { p: "一个条件感知的 DBN 可以推断机组运行状态、初始事件与损害状态，预测可用的缓冲时间，并评估备选缓解措施", cite: 1 },
      { p: "。" },
      { br: true },
      { p: "2. ", b: true },
      { p: "系统风险量化。", b: true },
      { p: "BN 被用来建模故障传播，但一个关键难点是如何构造结构及离散化系统状态 —— 大多数先前研究依赖于专家知识", cite: 2 },
      { p: "。" },
    ],
    sourcesKey: "SOURCES_BAYES_Q1",
  },
  {
    id: "t2-u",
    role: "user",
    text: "构造它们的结构时主要的难点是什么？",
  },
  {
    id: "t2-a",
    role: "assistant",
    standalone: "构造贝叶斯网络结构时的主要难点",
    timing: { totalMs: 9100, tokens: 248 },
    trace: {
      status: "complete",
      retries: 1,
      grade: "relevant",
      nodes: [
        { id: "rewrite-1",  name: "rewrite",   tag: "LLM",      ms: 540,
          detail: "代词“它们”已解析为“贝叶斯网络”。",
          quote: "它们 → 贝叶斯网络结构" },
        { id: "retrieve-1", name: "retrieve",  tag: "Hybrid",   ms: 1620,
          detail: "混合召回 · 8 篇文献 → 10 候选 → 重排取前 5。" },
        { id: "grade-1",    name: "grade",     tag: "LLM",      ms: 780,
          detail: "判定：上下文部分相关，但缺乏关于构造方法的具体细节。触发重写。",
          retry: true,
          verdict: "insufficient" },
        { id: "rewrite-2",  name: "rewrite",   tag: "retry",    ms: 510,
          detail: "加入领域提示进行扩写：“变量选择 · BN 结构设计 · 从数据中学习的挑战”。",
          quote: "构造用于故障诊断的贝叶斯网络结构的主要难点（变量选择、结构设计、学习挑战）" },
        { id: "retrieve-2", name: "retrieve",  tag: "Hybrid",   ms: 1740,
          detail: "第二轮检索补充了 Kim 等人关于 BN 设计挑战的论文。" },
        { id: "grade-2",    name: "grade",     tag: "LLM",      ms: 720,
          detail: "上下文现包含明确的构造难点 → 进入生成。",
          verdict: "relevant" },
        { id: "generate-1", name: "generate",  tag: "LLM",      ms: 3190,
          detail: "生成回答，引用 2 篇文献中的 3 个来源。" },
      ],
    },
    answer: [
      { p: "文献中重点提出三个主要难点：" },
      { br: true },
      { p: "1. ", b: true }, { p: "变量选择。", b: true },
      { p: "设计一个 BN 面临两个问题：选哪些变量，以及怎么设定网络结构本身", cite: 1 },
      { p: "。多数研究要么依赖专家知识，要么未明确说明节点是如何选取的", cite: 1 },
      { p: "。" },
      { br: true },
      { p: "2. ", b: true }, { p: "数据驱动学习成本高。", b: true },
      { p: "从高维数据中学习网络结构需要大量数据与计算成本", cite: 1 },
      { p: "，而 NPP 场景中这些资源几乎不可得。" },
      { br: true },
      { p: "3. ", b: true }, { p: "依赖专家经验。", b: true },
      { p: "在动态 BN 中，网络结构通常是在 GeNIe 等软件中手动定义、依赖专家裁决调校互依赖关系", cite: 4 },
      { p: "，参数学习则基于物理模型生成的合成数据进行", cite: 3 },
      { p: "。" },
    ],
    sourcesKey: "SOURCES_BAYES_Q2",
  },
  {
    id: "t3-u",
    role: "user",
    text: "功能建模是如何缓解这些局限的？",
  },
  {
    id: "t3-a",
    role: "assistant",
    standalone: "功能建模（MFM）如何缓解 NPP 故障诊断中贝叶斯网络结构构造的局限",
    timing: { totalMs: 7200, tokens: 286 },
    trace: {
      status: "complete",
      retries: 0,
      grade: "relevant",
      nodes: [
        { id: "rewrite-31",  name: "rewrite",  tag: "LLM",     ms: 480,
          detail: "依据上一轮上下文解析了“这些局限”。",
          quote: "这些局限 → BN 结构构造的难点（Q2）" },
        { id: "retrieve-31", name: "retrieve", tag: "Hybrid",  ms: 1980,
          detail: "混合召回，重点面向 MFM / 功能建模相关论文。" },
        { id: "grade-31",    name: "grade",    tag: "LLM",     ms: 740,
          detail: "在 Lind 2014 与 Kim 2022 中均有强匹配 —— 进入生成。",
          verdict: "relevant" },
        { id: "generate-31", name: "generate", tag: "LLM",     ms: 4000,
          detail: "已生成回答，引用 2 篇文献中的 3 个来源。" },
      ],
    },
    answer: [
      { p: "功能建模（具体说是多层次流建模 MFM）从两个互补的角度缓解了 BN 结构构造的难题：" },
      { br: true },
      { p: "首先，它提供了 ", b: false },
      { p: "领域接地的网络拓扑", b: true },
      { p: "。MFM 将机组表示为目标、功能、组件的层次结构，使因果关系明确可见", cite: 1 },
      { p: "。该层次映射到贝叶斯网络后，就直接供给了本需要专家裁决或从稀疏数据中学习的拓扑结构", cite: 2 },
      { p: "。" },
      { br: true },
      { p: "其次，它 ", b: false },
      { p: "降低了对大规模训练数据的依赖", b: true },
      { p: "。以 MFM 作为骨架后，DBN 的结构既对运行员可解释、又有物理意义支撑，从而绕过了纯数据学习对数据体量的要求", cite: 3 },
      { p: "。" },
    ],
    sourcesKey: "SOURCES_BAYES_Q3",
  },
];

/* Suggested follow-up questions */
export const SUGGESTIONS = [
  "哪篇论文在 LSTM 检测上的实验结果最强？",
  "对比 MFM 与 DBN 在根因分析上的差异",
  "概括强化学习用于 NPP 控制的约束",
  "这 8 篇论文中还有哪些开放问题？",
];

/* Evaluation metrics (Ragas) — for the Evals tab in inspector */
export const METRICS = {
  baseline: { faithfulness: 0.71, answer_relevancy: 0.58 },
  agentic:  { faithfulness: 0.85, answer_relevancy: 0.68 },
  runs: 12,
  testset: "testset.jsonl · 32 questions · 8 dialogues",
};


/* 让组件可以通过字符串键查找引用源集合
   (因为 MESSAGES 里写的是 sourcesKey: "SOURCES_BAYES_Q1") */
export const SOURCES_BY_KEY = {
  SOURCES_BAYES_Q1,
  SOURCES_BAYES_Q2,
  SOURCES_BAYES_Q3,
};
