# 写作规范（Style Guide）— 强制执行

本书书名：**《智能体运行时原理 —— 从 LangChain 到 LangGraph，及可迁移的 Agent 设计法则》**

交付形态：多页 HTML 电子书，由 Markdown 源文件构建。读者：有工程经验的开发者，正在系统学习 LangChain/LangGraph 生态，目标是**理解框架行为、排查问题、做架构选型**。

---

## 一、最高原则：零真实代码

**绝对禁止**出现任何可直接运行的 API 调用代码。包括但不限于：

- ❌ `from langchain_openai import ChatOpenAI`
- ❌ `graph.add_node("agent", call_model)`
- ❌ `chain = prompt | model | parser`
- ❌ 任何带 `import`、赋值、方法链的真实代码块

**允许并鼓励**的表现形式（按优先级）：

1. **结构示意（伪代码）** — 描述"逻辑步骤"而非"函数调用"。语言可以是中性中文/英文伪代码。
2. **接口签名** — 只写概念签名，用于说明契约。例：`invoke(input: I) -> O`、`NodeFn(state: S) -> Partial<S>`。签名不是代码，是契约描述。
3. **流程图 / 结构图 / 状态迁移图** — 用下方"图示套件"。
4. **对照表** — 概念、取舍、失效模式优先用表格。

伪代码块统一用 `text` 语言标记，且**只允许出现流程步骤**，例如：

```text
输入 x
  ├─ 步骤一：解析并校验 x → 得到 (a, b)
  ├─ 步骤二：并发执行 f(a) 与 g(b)
  └─ 步骤三：合并结果，若校验失败则回退到默认分支
```

**判定标准**：读者读完这段话，能不能自己写出实现？能 → 合格。读者能不能直接复制粘贴运行？能 → 违规，必须改写。

---

## 二、叙述语气与结构

- **语气**：像一个资深工程师在给同事讲原理。直接、有判断、不客套。不用"众所周知""让我们一起来探索"这类填充语。
- **必须回答"为什么"**：每讲一个机制，都要交代它解决了什么本质问题、不这么做会怎样。
- **必须有观点**：框架的取舍要明说（"这个设计在 A 场景是优势，在 B 场景是负债"）。允许批评 LangChain/LangGraph 的设计。
- **必须可迁移**：每章末尾要有"离开这些框架，你自己会怎么实现"的视角。用户要的是通用原理。
- **禁止**：营销腔、AI 味套话、"总之/综上所述"式的空洞收尾、emoji。

### 每章固定结构

每章 Markdown 文件必须严格按此顺序：

```
# 第 N 章 章节标题

> 一句话主旨（blockquote，本章要解决的核心问题）

## 引子
（150-300 字，用一个具体困境/反例切入，不要讲定义）

## 小节一 …
## 小节二 …
（主体，每章 3-6 个小节，小节内可用 ### 细分）

## 常见误区与排查
（列表或表格，列 3-5 条实践中的误解与症状 → 根因）

## 本章要点
（5-8 条短句，每条一行，`-` 列表）

## 迁移视角：如果不用这个框架
（200-400 字，讲清楚这套原理在别的技术栈里对应什么）
```

### 结构例外的登记

以下例外是明确许可的（构建前由 `check.py` 自动校验，不要在正文里再自行偏离）：

| 文件 | 例外 | 理由 |
|---|---|---|
| `23-conclusion.md`（结语章） | 不设 `## 迁移视角` 小节；末节为 `## 最后` | 整章即迁移视角，再设该小节是同义重复。`## 常见误区与排查` 与 `## 本章要点` **仍须保留** |
| `A-glossary.md` / `B-checklist.md`（附录） | 不适用"每章固定结构"（无引子、无常见误区、无本章要点、无迁移视角） | 附录是工具页，按查询方式组织，不按叙述方式组织 |
| 附录 A | 不强制配图示 | 内容形态是术语表，图示不增加信息 |

除上表之外，任何偏离固定结构的写法都算不合格。

### 小节内部要求

- 每个小节开头**不要**写"本节将介绍…"。直接进入内容。
- 关键结论用 `**加粗**` 标出，但每章加粗不超过 15 处，否则失去信号价值。
- 有对比就用表格（至少每章 1 个表格）。
- 有流程/结构就用图示套件（至少每章 1 个图）。

---

## 三、图示套件（可控 HTML，务必按模板复制）

允许在 Markdown 中直接写 HTML 块（构建器会原样保留）。**只能使用以下类名，不要发明新类名，不要写内联 style**。

### 1. 横向流程

```html
<div class="dg">
  <div class="dg-flow">
    <div class="dg-box">用户输入</div>
    <div class="dg-arw">→</div>
    <div class="dg-box">模型调用</div>
    <div class="dg-arw">→</div>
    <div class="dg-box dg-hl">输出解析</div>
  </div>
</div>
```

### 2. 纵向流程（含分支标注）

```html
<div class="dg">
  <div class="dg-col">
    <div class="dg-box">接收状态 S</div>
    <div class="dg-arw">↓</div>
    <div class="dg-box dg-alt">条件判断</div>
    <div class="dg-arw">↓ 满足 / ↘ 不满足（回边）</div>
    <div class="dg-box dg-hl">执行节点</div>
  </div>
</div>
```

### 3. 分层结构

```html
<div class="dg">
  <div class="dg-stack">
    <div class="dg-layer"><span class="dg-tag">应用层</span>Agent 图 / 工作流编排</div>
    <div class="dg-layer"><span class="dg-tag">协议层</span>Runnable 执行语义 / 工具调用协议</div>
    <div class="dg-layer"><span class="dg-tag">契约层</span>Schema 校验（Pydantic 模型）</div>
    <div class="dg-layer"><span class="dg-tag">资源层</span>模型 API / 向量库 / 外部工具</div>
  </div>
</div>
```

### 4. 左右对照

```html
<div class="dg">
  <div class="dg-vs">
    <div class="dg-col-head">链（DAG）</div>
    <div class="dg-col-head dg-alt-head">图（带环）</div>
    <div class="dg-cell">单向，执行次数确定</div>
    <div class="dg-cell dg-alt">可回边，执行次数由状态决定</div>
    <div class="dg-cell">终止由拓扑保证</div>
    <div class="dg-cell dg-alt">终止必须显式设计</div>
  </div>
</div>
```

### 5. 状态迁移 / 时序

```html
<div class="dg">
  <div class="dg-seq">
    <div class="dg-act">调用方</div>
    <div class="dg-arw-h">请求 →</div>
    <div class="dg-act">执行引擎</div>
    <div class="dg-arw-h">← 暂停（保存检查点）</div>
  </div>
</div>
```

可选修饰类：`dg-box`、`dg-hl`（强调，主色）、`dg-alt`（次要色）、`dg-tag`（小标签）。

---

## 四、术语统一

| 统一写法 | 说明 |
|---|---|
| Runnable | 不译，首现时附"可运行组件" |
| 链（Chain） | LangChain 早期抽象 |
| 图（Graph） | LangGraph 的执行模型 |
| 超步（super-step） | Pregel/BSP 的同步边界 |
| 检查点（Checkpoint） | 持久化快照 |
| 状态（State） | 图中流动的共享数据 |
| 归约器（Reducer） | 并发更新的合并函数 |
| 工具调用（Tool Calling） | 不译 |
| 上下文窗口 | 不写"语境窗口" |
| Agent / 智能体 | 首次出现写"智能体（Agent）"，之后可混用 |
| LLM | 不写"大语言模型"缩写形式混乱，统一用 LLM |

首次出现的英文术语用 `中文（English）` 格式。

---

## 五、篇幅控制

- 每章正文 **3500-5000 字**（中文字符计）。低于 3200 字视为不合格，需扩写。
- 引子 150-300 字；"迁移视角"200-400 字。
- 不要把内容堆在列表里，正文段落必须占主体（列表/表格合计不超过全文 40%）。
- 每章至少 1 个表格、至少 1 个图示。**这是两项独立要求，互不替代**：用 `.dg-vs` 对照块示意过对比，仍然必须再给一个 Markdown 表格（表格可检索、可复制、可被外部工具消费，图示不能）。反之亦然。
- 表格要与相邻内容互补，不要只是把旁边段落再抄一遍。

---

## 六、文件输出规范

- 文件路径：`/home/huawei/WorkBuddy/langchain/book/content/<章号>-<slug>.md`
- 章号两位数字，如 `03`。
- 文件**只含本章内容**，不要加书名、不要加其他章节。
- 不要写"参见第 X 章"以外的交叉引用占位符；如需引用，直接写"第 X 章"。

---

## 七、规范的可执行化：check.py

本规范里"每章必须…"这类条目靠人眼审阅一定会漏。因此它们被实现成了脚本 `book/check.py`，**每次改完 content/ 必须跑一次**：

```text
python check.py     # 退出码 0 = 通过，1 = 有不合格项
```

它检查的内容与本规范一一对应：

| 检查项 | 对应本文档 |
|---|---|
| 汉字数达标（正文 ≥3500，>5000 提醒） | 五 |
| 每章有 Markdown 表格 + 图示块 | 五、三 |
| 固定结构小节齐全且顺序正确（含已登记的例外） | 二 |
| 首行一级标题格式、章首 blockquote | 二 |
| 无 import / 函数定义 / .invoke() / pip install 等可运行痕迹 | 一 |
| 代码块语言标记只能是 `text` | 一 |
| 无内联 style、图示类名在白名单内 | 三 |
| 附录 B `### 名称（N 条）` 的声明条数与实际条目数一致 | 六 |
| 章节编号连续、附录齐备 | 六 |
| 跨章口径一致（如"四个约束"不得写成"五个约束"） | 四 |

**新增任何跨章节的统一说法（数字、命名、定义），都要在 `check.py` 的 `BAD_PHRASES` 里登记一条**，否则同类矛盾会再次发生。
