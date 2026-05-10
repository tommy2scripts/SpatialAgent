# GPT 5.5 — Phase 2B Scientific/Statistical Review

**Reviewer:** GPT 5.5 (acting as scientific arbiter)
**Date:** 2026-05-09
**Subject:** Phase 2B VISTA/VSIR macrophage-state and spatial-niche analysis (QA-repaired)
**Design constraint:** 2-patient / 4-sample matched-case Xenium atlas. Tissue × patient confounded. No biological replicates. No population claims.

---

## 1. Denominator Repair — PASS (with qualifications)

The QA repair is **logically sound and verified.** The corrected numbers reconcile cleanly:

| Metric | Pre-repair | Post-repair |
|---|---|---|
| VISTA-high | 14,613 | **34,071** |
| VISTA-low | 79,655 | **136,281** |
| Sum | 94,268 (PT_Lung only) | **170,352** (all macrophages) |

The root cause (variable shadowing in the sensitivity loop) is a plausible scripting error. The QA diagnostic independently reproduced all values. The verification that "CSVs and figures are unaffected" is confirmed by the fact that `is_vista_high` was recomputed from the full 170,352-cell `vista_clr_macro` array before any variable overwriting, and the sensitivity CSV independently records correct counts.

**Minor concern:** The QA section says "the denominator bug did NOT cascade into downstream analyses because is_vista_high was correctly computed from all 170,352 macrophages before any variable shadowing." This is partially inaccurate — `is_vista_high` was recomputed AFTER the sensitivity loop, and the report-generation code that ran AFTER that recomputation still grabbed wrong numbers. The bug was in the report-writing code path, not in `is_vista_high` itself. But the CSVs and figures do indeed use the correct `is_vista_high`. The explanation should be clarified.

---

## 2. VISTA-High Definition — REVISE

### 2.1 Global top 20% CLR is acceptable as primary, but NOT as only definition

**Strengths:**
- Raw-CLR concordance ρ = 0.967 in macrophages — CLR faithfully represents the raw signal
- Top 10%, top 20%, and GMM threshold sensitivity show consistent direction
- All 4 samples independently show VISTA-high > VISTA-low in raw protein

**Critical weakness — sample/condition confounding:**

The global threshold creates extreme sample imbalance:

| Sample | % VISTA-high | Macrophage count |
|---|---|---|
| PN_Breast | **59%** | 2,926 |
| PN_Lung | **37%** | 26,945 |
| PT_Breast | 17% | 46,213 |
| PT_Lung | 16% | 94,268 |

This means "VISTA-high" is heavily confounded with "normal tissue" and with "low macrophage count." Any comparison of VISTA-high vs VISTA-low macrophages is partially a comparison of normal-tissue macrophages vs tumor macrophages. **This is the most serious threat to the biological interpretation of Phase 2B.**

**Recommendation:** The analysis MUST be repeated with per-sample VISTA-high definitions (top 20% within each sample). If the Immunosuppression module effect and spatial niche patterns survive per-sample thresholding, the findings are robust. If they collapse (i.e., the effect was driven by normal-vs-tumor composition, not VISTA biology), the verdict must be downgraded.

### 2.2 GMM threshold is effectively broken

The sensitivity CSV reports GMM threshold = −3.809 with n_high = 170,351 and n_low = 1. This means GMM separates a single outlier cell from the rest of the population. This is **not a useful bimodal split** and should not be reported as supporting evidence for a "VISTA-high population." The GMM finding should be reported honestly: "GMM identified a single outlier component; bimodality in the biological range was not detected by this method."

### 2.3 CLR is acceptable as primary given ρ = 0.967

The concordance is strong enough to justify CLR-based thresholding.

---

## 3. Sample/Condition Confounding — CRITICAL ISSUE

### 3.1 The omission of Tissue_residency module (d = −0.63)

This is the **most important finding the report buried.** The module scores CSV shows:

| Module | Cohen's d | Direction |
|---|---|---|
| **Tissue_residency** | **−0.63** | VISTA-high < low |
| Immunosuppression | +0.41 | VISTA-high > low |
| M2/anti-inflammatory | +0.08 | negligible |
| Phagocytosis | +0.07 | negligible |
| M1/inflammatory | −0.03 | nothing |
| Chemokine_signaling | −0.05 | nothing |
| Proliferation | −0.03 | nothing |

The Tissue_residency module (SPARC, TREM2, APOE) shows the **strongest effect in the entire module analysis** and the report **completely omitted it.** Worse, the report's narrative claims VISTA-high macrophages are "tissue-resident macrophages" — a claim directly contradicted by the strongest module effect in the data.

**VISTA-high macrophages have LOWER tissue residency scores (d=−0.63).** This is a medium-to-large effect by the project's own thresholds (|d| ≥ 0.5 = meaningful). If VISTA-high macrophages are NOT tissue-resident (they downregulate SPARC, TREM2, APOE), what are they? This finding changes the biological interpretation and MUST be the headline module result, not Immunosuppression.

### 3.2 Are marker/module/spatial findings driven by sample composition?

Given the 59% vs 16% sample imbalance, the pooled analysis conflates "VISTA-high" with "normal tissue macrophage." The Tissue_residency module finding (d=−0.63, VISTA-high < low) is consistent with the alternative interpretation: VISTA-high macrophages are predominantly tumor macrophages (which have lower tissue residency scores), and the VISTA protein difference is confounded with tissue type.

**Critical test needed:** Per-sample VISTA-high definitions. If Tissue_residency d remains negative within individual samples, it's a genuine VISTA-associated pattern. If it disappears, the pooled result was compositional.

### 3.3 Heatmap markers are mostly pan-immune, not macrophage-state-specific

The heatmap's top distinguishing proteins are: CD45, CD31, CD45RA, CD163-1, CD11c, CD68-1, CD14, HLA-DR, CD4-1. These are largely pan-immune or pan-myeloid markers (CD45, CD45RA, CD14, HLA-DR), endothelial/stromal (CD31), and dendritic cell markers (CD11c). Their elevation in VISTA-high macrophages could reflect generally higher protein detection, higher cell size, or higher overall protein content in normal-tissue macrophages — NOT a specific macrophage state.

This weakens the claim that VISTA-high macrophages have a "distinct protein-level profile." The profile may simply be "normal tissue macrophages have more protein."

---

## 4. Module Score Validity — REVISE

### 4.1 Immunosuppression module: d = 0.41

This is a **small-to-medium effect** (|d| < 0.5 = "small" by project thresholds). The module includes VSIR itself (the VISTA gene), which creates circularity: VISTA-high macrophages (selected by VISTA CLR protein) will naturally have higher VSIR RNA. This inflates the module score.

**Recommendation:** Recompute the Immunosuppression module WITHOUT VSIR. If the effect survives (d ≥ 0.2), it's a genuine signal. If it collapses, the module score was driven by circularity.

### 4.2 Tissue_residency module: d = −0.63

This should be the **headline module finding.** It is the largest effect, it is not circular (the module genes SPARC, TREM2, APOE are independent of VISTA/VSIR), and it provides a coherent biological narrative: VISTA-high macrophages may be recruited/activated macrophages that have not yet adopted a tissue-resident program, or they may be an intermediate state.

### 4.3 The report should call the module "immunoregulatory" or "checkpoint-expressing"

"Immunosuppression" is too strong and causal for a descriptive module score in a matched-case atlas. The module genes (IDO1, PDCD1LG2, CD274, VSIR, HAVCR2, LILRB2, LILRB4) are better described as "checkpoint/immunoregulatory" — they include both co-stimulatory and co-inhibitory molecules. The word "immunoregulatory" is more precise and less causal.

### 4.4 Per-sample module scores are absent

This is a critical gap. All module scores are computed pooled across all 4 samples. Without per-sample verification, we cannot distinguish VISTA biology from sample composition effects.

---

## 5. Spatial Niche Robustness — REVISE (incomplete verification)

### 5.1 Consistency across radii

The neighbor composition CSV provides data at 25, 50, and 100µm. The report only discusses 50µm. The 25µm and 100µm radii should be checked for consistency of the key patterns (endothelial enrichment, tumor epithelial depletion).

### 5.2 Within-sample consistency not verified

The spatial neighbor panel (Figure 4) shows per-sample patterns, but the report's "enriched near VISTA-high" summary is the mean across all 4 samples. This averages over the extreme sample imbalance (PT_Lung = 94K macrophages, PN_Breast = 3K). The PT_Lung VISTA-low macrophages dominate the "low" group, meaning the "VISTA-low neighbor composition" is essentially PT_Lung's tumor microenvironment.

**This is the same confounding problem in spatial form.** VISTA-high macrophages are enriched near normal epithelium because normal-tissue macrophages ARE near normal epithelium. The spatial niche signal may be entirely compositional.

### 5.3 Endothelial enrichment — interesting but unvalidated

If VISTA-high macrophages are enriched near endothelial cells in a perivascular pattern, this could indicate a genuine biological niche (perivascular macrophages). But the current analysis cannot distinguish "VISTA-high macrophages are near endothelial cells" from "normal tissue has more endothelial cells and normal tissue has more VISTA-high macrophages." Per-sample or within-condition spatial analysis is needed.

### 5.4 TLS enrichment is largely a PN_Lung vignette

The report highlights 3.4× Mature_TLS enrichment in PN_Lung. But:
- PN_Breast Mature_TLS has inf ratio (division by zero in low group)
- PT_Breast Mature_TLS has 1.2× (negligible)
- PT_Lung Mature_TLS is not in the top enrichments

The TLS association is specific to one sample (PN_Lung). This should be reported as a **sample-specific vignette, not a general finding.** The report currently treats it as a general characteristic.

### 5.5 CAF enrichment is entirely absent

The CAF enrichment figure shows all "NA" — no CAF enrichment data was computed. This should be stated explicitly rather than shown as an empty panel.

---

## 6. Figure Review

| Figure | Verdict | Rationale |
|---|---|---|
| `vista_raw_clr_macrophages_by_sample.png` | **SUPPLEMENTAL** | Useful for showing raw-CLR concordance. The CLR histograms clearly show the top-20% threshold. But this is a methods/QC figure, not a main biological result. |
| `vsir_rna_macrophages_by_sample.png` | **SUPPLEMENTAL** | Shows VSIR RNA detection rates. Useful validation but not a main result. |
| `vista_high_low_macrophage_marker_heatmap.png` | **REVISE** | The heatmap shows pan-immune markers (CD45, CD45RA, CD14) as top hits, which weakens the "distinct state" claim. Consider: (a) add per-sample heatmaps, (b) normalize by total protein content, or (c) replace with a volcano-style plot showing which markers survive per-sample analysis. |
| `vista_macrophage_spatial_neighbor_panel.png` | **REVISE** | Shows the compositional confounding problem clearly. Needs per-sample VISTA-high definitions to be interpretable. Currently, "VISTA-high" = "normal tissue," so the normal-epithelium enrichment is tautological. |
| `vista_macrophage_tls_caf_domain_enrichment.png` | **SUPPLEMENTAL** | TLS enrichment is sample-specific. CAF enrichment is empty. The Squidpy domain panel is dominated by one PN_Breast domain. Not main-figure quality. |
| `vista_axis_summary_figure_candidate.png` | **REVISE** | Six panels attempt to tell the full story but omit the Tissue_residency module (the strongest effect). The TLS panel at bottom shows a confusing heatmap with only 4 data points. The missing caveat text at the bottom is present but too small. |

---

## 7. Claim Control

### Proposed wording: REVISE

The DeepSeek-proposed claim:

> "VISTA-high macrophages mark a reproducible within-dataset macrophage state/niche associated with normal-tissue, endothelial/T-cell, and TLS-like microenvironments, with depletion from tumor-epithelial neighborhoods."

**Assessment: TOO STRONG.** The word "reproducible" is explicitly banned by the matched-case language contract (requires external replication). "Macrophage state/niche" implies the VISTA signal is independent of tissue type — but the global threshold makes VISTA-high = normal tissue. The claim must be revised.

### Strongest defensible claim (corrected):

> "In this matched-case atlas, macrophages with VISTA protein in the top 20% of the CLR distribution (VISTA-high) were enriched in normal-tissue samples (59% of PN_Breast, 37% of PN_Lung macrophages) and depleted in tumor samples (17% PT_Breast, 16% PT_Lung). VISTA-high macrophages showed elevated expression of checkpoint/immunoregulatory genes (Immunosuppression module d=0.41) and lower expression of tissue-residency markers (SPARC, TREM2, APOE; d=−0.63). Within individual samples, VISTA-high macrophages were spatially associated with endothelial and normal epithelial neighborhoods and depleted from tumor epithelial neighborhoods. These observations are hypothesis-generating and cannot distinguish VISTA-driven biology from compositional differences between normal and tumor macrophage populations."

### Claims to explicitly reject:
- "VISTA-high macrophages are tissue-resident" — contradicted by Tissue_residency module (d=−0.63)
- "VISTA marks an immunosuppressive macrophage state" — circular with VSIR in the module; use "immunoregulatory"
- "Enriched in mature TLS" — sample-specific (PN_Lung), not general
- "Reproducible macrophage state" — banned language
- "Tumors suppress VISTA" — banned causal language
- Any cross-tissue breast-vs-lung claim

---

## 8. Final Verdict

### REVISE (not FAIL)

Phase 2B has produced useful, well-structured data that answers the core question ("what does VISTA/VSIR mark?") but the **biological interpretation needs substantial revision.** The current narrative ("VISTA-high macrophages are tissue-resident, immunosuppressive, TLS-associated") is partially wrong (Tissue_residency d=−0.63) and partially unvalidated (pooled analysis conflates VISTA with normal tissue).

**The key finding is actually more interesting than the current narrative:** VISTA-high macrophages have lower tissue-residency scores and higher checkpoint/immunoregulatory scores — suggesting they may be a recruited or activated population rather than a resident one.

### Specific Fixes Required Before Phase 3:

1. **[CRITICAL] Recompute all module scores per sample.** Determine whether Tissue_residency (d=−0.63) and Immunosuppression (d=0.41) persist within individual samples.

2. **[CRITICAL] Add per-sample VISTA-high definitions.** Repeat the key analyses (marker effects, module scores, spatial neighbors) with top-20%-within-each-sample thresholds. This is the only way to disentangle VISTA biology from sample composition.

3. **[CRITICAL] Recompose Immunosuppression module without VSIR.** Remove VSIR from the module gene list and recompute. Report both with-VSIR and without-VSIR scores.

4. **[HIGH] Add the Tissue_residency module to the report and summary figure.** It is the strongest module effect and changes the biological interpretation. The report's silence on this finding is a major omission.

5. **[HIGH] Fix the GMM reporting.** State clearly that GMM identified a single-outlier component, not a biologically meaningful bimodal split.

6. **[MEDIUM] Rename "Immunosuppression" module to "Checkpoint/Immunoregulatory."** More precise and less causal.

7. **[MEDIUM] Verify spatial neighbor patterns at 25µm and 100µm radii.** Report consistency across all three radii.

8. **[MEDIUM] Add missing figure caveats.** The summary figure needs the mandatory matched-case caveat text at readable size.

9. **[LOW] Remove or explain the empty CAF enrichment panel.** Either remove it or add a note explaining why CAF enrichment was not computed.

### Phase 3 Readiness:

**CONDITIONAL PROCEED.** Phase 3 (BANKSY domain characterization) can proceed in parallel with Phase 2B revisions, because the BANKSY domains are sample-specific and independent of the VISTA-high classification. However, the Phase 2B main-figure verdict cannot be finalized until per-sample verification is complete.

---

## Summary

| Assessment | Rating |
|---|---|
| Denominator repair | PASS ✓ |
| Data integrity (CSVs) | PASS ✓ |
| Global threshold definition | ACCEPTABLE (primary only) |
| Per-sample verification | **MISSING — CRITICAL** |
| Module score interpretation | **REVISE** |
| Tissue_residency omission | **CRITICAL OVERSIGHT** |
| Spatial niche robustness | **INCOMPLETE** |
| TLS claim generalizability | **OVERSTATED** |
| Figure readiness | 0 main-figure, 3 supplemental, 3 revise |
| Claim language compliance | **TOO STRONG — REVISE** |

**Final action:** REVISE Phase 2B with per-sample definitions and Tissue_residency module inclusion. Phase 3 may proceed in parallel.
