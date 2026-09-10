from pathlib import Path
import shutil

p=Path(__file__).resolve().parents[2]
f=p/'reports/RESULTS_REPORT.md'
title='## 2026-09-11 新增图形'
if title not in f.read_text(encoding='utf8'):
    with f.open('a',encoding='utf8') as stream:
        stream.write('\n\n'+title+'\n\n保持既有原图不变，新增 Q1 温度曲面、Q2 水分曲面与扩散系数云图、Q3 达标区域、Q4 收缩水分场与等比例截面。全部来自当前终算数据；图形契约、数值范围、来源校验和图文位置见 reports/figure_additions_20260911/。论文图 3、5、6、8、11 分别位于第 13、17、17、21、26 页。\n')
f=p/'reports/AI_USAGE.md'
text='2026-09-11 图形增补：依据用户粘贴的可视化建议，使用既有终算数据新增五张图并补充图文解读；以代码进行原图哈希、数据范围、字体嵌入和交叉引用检查，AI 查看单图及论文页面。最终人工审查由用户完成。'
if text not in f.read_text(encoding='utf8'):
    with f.open('a',encoding='utf8') as stream:
        stream.write('\n- '+text+'\n')
shutil.copy2(p/'code/make_additional_figures.py',p/'paper/cumcm-1.1.0/code/make_additional_figures.py')
shutil.copy2(p/'paper/cumcm-1.1.0/main.pdf',p/'A题_完整论文.pdf')
assert (p/'A题_完整论文.pdf').read_bytes()==(p/'paper/cumcm-1.1.0/main.pdf').read_bytes()
print('Final PDF and supporting records synchronized.')
