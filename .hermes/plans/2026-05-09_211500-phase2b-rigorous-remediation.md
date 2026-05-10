# Phase 2B Rigorous Remediation Plan

## Goal
Re-evaluate the Phase 2B VISTA/VSIR macrophage state analysis by strictly applying all relevant scientific skills (statistical analysis, scientific visualization, exploratory data analysis) before generating the final data outputs.

## Context & Assumptions
- In the previous review pass, `scientific-brainstorming` and `scientific-critical-thinking` were active, but `scientific-visualization` and `statistical-analysis` were NOT explicitly loaded.
- The Phase 2B DeepSeek report contains severe data leakage (module circularity with VSIR), spatial density artifacts, and small-N noise.
- We must fix these analytical flaws using rigorous statistical frameworks before declaring the phenotype valid or invalid.

## Governing Skills to Activate
Before executing this plan, the following skills MUST be loaded via `skill_view`:
1. `openclaw-imports/statistical-analysis`
2. `openclaw-imports/scientific-visualization`
3. `openclaw-imports/exploratory-data-analysis`

## Step-by-Step Plan

### Phase 1: Rigorous Statistical Remediation (`statistical-analysis`)
1. **Module Circularity Fix:** Re-calculate all macrophage state module scores explicitly excluding `VSIR` (and `LILRB2` if heavily co-expressed). Evaluate effect sizes using formal confidence intervals.
2. **Within-Sample Thresholding:** Calculate top-20% VISTA CLR thresholds *per sample* or *per tissue* rather than globally, to break the confounding between tissue type (Breast vs. Lung) and VISTA status.
3. **Spatial Null Modeling:** Instead of raw neighbor fractions, calculate the expected endothelial cell density in PN vs PT tissues. Test if the spatial enrichment survives when controlling for baseline tissue vascularity.
4. **Small-N Filtering:** Apply a strict statistical power filter. Discard any TLS or domain enrichment ratios where the base N < 20 cells.

### Phase 2: Scientific Visualization (`scientific-visualization`)
1. **Scrap Original Figure:** Delete `vista_axis_summary_figure_candidate.png`.
2. **Design New Figure Layout:**
   - Panel A: VISTA CLR distributions (showing within-sample threshold lines).
   - Panel B: Corrected Module Scores (excluding VSIR).
   - Panel C: Spatial Enrichment (Observed vs. Expected null model).
3. **Generate Publication-Ready Plots:** Follow the guidelines in the `scientific-visualization` skill to ensure colorblind accessibility, proper scaling, and non-deceptive axes.

### Phase 3: Final Synthesis
1. Synthesize the corrected statistical and visual data.
2. Output a finalized Phase 2B Remediation Report based on the clean statistics.
3. Update `DEEPSEEK_RESULTS.md` with the new, statistically sound findings.

## Risks & Open Questions
- Does the "immunosuppressive" macrophage phenotype disappear entirely when within-sample thresholding is applied? If so, the finding is purely a tissue-specific baseline artifact and should be dropped from the main paper.
- Are there enough "VISTA-high" cells left per sample to run robust spatial stats once within-sample thresholding is applied?