#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""框架合规反思：按步骤输出自查问题。

用法：
    python reflect.py novelty    # 查重检索环节
    python reflect.py scoring    # 质量评分环节
    python reflect.py naming     # 建议专利名环节
"""

import sys

QUESTIONS = {
    "novelty": [
        "是否执行了三轮检索式（全特征、两两组合、上位加 IPC）？",
        "是否为每个核心区别特征准备了至少两个关键词变体（俗称、标准术语、英文）？",
        "最接近的 3-5 份文件是否记录了公开号与申请日，并交叉验证了来源？",
        "是否检查过申请日早于本专利、公开日晚于本专利的抵触申请？",
        "除新颖性判定外，是否检查了惯用手段的直接置换情形？",
        "风险等级依据是否引用了具体文件编号，而不是泛泛的结论？",
        "非 Google Patents 详情页直接命中的文件（文档站、快照、自媒体）是否已逐条回验？回验失败的是否已标记「未经核实」并排除出判级依据？",
        "报告中的申请人、申请日、公开日是否与回验结果一致，而非照抄检索摘要？",
        "是否检索过外文同族（如 country=US），避免漏掉先于国内公开的同族申请？",
    ],
    "scoring": [
        "每个维度都给出了 0-5 分吗？材料缺失的维度是否明确标注为 0 并列入待补充清单？",
        "每个给分是否都附带了扣分点与具体修改建议？",
        "所给分数是否可在原文中找到支撑（段落号、权利要求序号、标号）？",
        "名称评分是否同时检查了领域、技术手段、区别点、字数四项？",
        "内容评分中权重最高的「技术手段具体性」是否按可重现标准判断？",
        "是否存在因用户期待高分而抬高分数的情况？",
        "总分是否由 scripts/score.py 计算，而非手工估算？",
    ],
    "naming": [
        "是否询问过用户是否需要建议名称？",
        "每个建议名称是否包含领域、具体技术手段、主题类型词三要素？",
        "是否避免使用产品名、商标、宣传语、空泛形容词（如「智能」「高效」「新型」）？",
        "每个候选是否控制在 25 字以内（最多不超过 30 字）？",
        "是否用 scripts/name_check.py 完成初筛并据结果修正？",
        "是否用 AskUserQuestion 让用户选择，而非自行替用户决定？",
    ],
}


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    if not args or args[0] not in QUESTIONS:
        print("用法：python reflect.py <novelty|scoring|naming>")
        sys.exit(1)
    key = args[0]
    print(f"# {key} 环节反思清单\n")
    for i, q in enumerate(QUESTIONS[key], 1):
        print(f"{i}. {q}")
    print("\n逐项确认，存在「否」时回到对应环节修正后再继续。")


if __name__ == "__main__":
    main()
