"""Synchronize appendix source listings from the canonical project programs."""
from pathlib import Path
import hashlib
import json
import re

AUDIT = Path(__file__).resolve().parent
PROJECT = AUDIT.parent.parent
PAPER = PROJECT / "paper/cumcm-1.1.0"

SOURCE_CATALOG = [
    ("code/solve_drying.py", "四问热湿迁移求解、首达判定及收缩模型"),
    ("code/write_results.py", "四份结果工作簿导出与逐项回读核验"),
    ("code/check_numerics.py", "空间网格与时间步长收敛检验"),
    ("code/validate_2d.py", "问题一轴对称二维端面影响检验入口"),
    ("code/validate_long_2d.py", "长期二维与一维配对计算"),
    ("code/verify_revision.py", "轨迹一致性、场量与离散平衡检查"),
    ("code/run_sensitivity.py", "长期环境边界灵敏度计算"),
    ("code/run_q4_counterfactual.py", "同物性固定半径反事实计算"),
    ("code/validate_moving_mesh.py", "独立移动控制体模型与几何守恒检验"),
    ("code/check_moving_mesh_delivery.py", "移动网格验证结果一致性检查"),
    ("code/figure_style.py", "绘图字体、数学排版与缺字检查"),
    ("code/make_figures.py", "四问主要数值结果图绘制"),
    ("code/make_additional_figures.py", "时空场、扩散系数和收缩截面图绘制"),
    ("code/plot_moving_mesh_validation.py", "移动网格与固定域结果对照图绘制"),
    ("code/make_geometry_diagram.py", "药材几何与坐标示意图绘制"),
    ("code/run_figures.sh", "绘图批处理入口及字体环境检查"),
    ("inspect_inputs.py", "题目附件与结果模板结构检查"),
    ("comsol_q1/prepare_inputs.py", "问题一有限元输入准备与结果比较"),
    ("comsol_q1/Q1Automation.java", "问题一有限元建模、求解和剖面导出"),
    ("comsol_q1/run_comsol_q1.ps1", "问题一有限元编译、运行与比较入口"),
    ("comsol_q4/prepare_q4_inputs.py", "问题四有限元物性与边界输入准备"),
    ("comsol_q4/Q4Automation.java", "问题四收缩有限元建模、求解和剖面导出"),
    ("comsol_q4/analyze_q4_comsol.py", "有限元与有限体积数值结果比较"),
    ("comsol_q4/plot_q4_physical.py", "有限元物理剖面和水分场绘制"),
    ("comsol_q4/near_surface_check/analyze_refinement.py", "有限元近表面加密结果分析"),
    ("comsol_q4/near_surface_check/write_report.py", "有限元网格与容差检验结果汇总"),
    ("comsol_q4/near_surface_check/run_cases.ps1", "六组有限元网格与容差算例运行入口"),
]
for case, purpose in [
    ("original_dense", "原始网格加密输出检验"),
    ("original_tight", "原始网格收紧求解容差检验"),
    ("graded80", "近表面分级网格80单元检验"),
    ("graded160", "近表面分级网格160单元检验"),
    ("graded320", "近表面分级网格320单元检验"),
    ("graded320_tight", "近表面分级网格320单元及严格容差检验"),
]:
    SOURCE_CATALOG.append((f"comsol_q4/near_surface_check/{case}/Q4Automation.java", purpose))

selected = {path for path, _ in SOURCE_CATALOG}
discovered = {p.relative_to(PROJECT).as_posix() for p in (PROJECT / "code").iterdir()
              if p.suffix in {".py", ".sh"}}
discovered.add("inspect_inputs.py")
for directory in ("comsol_q1", "comsol_q4"):
    discovered.update(p.relative_to(PROJECT).as_posix()
                      for p in (PROJECT / directory).rglob("*")
                      if p.suffix in {".py", ".java", ".ps1"})
assert selected == discovered, {"missing": sorted(discovered - selected),
                                "unexpected": sorted(selected - discovered)}

def digest(data):
    return hashlib.sha256(data).hexdigest()

def escape(text):
    return text.replace("_", r"\_")

manifest = []
for relative, description in SOURCE_CATALOG:
    source = PROJECT / relative
    original = source.read_bytes()
    text = original.decode("utf-8-sig").replace("\r\n", "\n")
    language = {".py": "Python", ".java": "Java", ".ps1": "PowerShell", ".sh": "Bash"}[source.suffix]
    destination = PAPER / relative if relative.startswith("code/") else PAPER / "code" / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    heading = ("// File: " if language == "Java" else "# File: ") + relative + "\n"
    annotated = heading + text
    destination.write_text(annotated, encoding="utf-8", newline="\n")
    if language == "Python":
        compile(text, relative, "exec")
    assert destination.read_text(encoding="utf-8").split("\n", 1) == [heading.strip(), text]
    manifest.append({
        "source": relative,
        "appendix_copy": destination.relative_to(PAPER).as_posix(),
        "description": description,
        "language": language,
        "first_line": heading.strip(),
        "source_lines": len(text.splitlines()),
        "source_sha256": digest(original),
        "appendix_sha256": digest(destination.read_bytes()),
        "identical_after_filename_comment_and_newline_normalization": True,
    })
(AUDIT / "source_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
(AUDIT / "excluded_appendix_sources.json").write_text("[]\n", encoding="utf-8")

support_path = AUDIT / "support_manifest.json"
support = json.loads(support_path.read_text(encoding="utf-8")) if support_path.exists() else None
# A uses archive paths, so the list remains correct after extracting the package.
rows = [(item["source"], item["description"]) for item in manifest]
if support:
    file_items = support["files"]
    archive_paths = {item["archive_path"] for item in file_items}
    assert selected <= archive_paths, sorted(selected - archive_paths)
    rows.append(("support_manifest.json", "逐文件来源、哈希及可重建资料清单"))
    for item in file_items:
        if item["archive_path"] not in selected:
            rows.append((item["archive_path"], item.get("description", "模型运行与结果核验资料")))
else:
    rows.extend((f"results/result{i}.xlsx", f"问题{i}结果工作簿") for i in range(1, 5))
    rows.append(("AI工具使用详情.pdf", "工具名称、使用环节及人工核验说明"))

a1 = [
    r"\section{支撑材料文件列表}", "",
    r"以下路径均相对于支撑材料压缩包的解压根目录。程序运行环境、执行顺序及可重建文件见包内运行说明。",
    r"\begingroup", r"\small",
    r"\renewcommand{\arraystretch}{1.18}", r"\setlength{\tabcolsep}{5pt}",
    r"\begin{longtable}{>{\centering\arraybackslash}m{0.48\textwidth}>{\centering\arraybackslash}m{0.45\textwidth}}",
    r"\caption{支撑材料及作用}\\", r"\toprule",
    r"文件（相对支撑包根目录） & 作用\\", r"\midrule", r"\endfirsthead",
    r"\multicolumn{2}{c}{表\thetable\quad 支撑材料及作用（续）}\\",
    r"\toprule", r"文件（相对支撑包根目录） & 作用\\", r"\midrule", r"\endhead",
    r"\midrule", r"\multicolumn{2}{c}{续下页}\\", r"\endfoot",
    r"\bottomrule", r"\endlastfoot",
]
def latex_path(path):
    # xeCJK cannot select a CJK font inside the url package verbatim command.
    parts = re.split(r"([\u2e80-\u9fff]+)", path)
    return "".join(part if re.fullmatch(r"[\u2e80-\u9fff]+", part) else r"\path{" + part + "}" for part in parts if part)

for path, description in rows:
    a1.append(latex_path(path) + " & " + description + r"\\")
a1.extend([r"\end{longtable}", r"\endgroup", ""])
(PAPER / "contents/appendix/a1.tex").write_text("\n".join(a1), encoding="utf-8", newline="\n")

a2 = [
    r"\clearpage", r"\section{完整源程序}", "",
    r"以下收录求解、结果导出、数值验证与绘图所用源程序。除首行文件路径注释外，内容与项目对应源码一致；可执行文件及运行说明见支撑材料。",
    r"\begingroup",
    r"\IfFontExistsTF{Menlo}{\newfontfamily\appendixcodefont{Menlo}}{\newfontfamily\appendixcodefont{Consolas}}",
    r'\xeCJKDeclareCharClass{CJK}{"2103}',
    r"\lstset{basicstyle=\small\appendixcodefont,breaklines=true,breakatwhitespace=false,columns=fullflexible,keepspaces=true,tabsize=4,showstringspaces=false,numbers=none}",
    "",
]
for index, item in enumerate(manifest, 1):
    source = Path(item["source"])
    name = source.name
    if name == "Q4Automation.java" and "near_surface_check" in source.parts:
        name += "（" + source.parent.name + "）"
    title = escape(name)
    language = {"Python": "Python", "Java": "Java", "Bash": "bash", "PowerShell": ""}[item["language"]]
    a2.extend([
        r"\subsection{\texorpdfstring{\texttt{" + title + "}}{" + title + "}}",
        r"\label{app:source" + str(index) + "}", "",
        r"\lstinputlisting[language={" + language + "}]{" + item["appendix_copy"] + "}",
        r"\label{app:source" + str(index) + "end}", "",
    ])
a2.extend([r"\endgroup", ""])
(PAPER / "contents/appendix/a2.tex").write_text("\n".join(a2), encoding="utf-8", newline="\n")
print(json.dumps({"source_files": len(manifest),
                  "total_original_lines": sum(item["source_lines"] for item in manifest),
                  "support_list_rows": len(rows),
                  "support_manifest_loaded": support is not None,
                  "canonical_files_modified": 0}, ensure_ascii=False))
