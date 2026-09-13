"""Build an auditable support ZIP without executing or changing model code/data."""
from __future__ import annotations

import ast
import hashlib
import io
import json
from pathlib import Path
import sys
import zipfile
import zlib

AUDIT = Path(__file__).resolve().parent
PROJECT = AUDIT.parent.parent
DESTINATION = PROJECT / "support_materials_20260913.zip"
MANIFEST = AUDIT / "support_manifest.json"
LIMIT = 20_000_000
# Reserve room for the final appendix PDF, README, manifest and ZIP headers.
PAYLOAD_LIMIT = 18_800_000
SOURCE_SUFFIXES = {".py", ".java", ".ps1", ".sh"}
DATA_SUFFIXES = {".json", ".csv", ".npz", ".xlsx", ".txt"}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def source_files() -> list[Path]:
    paths = [PROJECT / "inspect_inputs.py"]
    for folder in ("code", "comsol_q1", "comsol_q4"):
        paths.extend(p for p in (PROJECT / folder).rglob("*")
                     if p.is_file() and p.suffix.lower() in SOURCE_SUFFIXES)
    return sorted(paths)


def description(relative: str) -> str:
    name = Path(relative).name
    if Path(relative).suffix in SOURCE_SUFFIXES:
        if relative.startswith("comsol"):
            return "COMSOL模型、输入准备、比较或运行源程序"
        return "建模、求解、结果导出、验证或绘图源程序"
    if relative.startswith("附件/"):
        return "题目原始输入数据或结果工作簿模板"
    if name.startswith("result") and name.endswith(".xlsx"):
        return "题目要求的正式结果工作簿"
    if relative.startswith("comsol"):
        return "COMSOL输入、导出数据或数值比较记录"
    if relative.startswith("results/"):
        return "已保存的计算场、汇总结果或验证记录"
    if relative.endswith("main.pdf"):
        return "当前完整论文；供附录与结果核对"
    if relative.endswith("AI工具使用详情.pdf"):
        return "AI工具使用情况说明"
    return "支撑材料运行及文件核验说明"


def rebuild_command(relative: str) -> str:
    if relative == "results/q4/fixed_radius_counterfactual.npz":
        return "python code/run_q4_counterfactual.py"
    if relative == "results/q2/fields.npz":
        return "python code/solve_drying.py --skip-convergence"
    if relative == "results/q4/validation_moving_mesh/fields.npz":
        return "python code/validate_moving_mesh.py"
    if relative.startswith("comsol_q4/near_surface_check/"):
        case = Path(relative).parent.name
        return (f"在 comsol_q4/near_surface_check/{case}/ 修正 WORK_DIR 后，"
                "用 COMSOL 6.3 的 comsolcompile 和 comsolbatch 执行同目录 Q4Automation.java")
    raise ValueError(f"No reconstruction recipe: {relative}")


def readme(omitted: list[dict], source_count: int) -> bytes:
    omitted_lines = "\n".join(
        f"- {item['archive_path']}（原件 {item['size_bytes']:,} 字节）：{item['rebuild_command']}"
        for item in omitted)
    text = f"""# 数学建模支撑材料运行说明

本包对应当前论文与项目源码，ZIP根目录即项目目录，保持 code/、results/、附件/、comsol_q1/、comsol_q4/ 和 paper/ 的相对位置。
共收录 {source_count} 份建模、结果导出、验证、绘图及COMSOL运行源码；源码、原始附件和已收录数值资料均按原字节复制。
本轮仅同步源文件、补齐依赖、核对文件并打包，没有重新运行模型、修改模型公式或更新计算数值。
support_manifest.json 给出逐文件作用、原项目路径和 SHA-256；其 files 列表不自包含该清单的哈希。

## 文件与体积

- code/ 与 inspect_inputs.py：Python建模、求解、导出、二维/移动网格/灵敏度验证、绘图及原运行入口。
- comsol_q1/、comsol_q4/：全部相关Python、Java和PowerShell源文件，边界输入、保留的剖面与比较数据；近表面六种网格/容差算例Java源码均保留。
- 附件/：附件1、附件2和附件3内四个原始输出模板。
- results/result1.xlsx 至 result4.xlsx：现有正式结果文件，未重新导出。
- results/其余条目：保留的原始计算场、摘要及核验记录，具体以清单为准。
- paper/cumcm-1.1.0/main.pdf：本轮最终编译论文副本，用于部分已有核验程序的PDF依赖。
- AI工具使用详情.pdf：与正式中文阅读版完全一致。

为满足ZIP不超过20 MB，以下较大中间场或非最终COMSOL逐时导出数据未收录；未压缩精度、抽样或改写这些数值资料，原始工程中仍有原件，完整重建源码和输入已保留：
{omitted_lines or '- 无。'}

COMSOL .mph、.class、恢复文件、运行日志和图件预览不纳入本包；.mph可由相应Java源程序重建。普通ZIP解压即可读取中文路径。

## 环境与执行位置

使用Python 3.11或更新版本；计算/导出依赖 numpy、scipy、openpyxl，绘图依赖 matplotlib，PDF交付核验依赖 PyMuPDF（import pymupdf）。
如需创建独立环境，可安装上述库；本次打包没有安装依赖。
绘图程序明确要求 Times New Roman Regular 和 SimSun Regular（宋体），缺少字体时会报错；应先安装字体或在具有这两种字体的Windows环境运行。
本文的数学变量字体还使用 Times New Roman italic/bold。不要以缺字方框或自动替代字体结果作为论文图。
所有下面的Python命令均从本说明所在的解压根目录执行。程序会在解压副本写入新计算/图表/报告；重算耗时与模型规模有关。
推荐在独立解压副本复现，保留提交原件及清单作为比较基准。

## Python复现顺序

1. 检查输入：python inspect_inputs.py
2. 重建四问主模型及缺失的q2场：python code/solve_drying.py --skip-convergence
   该命令以原程序配置从初始状态求解全部四问；--skip-convergence仅跳过附带收敛循环，收敛检验另见步骤4。
3. 固定半径反事实与工作簿：python code/run_q4_counterfactual.py；随后 python code/write_results.py。
   write_results.py读取附件3原模板及主场，按原导出逻辑生成四份工作簿。本包保留当前逻辑，包括第二问导出前3小时的既有范围，未借同步源码改变答案。
4. 各独立检验按需运行：python code/check_numerics.py；python code/validate_2d.py；python code/validate_long_2d.py；python code/run_sensitivity.py；python code/verify_revision.py。
   validate_long_2d.py保留已有问题一记录，每次运行都会重新计算问题三、四的四组长期二维算例；不会因已有记录而跳过这些长期算例。
5. 重建移动网格完整场：python code/validate_moving_mesh.py。
   该步骤会重新生成本次未打包的大字段，并创建与当前解压副本对应的保护清单。--check-only仅做物理/离散检查，不重建完整场。
6. 绘图：python code/make_figures.py；python code/make_additional_figures.py；python code/make_geometry_diagram.py；python code/plot_moving_mesh_validation.py --figures-only。
   移动网格绘图必须在步骤5完成后运行；--figures-only使用保存场绘图，避免把旧历史保护哈希作为新改版基线。
7. PDF与移动网格交付核验可在步骤5后运行：python code/check_moving_mesh_delivery.py --skip-build-check。
   这会明确记录“未验证本次LaTeX构建”；本包不含LaTeX编译日志。完整构建核验须在对应论文工程提供当前编译日志并通过 --log 指定，不能把部分核验当作完整编译通过。

以上为复现说明，未表示本次已执行这些模型计算。包内已保存的验证JSON中的日期和SHA属于各次原始记录；不能把历史快照视为当前文件的通过结论。

## COMSOL复现与已有数据查看

需要已安装且可使用的COMSOL Multiphysics 6.3（含Java API批处理能力）；Python不能代替COMSOL求解Java模型。
所有Java和PowerShell文件保留原件。它们带有原开发机路径，运行前必须在解压副本调整路径：
- comsol_q1/Q1Automation.java 的 DEFAULT_WORK_DIR 原为 D:\\COMSOL\\test。
- comsol_q4/Q4Automation.java 及 near_surface_check 各 Q4Automation.java 的 WORK_DIR 原为 D:\\26mathmodel\\CUMCM2026Problems\\A题\\...，须改为各Java文件所在绝对目录。
- comsol_q1/run_comsol_q1.ps1 的 ComsolBin、WorkDir、ProjectToolDir、Python路径，以及 near_surface_check/run_cases.ps1 中COMSOL和Python可执行文件路径，须改为本机实际位置。
- 若使用问题一原PowerShell入口，需把 Q1Automation.java 放入其 WorkDir；也可把 WorkDir/DEFAULT_WORK_DIR统一到包内comsol_q1目录后执行。
- code/run_figures.sh 是原macOS/zsh入口，含Homebrew expat路径和Songti SC字体预检，与本轮SimSun配置不同；本包建议使用上文直接Python命令，原入口只为完整留存，不能在Windows直接执行。

问题一：运行 python comsol_q1/prepare_inputs.py 准备输入；在comsol_q1工作目录执行 comsolcompile Q1Automation.java，再 comsolbatch -inputfile Q1Automation.class。
随后运行 python comsol_q1/prepare_inputs.py comsol_q1/q1_comsol_profiles.csv 生成比较。
问题四：python comsol_q4/prepare_q4_inputs.py 准备温度、水分和半径输入；在comsol_q4工作目录编译/批处理 Q4Automation.java。
包内已保留问题四初始与最终 graded320_tight 原始导出CSV，可直接用 python comsol_q4/analyze_q4_comsol.py 和 python comsol_q4/plot_q4_physical.py --refined 处理已保存数据；这不是重新执行COMSOL。
完整六算例收敛表须先在六个子目录分别编译/求解，或修正路径后使用 near_surface_check/run_cases.ps1，再运行 analyze_refinement.py 和 write_report.py。
注意 analyze_refinement.py 会跳过缺失算例；若仅有包内保留的最终CSV，重新分析不能声称已复现完整六算例。需要重建的CSV在前述清单中逐一列出。
COMSOL历史manifest带Windows反斜杠路径，相关保护检查应在Windows执行；旧SHA与本次论文不同会记录False，是历史版本差异，不是本次重新计算数值出错的证据。

## 文件核验与范围

所有源码的包内SHA-256都与当前项目原件核对；Python源码只做语法解析，没有执行其顶层计算。
本包包含全部33份实际建模/验证/绘图相关源文件。打包脚本属于交付工具，保留于原项目 reports/appendix_results_20260913/build_support_package.py，不作为建模程序计数。
解压后可依 support_manifest.json 逐个计算SHA-256，确认传输未改变内容。
源码所需本地Python模块均已收录；较大可重建中间结果的缺失和COMSOL路径条件已明确说明。
"""
    return text.encode("utf-8")


def build() -> dict:
    sources = source_files()
    if len(sources) != 33:
        raise ValueError(f"Source inventory changed: expected 33, found {len(sources)}")
    for path in sources:
        if path.suffix == ".py":
            ast.parse(path.read_text(encoding="utf-8-sig"), filename=path.name)
    files: dict[str, tuple[Path | None, bytes]] = {}
    for path in sources:
        files[path.relative_to(PROJECT).as_posix()] = (path, path.read_bytes())
    for path in (PROJECT / "附件").rglob("*.xlsx"):
        files[path.relative_to(PROJECT).as_posix()] = (path, path.read_bytes())
    candidates = []
    for folder in ("results", "comsol_q1", "comsol_q4"):
        for path in (PROJECT / folder).rglob("*"):
            if not path.is_file() or path.suffix.lower() not in DATA_SUFFIXES:
                continue
            if path.name == "interim_analysis.txt" or "figures" in path.parts:
                continue
            relative = path.relative_to(PROJECT).as_posix()
            if path.stat().st_size > 10_000_000 or relative == "results/q4/fixed_radius_counterfactual.npz":
                candidates.append(path)
            else:
                files[relative] = (path, path.read_bytes())
    paper = PROJECT / "paper/cumcm-1.1.0/main.pdf"
    files[paper.relative_to(PROJECT).as_posix()] = (paper, paper.read_bytes())
    ai = PROJECT / "paper/AI_usage/AI工具使用详情.pdf"
    files["AI工具使用详情.pdf"] = (ai, ai.read_bytes())

    compressed_estimate = sum(len(zlib.compress(data, 9)) for _, data in files.values())
    omitted = []
    # Prefer the exact final COMSOL comparison used in the manuscript.
    candidates.sort(key=lambda p: ("graded320_tight" not in p.parts, p.as_posix()))
    for path in candidates:
        relative = path.relative_to(PROJECT).as_posix()
        data = path.read_bytes()
        compressed_size = len(zlib.compress(data, 9))
        if compressed_estimate + compressed_size <= PAYLOAD_LIMIT:
            files[relative] = (path, data)
            compressed_estimate += compressed_size
        else:
            omitted.append(dict(archive_path=relative, source=relative,
                                size_bytes=len(data), sha256=digest(data),
                                compressed_size_bytes=compressed_size,
                                reason="超过20 MB提交包体积约束；保留完整源码与输入供重建",
                                rebuild_command=rebuild_command(relative)))
    final_csv = "comsol_q4/near_surface_check/graded320_tight/q4_comsol_profiles.csv"
    if final_csv not in files:
        raise ValueError("Final COMSOL profiles did not fit; review package budget")
    files["README.md"] = (None, readme(omitted, len(sources)))
    appendix_path = AUDIT / "source_manifest.json"
    appendix = json.loads(appendix_path.read_text(encoding="utf-8"))
    appendix_sources = {item["source"] for item in appendix}
    canonical_sources = {path.relative_to(PROJECT).as_posix() for path in sources}
    crosscheck = dict(equal=appendix_sources == canonical_sources,
                      missing_from_appendix=sorted(canonical_sources - appendix_sources),
                      missing_from_package=sorted(appendix_sources - canonical_sources))
    manifest = dict(schema_version=1, source_count=len(sources),
                    size_limit_bytes=LIMIT, appendix_crosscheck=crosscheck,
                    verification_scope="文件逐字节与哈希核对、Python语法解析、ZIP完整性；未运行仿真",
                    files=[dict(source=path.relative_to(PROJECT).as_posix() if path else None,
                                archive_path=name, description=description(name),
                                size_bytes=len(data), sha256=digest(data))
                           for name, (path, data) in sorted(files.items())],
                    omitted_rebuildable=omitted)
    manifest_bytes = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    archive_buffer = io.BytesIO()
    with zipfile.ZipFile(archive_buffer, "w", compression=zipfile.ZIP_DEFLATED,
                         compresslevel=9, strict_timestamps=False) as archive:
        for name, (_, data) in sorted(files.items()):
            archive.writestr(name, data)
        archive.writestr("support_manifest.json", manifest_bytes)
        # Existing source programs copy figures/tables into these destinations.
        for directory in ("figures/", "drawio/", "paper/cumcm-1.1.0/figures/",
                          "paper/cumcm-1.1.0/contents/sections/"):
            archive.writestr(directory, b"")
    payload = archive_buffer.getvalue()
    if len(payload) > LIMIT:
        raise ValueError(f"ZIP too large: {len(payload):,} > {LIMIT:,}")
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        if archive.testzip() is not None:
            raise ValueError("ZIP integrity check failed")
        for name, (path, data) in files.items():
            if archive.read(name) != data or (path and path.read_bytes() != data):
                raise ValueError(f"File changed during packaging: {name}")
    # Only the owned ZIP and support manifest are written after all checks pass.
    DESTINATION.write_bytes(payload)
    MANIFEST.write_bytes(manifest_bytes)
    result = dict(zip_bytes=len(payload), zip_sha256=digest(payload),
                  files=len(files), source_count=len(sources),
                  omitted_rebuildable=len(omitted), appendix_crosscheck=crosscheck,
                  manifest=str(MANIFEST))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    build()
