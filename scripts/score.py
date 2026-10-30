#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""加权评分与风险等级计算。

输入 JSON：
{
  "name":    {"clarity": 5, "technical_means": 4, "distinguishing": 3, "brevity": 5},
  "content": {"problem_definition": 4, "technical_specificity": 3,
              "advantage_support": 3, "support_consistency": 4, "terminology": 4},
  "features_total": 4,
  "features_disclosed": 2,
  "single_source_covers_all": false
}

各维度为 0-5 分，脚本按权重线性折算：名称 40 分 + 内容 60 分 = 总分 100。
未提供或不合法的维度按 0 分计入，并在输出末尾列出，便于追溯为何总分偏低。

用法：
    python score.py data.json
    python score.py data.json --json
    cat data.json | python score.py
"""

import json
import os
import sys

MAX_SCORES = {
    "name": {"clarity": 12, "technical_means": 12, "distinguishing": 10, "brevity": 6},
    "content": {
        "problem_definition": 12,
        "technical_specificity": 18,
        "advantage_support": 12,
        "support_consistency": 12,
        "terminology": 6,
    },
}

PART_LABEL = {"name": "名称", "content": "内容"}

DIM_LABELS = {
    ("name", "clarity"): "主题明确性",
    ("name", "technical_means"): "技术手段明确性",
    ("name", "distinguishing"): "区别特征体现",
    ("name", "brevity"): "简洁性与长度",
    ("content", "problem_definition"): "技术问题明确性",
    ("content", "technical_specificity"): "技术手段具体性",
    ("content", "advantage_support"): "有益效果说服力",
    ("content", "support_consistency"): "支持一致性",
    ("content", "terminology"): "术语规范与一致性",
}


def clamp(value, max_value):
    """转为数值并限制在 [0, max_value]；无法解析时返回 None。"""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    if v != v:  # NaN
        return None
    return max(0.0, min(v, max_value))


def grade_of(total):
    if total >= 85:
        return "A"
    if total >= 70:
        return "B"
    if total >= 55:
        return "C"
    return "D"


def risk_of(features_total, features_disclosed, single_source):
    """依据特征覆盖情况返回 (等级, 理由)。"""
    single = str(single_source).strip().lower() in ("true", "1", "yes", "y", "是")
    if single:
        return "高", "单份对比文件已覆盖全部核心区别特征，独立权利要求很可能被否定，需要重构独权或突出真正区别于现有技术的特征。"
    ft = clamp(features_total, 10 ** 6)
    fd = clamp(features_disclosed, 10 ** 6)
    if ft is None or ft <= 0:
        return "中", "未能识别出核心区别特征，无法评估新颖性，请补充权利要求书或说明书内容。"
    if fd is None:
        return "中", "未提供已公开特征数量，无法判定。"
    if fd >= ft:
        return "高", "核心区别特征合计已被公开（虽分散于多份文件），存在组合启示风险，建议突出跨文件未覆盖的区别点。"
    if fd >= 0.6 * ft:
        return "中", "超过六成核心区别特征已被公开，建议收紧独权中的具体参数或结构关系以拉开距离。"
    return "低", "多数核心区别特征未被检索到的文件公开，可在撰写时突出这些区别点的具体实现方式。"


def evaluate(entry):
    entry = entry if isinstance(entry, dict) else {}
    rows = []
    missing = []
    part_totals = {}

    for part, dims in MAX_SCORES.items():
        scores = entry.get(part) if isinstance(entry.get(part), dict) else {}
        total = 0.0
        for key, max_value in dims.items():
            raw = scores.get(key)
            got = clamp(raw, 5)
            if got is None:
                missing.append(f"{part}.{key}")
                got = 0.0
            weighted = got / 5.0 * max_value
            label = DIM_LABELS.get((part, key), key)
            rows.append((PART_LABEL[part], label, f"{got:.0f}/5", f"{weighted:.1f}/{max_value}"))
            total += weighted
        part_totals[part] = total

    name_total = part_totals["name"]
    content_total = part_totals["content"]
    total = name_total + content_total
    level, reason = risk_of(
        entry.get("features_total"),
        entry.get("features_disclosed"),
        entry.get("single_source_covers_all", False),
    )

    return {
        "rows": rows,
        "missing": missing,
        "name_total": name_total,
        "content_total": content_total,
        "total": total,
        "grade": grade_of(total),
        "risk_level": level,
        "risk_reason": reason,
    }


def render_markdown(res):
    lines = [
        "# 加权评分结果",
        "",
        f"- 名称质量：{res['name_total']:.0f}/40",
        f"- 内容质量：{res['content_total']:.0f}/60",
        f"- 总分：{res['total']:.0f}/100 —— 等级：{res['grade']}",
        f"- 查重风险：{res['risk_level']}",
        f"  - 理由：{res['risk_reason']}",
        "",
        "## 明细",
        "",
        "| 类别 | 维度 | 原始分 | 折算得分 |",
        "|---|---|---|---|",
    ]
    for part, label, raw, shown in res["rows"]:
        lines.append(f"| {part} | {label} | {raw} | {shown} |")
    if res["missing"]:
        lines.append("")
        lines.append("以下维度未提供，按 0 分计入：")
        lines.extend(f"- {m}" for m in res["missing"])
    return "\n".join(lines)


def batch_render(results):
    lines = [
        "# 批量评分汇总",
        "",
        "| # | 名称质量 | 内容质量 | 总分 | 等级 | 查重风险 |",
        "|---|---|---|---|---|---|",
    ]
    for i, res in enumerate(results, 1):
        lines.append(
            f"| {i} | {res['name_total']:.0f}/40 | {res['content_total']:.0f}/60 | "
            f"{res['total']:.0f}/100 | {res['grade']} | {res['risk_level']} |"
        )
    if results:
        avg = sum(r["total"] for r in results) / len(results)
        lines.append("")
        lines.append(f"平均分：{avg:.0f}/100")
    return "\n".join(lines)


def load_input(args):
    if args:
        path = args[0]
        if not os.path.exists(path):
            print(f"错误：找不到文件 {path}")
            sys.exit(1)
        with open(path, encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError as exc:
                print(f"JSON 解析失败：{exc}")
                sys.exit(1)
    stdin_data = sys.stdin.read().strip()
    if stdin_data:
        try:
            return json.loads(stdin_data)
        except json.JSONDecodeError as exc:
            print(f"JSON 解析失败：{exc}")
            sys.exit(1)
    return {}


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    raw = load_input(args)
    is_batch = isinstance(raw, list)
    entries = raw if is_batch else [raw]
    results = [evaluate(e) for e in entries]

    if "--json" in sys.argv:
        print(json.dumps(results if is_batch else results[0], ensure_ascii=False, indent=2))
    elif is_batch:
        print(batch_render(results))
    else:
        print(render_markdown(results[0]))


if __name__ == "__main__":
    main()
