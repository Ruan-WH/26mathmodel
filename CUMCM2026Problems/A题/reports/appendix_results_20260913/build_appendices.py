"""Synchronize appendix source listings from the canonical project programs."""
from pathlib import Path
import hashlib
import json
import re
import sys

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
    ("inspect_inputs.py", "题目附件与结果模板结构检查"),
    ("comsol_q1/prepare_inputs.py", "问题一有限元输入准备与结果比较"),
    ("comsol_q4/prepare_q4_inputs.py", "问题四有限元物性与边界输入准备"),
    ("comsol_q4/analyze_q4_comsol.py", "有限元与有限体积数值结果比较"),
    ("comsol_q4/plot_q4_physical.py", "有限元物理剖面和水分场绘制"),
    ("comsol_q4/near_surface_check/analyze_refinement.py", "有限元近表面加密结果分析"),
    ("comsol_q4/near_surface_check/write_report.py", "有限元网格与容差检验结果汇总"),
]
selected = {path for path, _ in SOURCE_CATALOG}
discovered = {p.relative_to(PROJECT).as_posix() for p in (PROJECT / "code").iterdir()
              if p.suffix == ".py"}
discovered.add("inspect_inputs.py")
for directory in ("comsol_q1", "comsol_q4"):
    discovered.update(p.relative_to(PROJECT).as_posix()
                      for p in (PROJECT / directory).rglob("*")
                      if p.suffix == ".py")
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
    language = "Python"
    destination = PAPER / relative if relative.startswith("code/") else PAPER / "code" / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    heading = "# File: " + relative + "\n"
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

if "--sources-only" in sys.argv:
    print(json.dumps({"source_files": len(manifest), "source_copies_synchronized": True}))
    raise SystemExit(0)

# All appendix-B Python sources are archived under the code folder;
# the four result workbooks and the AI-use document remain at ZIP root.
support_path = PROJECT / "reports/python_delivery_20260913/support_manifest.json"
support = json.loads(support_path.read_text(encoding="utf-8"))
rows = [(item["archive_path"], item["description"]) for item in support["files"]]
assert all("\\" not in path for path, _ in rows)
assert {"代码/" + Path(item["source"]).name for item in manifest} <= {path for path, _ in rows}

a1 = [
    r"\section{支撑材料文件列表}", "",
    r"压缩包根目录存放四份结果工作簿及 AI 使用说明；附录 B 的全部 22 份 Python 程序直接放在“代码”文件夹下，不设子文件夹。运行 Python 前须按附录 B 首行来源路径恢复工程目录，并配合题给附件及相应计算数据。以下路径均相对于压缩包根目录。",
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
    r"以下完整收录求解、结果导出、数值验证与绘图使用的 22 份 Python 源程序。除首行来源路径注释外，内容与支撑材料“代码”文件夹内对应程序一致。COMSOL 相关 Python 程序用于输入准备和既有计算结果的对照分析。",
    r"\begingroup",
    r"\IfFontExistsTF{Menlo}{\newfontfamily\appendixcodefont{Menlo}}{\newfontfamily\appendixcodefont{Consolas}}",
    r'\xeCJKDeclareCharClass{CJK}{"2103}',
    r"\lstset{basicstyle=\small\appendixcodefont,breaklines=true,breakatwhitespace=false,columns=fullflexible,keepspaces=true,tabsize=4,showstringspaces=false,numbers=none}",
    "",
]
for index, item in enumerate(manifest, 1):
    source = Path(item["source"])
    name = source.name
    title = escape(name)
    language = "Python"
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
