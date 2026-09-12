from pathlib import Path
import hashlib
import json

AUDIT = Path(__file__).parent
PROJECT = AUDIT.parent.parent
PAPER = PROJECT / 'paper/cumcm-1.1.0'

SOURCE_CATALOG = [
    ('code/solve_drying.py', '四问热湿迁移求解、首达判定及收缩模型'),
    ('code/write_results.py', '四份结果工作簿导出与逐项回读核验'),
    ('code/check_numerics.py', '空间网格与时间步长收敛检验'),
    ('code/validate_2d.py', '问题一轴对称二维端面影响检验入口'),
    ('code/validate_long_2d.py', '长期二维与一维配对计算'),
    ('code/verify_revision.py', '轨迹一致性、场量与离散平衡检查'),
    ('code/run_sensitivity.py', '长期环境边界灵敏度计算'),
    ('code/run_q4_counterfactual.py', '同物性固定半径反事实计算'),
    ('code/validate_moving_mesh.py', '独立移动控制体模型与几何守恒检验'),
    ('code/check_moving_mesh_delivery.py', '移动网格验证结果一致性检查'),
    ('code/make_figures.py', '四问主要数值结果图绘制'),
    ('code/make_additional_figures.py', '时空场、扩散系数和收缩截面图绘制'),
    ('code/plot_moving_mesh_validation.py', '移动网格与固定域结果对照图绘制'),
    ('code/make_geometry_diagram.py', '药材几何与坐标示意图绘制'),
    ('inspect_inputs.py', '题目附件与结果模板结构检查'),
    ('comsol_q1/prepare_inputs.py', '问题一有限元输入准备'),
    ('comsol_q4/prepare_q4_inputs.py', '问题四有限元物性与边界输入准备'),
    ('comsol_q4/analyze_q4_comsol.py', '有限元与有限体积数值结果比较'),
    ('comsol_q4/plot_q4_physical.py', '有限元物理剖面和水分场绘制'),
    ('comsol_q4/near_surface_check/analyze_refinement.py', '有限元近表面加密结果分析'),
    ('comsol_q4/near_surface_check/write_report.py', '有限元网格与容差检验结果汇总'),
]

# Final scope confirmed by the user: core solution and manuscript plotting only.
SELECTED = {
    'code/solve_drying.py',
    'code/run_q4_counterfactual.py',
    'code/make_figures.py',
    'code/make_additional_figures.py',
    'code/plot_moving_mesh_validation.py',
    'code/make_geometry_diagram.py',
    'comsol_q4/plot_q4_physical.py',
}
SOURCES = [(path, purpose) for path, purpose in SOURCE_CATALOG if path in SELECTED]
assert len(SOURCES) == 7

def digest(data):
    return hashlib.sha256(data).hexdigest()

def escape(text):
    return text.replace('_', r'\_')

manifest_path = AUDIT / 'source_manifest.json'
if manifest_path.exists():
    previous_manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    for item in previous_manifest:
        if item['source'] in SELECTED:
            continue
        copied = (PAPER / item['appendix_copy']).resolve()
        assert copied.is_relative_to((PAPER / 'code').resolve())
        # Undo only the appendix copies made by this operation; project sources stay intact.
        assert digest(copied.read_bytes()) == item['appendix_sha256']
        original_copy = AUDIT / 'before' / item['appendix_copy']
        if original_copy.exists():
            copied.write_bytes(original_copy.read_bytes())
        else:
            copied.unlink()

manifest = []
for relative, description in SOURCES:
    src = PROJECT / relative
    original = src.read_bytes()
    text = original.decode('utf-8-sig').replace('\r\n', '\n')
    destination = PAPER / relative if relative.startswith('code/') else PAPER / 'code' / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    heading = '# File: ' + relative + '\n'
    annotated = heading + text
    destination.write_text(annotated, encoding='utf-8', newline='\n')
    compile(annotated, relative, 'exec')
    assert destination.read_text(encoding='utf-8').split('\n', 1)[1] == text
    manifest.append({
        'source': relative,
        'appendix_copy': destination.relative_to(PAPER).as_posix(),
        'description': description,
        'first_line': heading.strip(),
        'source_lines': len(text.splitlines()),
        'source_sha256': digest(original),
        'appendix_sha256': digest(destination.read_bytes()),
        'identical_after_filename_comment_and_newline_normalization': True,
    })

assert {item['source'] for item in manifest} == SELECTED
assert (PROJECT/'paper/AI_usage/AI工具使用详情.pdf').is_file()
manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
(AUDIT/'excluded_appendix_sources.json').write_text(json.dumps([path for path, _ in SOURCE_CATALOG if path not in SELECTED],ensure_ascii=False,indent=2),encoding='utf-8')

# Longtable can continue onto another appendix page without changing body pagination.
a1 = [
    r'\section{支撑材料文件列表}', '',
    r'\begingroup', r'\small',
    r'\renewcommand{\arraystretch}{1.18}',
    r'\setlength{\tabcolsep}{5pt}',
    r'\begin{longtable}{>{\centering\arraybackslash}m{0.48\textwidth}>{\centering\arraybackslash}m{0.45\textwidth}}',
    r'\caption{支撑材料及作用}\\',
    r'\toprule', r'文件（相对项目目录） & 作用\\', r'\midrule', r'\endfirsthead',
    r'\multicolumn{2}{c}{表\thetable\quad 支撑材料及作用（续）}\\',
    r'\toprule', r'文件（相对项目目录） & 作用\\', r'\midrule', r'\endhead',
    r'\midrule', r'\multicolumn{2}{c}{续下页}\\', r'\endfoot',
    r'\bottomrule', r'\endlastfoot',
]
for relative, description in SOURCES:
    a1.append(r'\path{'+relative+r'} & '+description+r'\\')
for name, description in [
    ('result1.xlsx', '问题一前1800秒，每1秒、0.1厘米的温度和水分结果'),
    ('result2.xlsx', '问题二前3小时，每1秒、0.1厘米的温度和水分结果'),
    ('result3.xlsx', '问题三至达标，每60秒、0.1厘米的水分结果'),
    ('result4.xlsx', '问题四至达标，每60秒的固定物理位置及动态表面水分'),
]:
    a1.append(r'\path{results/'+name+r'} & '+description+r'\\')
a1.append(r'AI工具使用详情.pdf & AI工具名称、使用环节及人工核验说明\\')
a1 += [r'\end{longtable}', r'\endgroup', '']
(PAPER/'contents/appendix/a1.tex').write_text('\n'.join(a1),encoding='utf-8')

a2 = [r'\clearpage', r'\section{核心求解与绘图源程序}', '',
      r'\begingroup',
      r'\newfontfamily\appendixcodefont{Consolas}',
      r'\xeCJKDeclareCharClass{CJK}{"2103}',
      r'\lstset{language=Python,basicstyle=\small\appendixcodefont,breaklines=true,breakatwhitespace=false,columns=fullflexible,keepspaces=true,tabsize=4,showstringspaces=false,numbers=none}', '']
for index, item in enumerate(manifest):
    name = Path(item['source']).name
    a2 += [r'\subsection{\texorpdfstring{\texttt{'+escape(name)+r'}}{'+escape(name)+r'}}',
           r'\label{app:source'+str(index+1)+'}', '',
           r'\lstinputlisting{'+item['appendix_copy']+'}',
           r'\label{app:source'+str(index+1)+'end}', '']
a2 += [r'\endgroup', '']
(PAPER/'contents/appendix/a2.tex').write_text('\n'.join(a2),encoding='utf-8')
print(json.dumps({'source_files':len(manifest),'total_original_lines':sum(item['source_lines'] for item in manifest),'canonical_files_modified':0},ensure_ascii=False))
