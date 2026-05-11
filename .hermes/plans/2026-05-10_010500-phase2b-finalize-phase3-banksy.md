# Phase 2B Finalization & Phase 3 BANKSY — Implementation Plan

**Date:** 2026-05-10 01:05  
**Status:** Planning (no execution)  
**Peer Review Verdict:** PASS — MAIN FIGURE READY  
**Review Doc:** `experiments/phase2B_v2_vista_macrophage_remediation/GPT_3_1_PRO_REVIEW_V2.md`

---

## 1. Goal

Finalize the Phase 2B v2 main figure for publication and execute Phase 3 — BANKSY spatial domain analysis mirroring the remediated squidpy-based Phase 2B v2 workflow, then integrate all findings into a coherent manuscript skeleton.

## 2. Current State

### What Exists
| Artifact | Path | Status |
|----------|------|--------|
| Phase 2B v2 analysis script | `experiments/phase2B_v2_vista_macrophage_remediation.py` | Complete, executed |
| 6 figures | `experiments/phase2B_v2_vista_macrophage_remediation/figures/` | Generated |
| 9 CSVs | `experiments/phase2B_v2_vista_macrophage_remediation/*.csv` | Generated |
| Report | `experiments/phase2B_v2_vista_macrophage_remediation/phase2B_v2_vista_macrophage_remediation_report.md` | Generated |
| Peer review | `experiments/phase2B_v2_vista_macrophage_remediation/GPT_3_1_PRO_REVIEW_V2.md` | Complete, PASS |
| Anndata | `~/Downloads/xenium_atlas_v2/data/adata_v4.h5ad` | 1.28M cells, 380 genes, BANKSY domains pre-computed |

### BANKSY Domain Inventory
- `spatial_domain_banksy`: **34 domains** (coarse, ~comparable to squidpy's 24)
- `banksy_domain`: **98 domains** (fine, includes "unassigned")
- `spatial_domain_squidpy`: **24 domains** (used in Phase 2B v2)

### Peer Review Action Items
1. **Fix**: Standardize permutation count language — report says 25 but caveats say 100. Use actual count (25) consistently.
2. **Polish**: Summary figure candidate needs publication-quality panel labels (a–g), consistent typography, proper legend placement.
3. **Proceed**: Phase 3 (BANKSY domains) cleared.

## 3. Proposed Approach

### Part A — Phase 2B v2 Main Figure Finalization (est. 30 min)
Simple text fix to caveats section + figure polish script.

### Part B — Phase 3: BANKSY Domain Analysis (est. 2 hrs runtime)
Mirror the Phase 2B v2 workflow but use `spatial_domain_banksy` (34 domains) as the primary annotation. The v2 remediation pipeline (within-sample thresholds, VSIR-free modules, permutation null models, min-count filtering) is directly reusable. Key additions:

1. **BANKSY domain characterization** — what cell types compose each BANKSY domain? (Not done for squidpy.)
2. **Cross-domain comparison** — do VISTA-high macrophages enrich in the same anatomical regions under BANKSY vs squidpy definitions?
3. **BANKSY-specific findings** — are there spatial enrichments visible only in BANKSY but not squidpy?

### Part C — Manuscript Skeleton (est. 45 min)
Consolidate Phase 2A (checkpoint validation) + Phase 2B v2 (VISTA macrophage state) + Phase 3 (BANKSY domains) into a structured markdown manuscript skeleton with one-liner findings and figure panel assignments.

## 4. Step-by-Step Plan

### 4.1 Part A: Phase 2B v2 Finalization

**Step A1**: Fix permutation count inconsistency in report (lines 110 and 111 of report — change "100 permutations per test" to "25 permutations per test") and in figure subtitle (line 783 of script — change "100 permutations" to "25 permutations").

**Step A2**: Create `experiments/phase2B_v2_finalize_figure.py` — a lightweight script that:
- Reads the v2 CSVs
- Regenerates `vista_phase2b_v2_summary_candidate.png` with:
  - Standardized panel labels (a–g) in bold uppercase
  - Consistent font sizes (8pt axis labels, 9pt titles, 11pt panel labels)
  - Fixed caveat box text (permutation count correction)
  - Better color map for heatmap (Panel E)
  - 300 DPI output
- Saves as `figures/vista_phase2b_v2_main_figure.png`

**Step A3**: Write a short `MAIN_FIGURE_LEGEND.md` with one-paragraph figure legend suitable for manuscript submission.

**Deliverables**: 
- `figures/vista_phase2b_v2_main_figure.png` (300 DPI)
- `MAIN_FIGURE_LEGEND.md`
- Updated report (permutation count fix)

### 4.2 Part B: Phase 3 — BANKSY Domain Analysis

**Step B1**: Create `experiments/phase3_banksy_domains.py` — a new analysis script that:

1. **Loads** the same anndata, isolates macrophages, computes within-sample VISTA-high labels (identical to Phase 2B v2)
2. **Characterizes BANKSY domains**: Per-sample, per-domain cell-type composition heatmaps (what cell types live in each BANKSY domain?)
3. **Runs neighborhood enrichment** using `spatial_domain_banksy` as the annotation (mirrors Phase 2B v2 TLS/domain section but for BANKSY)
4. **Cross-compares** squidpy vs BANKSY enrichments: side-by-side heatmap showing enrichment ratios for both methods
5. **Runs spatial neighbor analysis** (kNN permutation null) as in Phase 2B v2 but stratified by BANKSY domain
6. **Generates figures**:
   - `banksy_domain_composition.png` — per-sample heatmaps of cell-type composition per BANKSY domain
   - `banksy_vista_enrichment.png` — VISTA-high enrichment per BANKSY domain (filtered, min-count ≥20)
   - `banksy_vs_squidpy_comparison.png` — side-by-side enrichment comparison
   - `phase3_banksy_summary.png` — 4-panel summary figure

**Step B2**: Write `phase3_banksy_domains_report.md` with:
- BANKSY domain characterization findings
- Cross-method comparison (BANKSY vs squidpy)
- Claims that survive / are rejected
- Caveats

**Key parameters** (matching Phase 2B v2):
- Within-sample top 20% CLR threshold
- VSIR-free modules
- 25 permutations for null models
- Min-count ≥20 cells for domain enrichment

**Files to create**:
- `experiments/phase3_banksy_domains.py`
- `experiments/phase3_banksy_domains/` (output directory)

### 4.3 Part C: Manuscript Skeleton

**Step C1**: Create `manuscript/MANUSCRIPT_SKELETON.md` — a structured document with:

1. **Title** (draft)
2. **One-liner findings** from each phase:
   - Phase 2A: VISTA/VSIR expression is higher in primary normal vs primary tumor across matched breast/lung pairs
   - Phase 2B v2: VISTA-high macrophages are NOT tissue-resident; they show modest checkpoint/immunoregulatory gene expression
   - Phase 3: [to be filled after execution]
3. **Figure panel assignments** — which panels go in which main/supplemental figure
4. **Abstract bullet points** — 5-6 bullets suitable for conference abstract
5. **Methods summary** — 200-word methods paragraph
6. **Caveat block** — matched-case, no biological replicates, tissue×patient confounded, pipeline-derived annotations

**Step C2**: Map existing figures to manuscript panels:
- Main Figure 1: VISTA/VSIR expression landscape (Phase 2A) + thresholding audit (Phase 2B v2)
- Main Figure 2: Macrophage module scores + Tissue_residency module (Phase 2B v2)
- Main Figure 3: Spatial niche + BANKSY domain comparison (Phase 2B v2 + Phase 3)
- Supplemental: Permutation null models, TLS/domain enrichment detail, BANKSY domain characterization

**Deliverable**: `manuscript/MANUSCRIPT_SKELETON.md`

## 5. Files Likely to Change / Create

| File | Action | Phase |
|------|--------|-------|
| `experiments/phase2B_v2_vista_macrophage_remediation.py` | Patch (permutation count in figure text) | A |
| `experiments/phase2B_v2_vista_macrophage_remediation/phase2B_v2_vista_macrophage_remediation_report.md` | Patch (caveat text) | A |
| `experiments/phase2B_v2_finalize_figure.py` | **CREATE** | A |
| `experiments/phase2B_v2_vista_macrophage_remediation/figures/vista_phase2b_v2_main_figure.png` | **CREATE** (output) | A |
| `experiments/phase2B_v2_vista_macrophage_remediation/MAIN_FIGURE_LEGEND.md` | **CREATE** | A |
| `experiments/phase3_banksy_domains.py` | **CREATE** | B |
| `experiments/phase3_banksy_domains/` | **CREATE** (output dir) | B |
| `experiments/phase3_banksy_domains/phase3_banksy_domains_report.md` | **CREATE** (output) | B |
| `manuscript/MANUSCRIPT_SKELETON.md` | **CREATE** | C |

## 6. Tests / Validation

### Part A
- [ ] Main figure regenerates without errors
- [ ] Panel labels (a–g) are legible
- [ ] Permutation count corrected to 25 in both figure footer and report
- [ ] Figure legend accurately describes all 7 panels

### Part B
- [ ] BANKSY script loads adata and isolates macrophages correctly
- [ ] Within-sample VISTA-high labels match Phase 2B v2 counts (20% per sample)
- [ ] BANKSY domain enrichment produces ≥10 rows passing min-count filter
- [ ] Cross-comparison produces meaningful differences (BANKSY ≠ squidpy for some domains)
- [ ] No pandas `nlargest(key=)` errors (use pre-computed abs column)
- [ ] Figures render without matplotlib errors

### Part C
- [ ] All 3 phases represented in manuscript skeleton
- [ ] Claims proportional to evidence (conservative stats language per Tommy's requirements)
- [ ] Caveats prominently featured

## 7. Risks, Tradeoffs, and Open Questions

### Risks
- **BANKSY domain granularity**: 34 domains across 4 samples may produce many domains with <20 cells, making filter too aggressive. Fallback: use `banksy_domain` (98 domains) grouped by broad anatomical region.
- **Runtime**: Phase 2B v2 took ~3 min for spatial analysis. Phase 3 adds domain characterization heatmaps (cheap) + cross-comparison (cheap). Expected total: 5-8 min.
- **BANKSY vs squidpy redundancy**: If BANKSY domains mirror squidpy domains, Phase 3 adds limited value. The cross-comparison panel will make this immediately visible.

### Tradeoffs
- **Coarse vs fine BANKSY**: `spatial_domain_banksy` (34 domains) is safer for enrichment analysis but `banksy_domain` (98 domains) may capture finer niches. Use coarse as primary, fine as exploratory supplemental.
- **Figure count**: Already 6 figures from Phase 2B v2 + 4 from Phase 3 = 10 figures. Some will be supplemental. The manuscript skeleton (Part C) will triage.

### Open Questions
1. Do BANKSY domains meaningfully differ from squidpy domains for macrophage niche analysis? (Empirical question — answered by Phase 3)
2. Should the BANKSY domain characterization (cell-type composition) become a main figure panel or supplemental?
3. Is there a "BANKSY-signature domain" where VISTA-high macrophages enrich that squidpy misses entirely?

## 8. Execution Order

```
Part A (1 hr) ──→ Part B (2 hrs) ──→ Part C (45 min)
                                      ↓
                              MANUSCRIPT_SKELETON.md
```

Parts A and B can be parallelized (different scripts, no data dependency). Part C requires both complete.

---

*Plan written 2026-05-10 01:05. Review: GPT_3_1_PRO_REVIEW_V2.md. Next: execute upon user approval.*
