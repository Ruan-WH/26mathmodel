---
name: typst-author
description: "创建、编辑、排错和编译 Typst 文档；仅在用户明确要求 Typst 或其他项目已有 .typ 文件时使用，不用于本项目固定的 CUMCM LaTeX 写作流程。"
---

# Typst 辅助

本 skill 保留给独立 Typst 任务。本数学建模工作流的 `5writing` 已固定为 CUMCM LaTeX，不调用本 skill，除非用户明确改变排版要求。

处理 Typst 时优先查本目录 `docs/` 的本地文档，内部记忆可能落后。根据任务读取相关教程、指南和 reference 文件，确认函数名、参数与语法后再编辑。

## 工作流

1. 定位入口、include/import 关系和现有样式。
2. 查阅与本次编辑直接相关的本地文档。
3. 最小化修改，避免混入 LaTeX 语法；数组用 `()`，内容块用 `[]`，在 markup 中进入代码使用 `#`。
4. 若有 `typstyle`，先运行 `typstyle --check`；格式化不得波及未编辑的用户代码。
5. 使用 `typst compile` 验证，并检查生成 PDF 的布局与字体。
6. 报告修改文件、编译结果与剩余警告。

大项目用 `#include` 分文件；遇到不确定的运行行为，先查文档，再用最小探针验证。
