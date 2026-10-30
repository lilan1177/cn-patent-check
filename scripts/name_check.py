#!/usr/bin/env python3
"""候选专利名初筛：字数、违规用词与结构要素检查。

用法：
    python name_check.py "候选名一" "候选名二"          # 直接传入候选名
    python name_check.py --file names.txt               # 每行一个候选名
    python name_check.py --file names.txt --json        # 机器可读输出

并非自动判定名称好坏，仅做机械初筛；主体-手段-类型的语义合理性仍需人工结合
references/name_generation.md 判断。
"""

import json
import re
import sys

MAX_LEN = 25

# 无技术含义的营销/空泛词（详见 references/quality_rubric.md 与 name_generation.md）
FLUFF_WORDS = [
    "智能", "高效", "新型", "改进的", "优化", "快速", "完美", "强大",
    "新一代", "革命性", "专利", "独家", "先进", "效果显著", "高精度产品",
]
# 违反名称撰写规范的内容
FORBIDDEN_PATTERNS = [
    ("疑似地名/单位后缀", r"(省|市|县|大学|公司|集团|研究院|研究所|企业|工厂)"),
    ("疑似型号/代号", r"[A-Z]{2,}[-]?\d{2,}"),
    ("宣传语/模糊限定", r"(一代|革命|领先|首创|最强|最好)"),
]
THEME_WORDS = [
    "方法", "装置", "系统", "设备", "电子设备", "存储介质", "芯片",
    "器件", "组件", "材料", "用途", "介质", "服务器", "终端",
]


def check(name):
    name = name.strip()
    fluff_hits = [w for w in FLUFF_WORDS if w in name]
    forbidden_hits = [label for label, pat in FORBIDDEN_PATTERNS if re.search(pat, name)]
    theme_hits = [w for w in THEME_WORDS if w in name]
    cn_len = len(re.findall(r"[\u4e00-\u9fff]", name))
    vis_len = len(re.sub(r"\s", "", name))

    issues = []
    if vis_len > MAX_LEN:
        issues.append(f"超长：{vis_len} 字（限 {MAX_LEN}）")
    if fluff_hits:
        issues.append("空泛/营销词：" + "、".join(fluff_hits))
    if forbidden_hits:
        issues.append("规范问题：" + "、".join(sorted(set(forbidden_hits))))
    if not theme_hits:
        issues.append("未检出主题类型词（方法/装置/系统等）")
    if re.search(r"[!！?？，,。.;；]", name):
        issues.append("含非规范标点")

    return {
        "name": name,
        "zh_chars": cn_len,
        "visible_chars": vis_len,
        "theme_words": theme_hits,
        "issues": issues,
        "pass": not issues,
    }


def render(results):
    out = ["# 候选专利名初筛结果", ""]
    out.append("| 候选名称 | 字数 | 主题类型 | 是否通过 | 问题 |")
    out.append("|---|---|---|---|---|")
    for r in results:
        out.append(
            f"| {r['name']} | {r['visible_chars']} "
            f"| {'、'.join(r['theme_words']) or '—'} "
            f"| {'✅' if r['pass'] else '❌'} | {'；'.join(r['issues']) or '—'} |"
        )
    passed = [r for r in results if r["pass"]]
    out.append("")
    out.append(f"通过初筛：{len(passed)}/{len(results)} 个")
    if not passed:
        out.append("无候选通过初筛，请按 name_generation.md 重新改写。")
    return "\n".join(out)


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)
    names = []
    if args[0] == "--file":
        with open(args[1], encoding="utf-8") as f:
            names = [ln.strip() for ln in f if ln.strip()]
        tail = args[2:]
    else:
        names = [a for a in args if not a.startswith("--")]
        tail = [a for a in args if a.startswith("--")]
    if not names:
        print(__doc__)
        sys.exit(1)
    results = [check(n) for n in names]
    if "--json" in tail:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print(render(results))


if __name__ == "__main__":
    main()
