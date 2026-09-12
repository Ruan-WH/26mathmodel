# AI 工具使用详情

- `AI工具使用详情.pdf`：按新截图指定文件名生成的提交阅读版，共3页。
- `AI_usage.tex`：LaTeX源文件。
- `AI_usage.pdf`：与提交阅读版完全一致的同步副本，保留原有文件链接。
- `build.ps1`：XeLaTeX编译脚本，辅助文件存放于`build/`。

## 本轮调整

按新截图改为四个章节：所用AI工具名称、版本或型号；具体使用目的和环节；主要提示方式与使用过程说明；对AI输出的采纳、人工修改和校验的主要情况。

型号按用户补充写为GPT6，使用日期为2026年9月10日至13日，使用形式为对话讨论、代码辅助实现与调试、LaTeX排版，主要输入为赛题及附件、队员建模文档、报错信息等。删除指定的图形制作相关段落，将对应示例改为“一致性复查”；原独立核验清单并入第四章的职责与校验说明，压缩重复叙述。

排版继续复用论文的CUMCM类文件与字体。表1增加单元格行距、行高和上下留白，保留加粗表头、上置表题及三线表。

## 编译

在本目录运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1
```

整个文件夹包含独立编译所需的模板与西文字体；仍需安装XeLaTeX、模板依赖宏包及Windows中文字体。

## 内容依据

型号、日期和主要输入采用用户本轮补充信息。三个处理实例对应项目内以下记录（路径相对于A题根目录）：

- `results/revision_checks.json`、`results/numerical_verification.json`：共享轨迹及离散精度校验。
- `reports/Q4_MOVING_MESH_PRINCIPLE.md`、`reports/Q4_MOVING_MESH_DELIVERY.md`：收缩条件与配对实现。
- `results/paper_table_audit.json`、`reports/VERIFY_REPORT.md`：论文数值与结果文件核对。

典型提示语为归纳表述，不作为逐字历史对话。职责表述不等同于逐项人工完成记录。本轮未改动原论文工程。
