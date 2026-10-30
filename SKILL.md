---
name: cn-patent-check
description: 中国专利查重与质量评估。当用户提供专利名称、权利要求书、说明书草稿或摘要，要求做国内专利查重/查新、评估新颖性撞车风险、对专利名称与内容质量评分，或希望获得多个建议专利名供选择时使用此 skill。基于 Google Patents 等公开渠道对中国专利文献做特征比对，输出查重风险等级、名称与内容加权评分（百分制）及改进建议。
agent_created: true
---

# Cn Patent Check（中国专利查重与质量评估）

## 概述

对提交的国内专利材料执行三项工作：基于公开渠道的近似查重并给出风险等级、按加权细则对名称与内容进行百分制评分、按需生成多个建议专利名供用户选择。

## 4-D 方法

1. **Deconstruct** — 明确待查重的技术方案：至少覆盖摘要、权利要求 1、核心实施方式；缺少权利要求时明确声明风险等级不可靠。
2. **Diagnose** — 从材料诊断最常见的失效点：名称是否缺领域或手段、独权是否过于上位、区别特征是否已被公开、术语是否同一对象多个名称。
3. **Develop** — 依据参考文档形成与改进和替代相关的意见。
4. **Deliver** — 按 `references/report_template.md` 交付报告。

## 工作流

### 第 1 步：确认输入（未完成前不要进入后续步骤）

向用户获取：专利名称、摘要、权利要求书、说明书中的核心技术手段与有益效果部分。材料不全时不要中止，先记录缺口，在第 6 步的待补充清单中列出。

### 第 2 步：建议专利名（询问需求后执行）

先询问用户是否需要建议专利名。确认需要后，按 `references/name_generation.md` 生成 3–5 个候选，用 AskUserQuestion 让用户选择，用户选定后再按该名称继续评分。

生成后必须执行初筛并据结果修正：

```bash
python scripts/name_check.py "候选名一" "候选名二"
```

用户明确表示不需要时跳过整份 `name_generation.md`，并在报告首部注明「本次未提供建议名称」。

### 第 3 步：查重检索

按 `references/novelty_search.md` 执行：

1. 抽取核心区别特征 C1…Cn，为每个特征准备 2–3 个关键词变体
2. 执行三轮检索式（全特征 / 两两组合 / 上位加 IPC），渠道以 Google Patents 为主，`https://patents.google.com/?q=<检索式>&country=CN`
3. 保留相关度最高的 3–5 份文件，逐份填写特征比对表
4. 统计 `features_total`、`features_disclosed`、`single_source_covers_all` 三项，供下一步脚本判级

检索结果必须包含具体公开号与出处；不得在只检索一个来源的情况下给出「高风险」或「低风险」结论。

### 第 4 步：质量评分

按 `references/quality_rubric.md` 逐维度打 0–5 分。材料缺失导致无法给出有依据的评分时该维度记 0，并列入待补充信息清单。

然后执行加权计算：

```bash
python scripts/score.py <ratings.json>           # Markdown 结果
python scripts/score.py <ratings.json> --json    # JSON 结果
```

JSON 结构参见 `scripts/score.py` 顶部说明。

每个给分必须同时写出扣分点与修改建议。

### 第 5 步：反思（第 3、4 步执行后）

分别执行：

```bash
python scripts/reflect.py novelty
python scripts/reflect.py scoring
```

针对每个触发的问题，深入复查并修正后继续。

### 第 6 步：输出报告

按 `references/report_template.md` 构建报告，包含：摘要、查重结论评分详情、缺点、建议原文、待补充信息清单。报告首部写明「本评估基于公开网络渠道，属内部自查，不构成法律意见」。

结果写入 Markdown 文件（`YYYY-MM-DD-patent-check-cn-<主题>.md`，放在用户当前工作目录下）并呈现给用户。

## 评估立场

保持独立、批判的专业评审立场，不要一味认同用户的方案。以下情形必须如实指出：

- 用户提供的权利要求可能与某一在先文件构成完全相同或惯用手段置换
- 用户期待高分，但材料支撑薄弱、区别点已被公开，或效果缺少数据

## 表达要求

使用简体中文；结论优先用表格或清单呈现；解释性文字精简，避免主观渲染与营销式表述。

## 资源清单

| 文件 | 用途 | 加载时机 |
|---|---|---|
| `references/novelty_search.md` | 三轮检索式、Google Patents 用法、特征比对口径、常见陷阱 | 第 3 步必读 |
| `references/quality_rubric.md` | 各维度的 0–5 分锚点与权重 | 第 4 步必读 |
| `references/name_generation.md` | 建议专利名模板、生成规则、初筛要求 | 第 2 步必读（用户需要时） |
| `references/report_template.md` | 报告结构与免责声明 | 第 6 步必读 |
| `scripts/score.py` | 加权评分与风险等级计算 | 第 4 步执行 |
| `scripts/name_check.py` | 候选名机械初筛（字数、水词、主题词） | 第 2 步执行 |
| `scripts/reflect.py` | 框架合规反思问题 | 第 5 步执行 |

## 禁止事项

| 禁止 | 正确做法 |
|---|---|
| 只给分数不给修改指导 | 每个给分同步扣分点与改写建议 |
| 材料不全时臆测给分 | 维度记 0 并列入待补充清单 |
| 单一来源检索即下风险结论 | 至少完成三轮检索并交叉验证后再判级 |
| 结论笼统（如「建议进一步改进」） | 具体说明改进哪个技术特征、涉及哪份对比文件、改为什么表述 |
| 用户未要求时仍强行生成建议名称 | 先询问，用户不需要则跳过并在报告注明 |
