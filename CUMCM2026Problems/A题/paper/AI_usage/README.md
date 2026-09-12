# AI 工具使用详情

- `AI工具使用详情.pdf`：正式阅读版，共 3 页。
- `AI_usage.tex`：LaTeX 源文件。
- `AI_usage.pdf`：与正式阅读版内容相同的同步副本。
- `build.ps1`：XeLaTeX 编译脚本，辅助文件存放于 `build/`。

## 本轮调整（2026-09-13）

根据用户说明，突出建模思路来自队员对题意与附件数据的分析，模型假设、控制方程及求解方案由队员讨论确定；AI 在已有建模思路下提供具体协助。相应调整开头、模型讨论、程序实现与建议取舍段落。

保留四个一级章节、十个小节、三个提示示例及三个处理案例，详细程度和 3 页篇幅不变。工具信息、具体用途及代码与核验记录继续保留，没有改称仅用于润色或极少使用。

使用原 CUMCM 类文件、西文字体和 Windows 宋体、黑体。新版已成功编译并逐页检查。

## 编译

安装 XeLaTeX 后，在本目录运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1
```

本轮使用本机已有 Tectonic 编译，自动完成交叉引用重跑，并同步两个阅读版及 `build/AI_usage.pdf`。Tectonic 首次运行需获取宏包，字体查找需配置本机 Windows 字体目录；后续可使用缓存。原 XeLaTeX 构建入口保持不变。

## 内容依据

工具型号、日期和主要输入沿用原稿。处理实例以 `results/revision_checks.json`、`results/numerical_verification.json`、收缩模型验证记录及 `reports/VERIFY_REPORT.md` 为依据，路径相对于 A 题目录。

典型提示为归纳表述；程序校验记录用于复核，不能代替人工审核记录。本轮仅修改本说明，未修改主论文和仿真结果。
