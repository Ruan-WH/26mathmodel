"""平铺支撑材料：主模型求解与主结果绘图。
环境：Python 3.11+，numpy、scipy、matplotlib；绘图需安装 Times New Roman
及 SimSun（宋体）字体。本交付副本无需外部输入Excel，附件1/2原始数值由同目录
input_data.py提供；数据来源和原始文件SHA-256写在该模块。
从解压根目录依次执行：
  python solve_drying.py --skip-convergence
  python run_q4_counterfactual.py
  python make_figures.py
  python make_additional_figures.py
第一个命令按原模型从初态计算四问；第二个命令生成第四问比较图所需的同物性固定半径
对照。计算可能耗时较长。--skip-convergence仅跳过主入口附带的时间步长与模型对照检查，
不改变主模型终算设置。运行后自动生成results/和figures/目录；ZIP本身没有目录。
图中的温湿场来自重新计算生成的NPZ，不能仅靠四个结果Excel替代全部内部场。
根目录result1.xlsx至result4.xlsx是原样保留的正式结果，本套命令不会改写这些文件。
这里只提供主模型和主结果图；COMSOL、独立验证图、论文排版与结果模板导出程序
不属于这个平铺包。canonical求解函数未改，只对输入读取和交付目录作适配。

Counterfactual Q4 run using Appendix-4 properties but a fixed radius."""

from __future__ import annotations

import json
import sys

from solve_drying import (
    RESULTS_DIR,
    load_environment,
    property_q4,
    save_npz,
    simulate_fixed,
)


def main() -> None:
    environment = load_environment()
    simulation = simulate_fixed(
        environment,
        property_q4,
        end_time_s=None,
        dt_s=1.0,
        output_interval_s=60.0,
        stop_at_threshold=True,
    )
    save_npz(RESULTS_DIR / "q4" / "fixed_radius_counterfactual.npz", simulation)
    summary_path = RESULTS_DIR / "q4" / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    fixed_time_h = float(simulation["threshold_time_s"]) / 3600.0
    moving_time_h = float(summary["drying_time_h"])
    summary["fixed_radius_counterfactual"] = {
        "same_appendix4_properties_time_h": fixed_time_h,
        "moving_radius_time_h": moving_time_h,
        "time_reduction_h": fixed_time_h - moving_time_h,
        "relative_reduction": (fixed_time_h - moving_time_h) / fixed_time_h,
    }
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary["fixed_radius_counterfactual"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
