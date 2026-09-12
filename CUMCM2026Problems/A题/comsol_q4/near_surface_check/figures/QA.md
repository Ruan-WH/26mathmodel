# Refined COMSOL figure and paper integration QA

- Contract: retain the existing three-panel comparison. Panel (a) shows three specified radial profiles, (b) uses all 6006 common sampling pairs from six times, (c) shows the existing radius history. No new simulation or experimental-accuracy claim.
- Source: graded320_tight/q4_comsol_profiles.csv; compare with results/q4/fields.npz, including the native-grid threshold profile.
- Reproduce: `python comsol_q4/plot_q4_physical.py --refined` from the project root. PDF and 300 dpi PNG are written here; the paper uses figures/q4_comsol_refined_validation.pdf.
- Numerical QA: maximum absolute moisture difference 4.544533736350331e-5 kg/kg, 6006 parity pairs, 161 reference nodes. The figure statistic equals the independent refinement summary.
- Marker display: panel (a) retains about 11 regularly spaced markers per curve plus near-surface markers for readability; full curves and all panel (b) comparisons are retained.
- Visual QA: reused Times New Roman/SimSun typography and existing color mapping, below-axis Chinese panel labels, unobstructed legend, scientific-notation error annotation. PNG inspected; no clipping or overlaps found.
- Paper integration: six-case table generated from summary.json. Abstract and Q4 discussion use the refined result. Legacy COMSOL result files remain preserved and are not the figure source for the new manuscript figure.
- Interpretation: supports numerical consistency under the stated equations and boundary assumptions, not experimental validation of the drying model. The FVM threshold time is retained.
- Chinese-label revision: all six axis descriptions in figure 13 are now Chinese; COMSOL, variable names and measurement units remain. Rendered PNG and final manuscript page checked for missing glyphs and overlap. The paper defines the initial auto-size-3 mesh (492 domain elements) and distinguishes total domain elements from the refined meshes' radial counts.
