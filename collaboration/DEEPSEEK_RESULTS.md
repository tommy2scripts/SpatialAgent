# Phase 2B Results — DeepSeek v4 Pro Execution Report (QA Repaired)

**Date:** 2026-05-09 21:13:27
**Worker:** DeepSeek v4 Pro via OpenCode Go
**Task:** Phase 2B VISTA/VSIR macrophage-state and spatial-niche analysis
**QA Status:** REPAIRED — denominator bug fixed (see QA section)

---

## Files Generated (15 deliverables)

All in `./experiments/phase2B_vista_macrophage_state/`

### CSVs (8)
| File | Rows | Content |
|------|------|--------|
| vista_high_threshold_sensitivity.csv | 4 | — |
| macrophage_marker_coverage_table.csv | 9 | — |
| vista_high_low_macrophage_marker_effects.csv | 73 | — |
| vista_high_low_macrophage_module_scores.csv | 7 | — |
| vista_macrophage_neighbor_composition_by_radius.csv | 192 | — |
| vista_macrophage_nearest_distance_summary.csv | 192 | — |
| vista_macrophage_domain_tls_caf_enrichment.csv | 44 | — |
| vista_macrophage_sensitivity_checks.csv | 8 | — |

### Figures (6)
| _phase2B_contact_sheet.png | 438 KB |
| vista_axis_summary_figure_candidate.png | 323 KB |
| vista_high_low_macrophage_marker_heatmap.png | 87 KB |
| vista_macrophage_spatial_neighbor_panel.png | 142 KB |
| vista_macrophage_tls_caf_domain_enrichment.png | 163 KB |
| vista_raw_clr_macrophages_by_sample.png | 213 KB |
| vsir_rna_macrophages_by_sample.png | 67 KB |

---

## Key Findings (QA-Verified)

### Macrophage Population
- 170,352 QC'd macrophages across 4 samples
  - PN_Breast: 2,926 (1,712 VISTA-high, 59%)
  - PN_Lung: 26,945 (9,914 VISTA-high, 37%)
  - PT_Breast: 46,213 (7,832 VISTA-high, 17%)
  - PT_Lung: 94,268 (14,613 VISTA-high, 16%)

### VISTA Threshold
- Global top 20% CLR: threshold = 2.460 CLR
- 34,071 VISTA-high macrophages (20.0% of total)
- GMM supports 2 components (BIC prefers over 1-component)

### Macrophage State
- Immunosuppression module: d=0.41 (VISTA-high > low) — strongest discriminator
- M2/anti-inflammatory: d=0.08 (weak)
- Phagocytosis: d=0.07 (weak)

### Spatial Niche (at 50µm)
- Enriched near VISTA-high: Endothelial (+0.036), Normal Epithelium (+0.010), T Cell (+0.004)
- Depleted near VISTA-high: Tumour Epithelium (−0.041)

### TLS Association
- VISTA-high macrophages 3.4× enriched in Mature_TLS (PN_Lung)

---

## Final Verdict

### MAIN FIGURE READY

VISTA-high macrophages form a distinct population characterized by:
1. Enrichment in normal tissue (PN > PT in both matched cases)
2. Immunosuppressive transcriptional profile
3. Spatial association with normal epithelium and endothelial cells
4. Depletion from tumor epithelial neighborhoods
5. Enrichment in mature TLS structures

---

## QA Section

### Bug: Denominator Error (QA-Repaired 2026-05-09 21:13:27)

- **Original report (2026-05-09 18:56):** Claimed VISTA-high = 14,613, VISTA-low = 79,655
- **Bug:** Report text used PT_Lung's per-sample count (14,613) instead of global count (34,071)
- **Root cause:** Variable shadowing in sensitivity loop — per-sample iteration overwrote global n_high
- **Actual values:** VISTA-high = 34,071, VISTA-low = 136,281 (sum = 170,352)
- **CSV data:** ALL CORRECT (verified against recomputation)
- **Figures:** ALL CORRECT (generated from correct is_vista_high)
- **Conclusion unchanged:** MAIN FIGURE READY
- **Classification method:** Global (across all 4 samples), top 20% CLR

---

## Exact Questions for GPT 5.5 Review (Unchanged)

1. Is the Immunosuppression module (d=0.41) strong enough to claim 'immunosuppressive transcriptional program'?
2. Is the Endothelial spatial enrichment a genuine perivascular pattern or density artifact?
3. Should Mature_TLS enrichment (3.4×) be a main-text finding despite small counts?
4. Does the summary figure need reorganization before manuscript insertion?
5. Is global top-20% CLR threshold defensible for publication?
