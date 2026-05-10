# SpatialAgent Full Pipeline — REVISED (Builds on Existing Analysis)

**Date:** 2026-05-09 16:00 PDT
**Status:** Plan (no execution)
**Supersedes:** `2026-05-09_154500-xenium-full-pipeline.md`
**Goal:** Publication-ready analysis that extends existing work — does NOT redo what's already been done.

---

## 0. What's Already Done (DO NOT REPEAT)

You've completed a substantial analysis. Here's what's established, with exact parameters preserved:

### 0.1 Data Nature

**Multi-modal Xenium**: RNA (380 genes) + Protein (unspecified number of antibody markers). This is NOT RNA-only data.

Key proteins detected: CD31, CD68, CD3E, PanCK, E-Cadherin, Vimentin, CD20, CD138, PD-1, PD-L1, VISTA, LAG-3, MS4A1 (RNA).

### 0.2 QC Pipeline (COMPLETED)

| Step | Method | Parameters |
|---|---|---|
| Filtering | MAD-based + fixed floors | RNA ≥ 10 counts, negative probe rate < 0.2 |
| Norm: RNA | log1p → TruncatedSVD | 20 PCs per sample |
| Norm: Protein | CLR → TruncatedSVD | 15 PCs per sample |
| Integration | Joint 35D embedding | Protein weight ×1.5, Harmony on `slide_id` |

### 0.3 Clustering & Annotation (COMPLETED)

| Step | Method | Details |
|---|---|---|
| Subsample | Stratified 100k cells | For Leiden clustering only |
| Clustering | Leiden (res=0.4) | 17 clusters |
| PT_Lung, PT_Breast | KNN projection | From subsample labels |
| PT_Breast rescue | Protein CLR thresholds | CD31>1.0 & CD68<0.5 → Endothelial; CD68>2.0 & CD3E<0.5 → Macrophage |
| PN_Breast | Independent protein CLR | Hierarchical: CD68>0.5→Macrophage; CD3E>0.5→T Cell; CD138>2.0&PanCK<1.0→Plasma; CD31>1.0→Endothelial; PanCK>1.0 or E-Cad>0.5→Epithelial; else CAF/Stromal |
| B Cell definition | Dual criterion | CD20 CLR > 1.0 AND MS4A1 RNA > 0 |

**Known limitation**: KNN projection from PT-dominated subsample fails for PN_Breast (validated: T Cell cluster was 93.9% PanCK+ under KNN).

### 0.4 Neighborhood Enrichment (COMPLETED)

| Parameter | Value |
|---|---|
| Method | Permutation Z-scores |
| Permutations | 100 |
| Subsample | 50k cells per sample (spatially-stratified) |
| Radius | 50 µm |
| Z-score formula | (observed − mean_permuted) / std_permuted |
| Colormap cap | ±50 |

**Key findings already reported (Section 3.2):**

| Interaction | PT_Lung | PT_Breast | PN_Breast |
|---|---|---|---|
| T Cell — Tumour Epi | −79.3 | −51.1 | +24.6 |
| T Cell self | +225.5 | +75.7 | +59.4 |
| Plasma Cell — T Cell | +37.3 | −1.0 | +17.6 |
| Macrophage self | +12.2 | +28.4 | +14.2 |

### 0.5 Checkpoint Protein Analysis (COMPLETED)

| Method | Details |
|---|---|
| Test | Mann-Whitney U |
| Correction | Benjamini-Hochberg FDR |
| Effect size | Cohen's d |
| Scope | PT_Breast vs PN_Breast only |
| Stratification | T Cell and Macrophage separately |

**Key finding**: All checkpoint proteins are LOWER in PT_Breast than PN_Breast. VISTA in macrophages: d = −0.84 (largest effect). Counterintuitive — normal macrophages have higher homeostatic VISTA.

**TODO: PT_Lung vs PN_Lung comparison NOT done.** Only Breast was analyzed. Lung checkpoint analysis is a new deliverable.

### 0.6 TLS Analysis (COMPLETED)

| Sample | B cells | % | TLS score | Median T→B dist |
|---|---|---|---|---|
| PT_Lung | 31,731 | 4.98% | 83.5% | 11.5 µm |
| PT_Breast | 872 | 0.25% | 31.3% | 253.9 µm |
| PN_Breast | 6 | 0.01% | 0.4% | 1,686 µm |

### 0.7 RNA–Protein Concordance (COMPLETED)

Spearman ρ on 50k random subsample (all samples pooled). Results not shown — need to retrieve from the file.

### 0.8 Cell Type Composition (COMPLETED)

| Cell Type | PT_Lung | PT_Breast | PN_Breast |
|---|---|---|---|
| Epithelial† | 41.2% | 48.7% | 55.8% |
| CAF / Stromal | 20.0% | 21.6% | 13.2% |
| T Cell | 19.4% | 6.6% | 4.9% |
| Macrophage | 10.0% | 15.6% | 7.4% |
| Endothelial | 6.0% | 7.5% | 17.7% |
| Plasma Cell | 3.5% | 0.1% | 1.0% |

**Note**: PN_Lung is missing from the table. Was it analyzed? If so, add it. If not, it's a gap.

---

## 1. What's Missing for Publication (The Actual Plan)

### Gap Analysis

| What's Done | What's Missing |
|---|---|
| QC + normalization | ✅ Nothing — re-use existing |
| Cell type annotation | ✅ Nothing — re-use existing |
| Composition table | ⚠️ PN_Lung missing; no statistical testing |
| Neighborhood enrichment | ✅ RNA-only | ⚠️ No protein-based enrichment; no domain-level analysis |
| Checkpoint proteins | ⚠️ Only PT_Breast vs PN_Breast | ❌ PT_Lung vs PN_Lung comparison |
| TLS scoring | ✅ Done | ⚠️ No spatial gradient analysis; no maturity grading |
| BANKSY domains | ❓ Pre-computed but no results shown | ❌ Domain characterization, λ stability |
| RNA DE (Tumor vs Normal) | ❌ NOT DONE | ❌ Full pipeline needed |
| Cell-cell communication | ❌ NOT DONE | ❌ COMMOT + CellPhoneDB needed |
| CAF spatial analysis | ❌ NOT DONE | ❌ Subtype localization, tumor proximity |
| Pathway enrichment | ❌ NOT DONE | ❌ PROGENy, ssGSEA |
| Publication figures | ❌ NOT DONE | ❌ Multi-panel figures |
| Multi-patient comparison | ❌ NOT DONE | ❌ H27259T vs H29433T |
| PN_Lung characterization | ❓ Status unclear | ❌ Need to verify and include |

### Revised Phase Plan

### PHASE 0: Data Reconnaissance (NEW — 30 min)

**DO NOT run any analysis yet. First, understand exactly what's in the file.**

Script: `experiments/phase0_recon.py`

1. Load `adata_v4.h5ad`
2. Print ALL column names in `adata.obs` (not just first 20)
3. Print ALL keys in `adata.obsm` and `adata.uns`
4. Print protein feature names (which are in `adata.var` vs `adata.obsm`)
5. Print unique values for: `sample`, `tissue`, `condition`, `patient`, `cell_type_v2`, `TLS_status`, `CAF_subtype`
6. Print: is `adata.X` the log1p-normalized RNA, raw counts, or something else?
7. Print: where are protein values stored? (`adata.obsm['protein']`? `adata.X` has protein columns?)
8. Print: what pre-computed domains exist? (`BANKSY_domain`? `squidpy_domain`? key names?)
9. Print: PN_Lung — is it in the data? How many cells?
10. Print: RNA–protein concordance values (retrieve from `adata.uns` or wherever stored)

**Output:** `experiments/phase0_recon_report.txt` — a complete inventory.

**CRITICAL**: This phase determines the exact column names, data layout, and what every subsequent phase can reference. No assumptions.

### PHASE 1: Complete the Compositional Picture (NEW — fills gaps)

**Script:** `experiments/phase1_composition.py`

1. **Verify PN_Lung exists** and add to composition table
2. **Statistical testing** on the existing composition data:
   - scCODA for compositional differences between Tissue × Condition
   - Dirichlet regression: `cell_type_proportions ~ tissue + condition`
   - Report confidence intervals for all proportions
3. **Cell density analysis**: cells/mm² per sample (not just percentages)
4. **Spatial composition maps**: Squidpy `spatial_scatter` with cell type colors, one figure per sample, 2×2 panel layout (Breast/Lung × Tumor/Normal)

**Why this is new**: Your composition table has no error bars, no statistics, and PN_Lung is MIA.

### PHASE 2: RNA Differential Expression — Tumor vs Normal (NEW)

**Script:** `experiments/phase2_de.py`

Your checkpoint analysis covered 6 proteins. RNA-level DE across 380 genes is entirely new.

1. **Pseudobulk neighborhoods** (50-100 cells each via spatial KNN)
   - Aggregate RNA counts within each neighborhood
   - Design: `~ tissue + condition`
   - Contrast: Tumor vs Normal, per tissue
   - Tool: PyDESeq2

2. **Per-cell-type DE**: Pseudobulk within each cell type, then DE
   - Particularly: T cells, Macrophages, CAFs, Epithelial
   - Report: |log2FC| > 0.5, FDR < 0.05

3. **Protein-level DE** (extend your checkpoint analysis):
   - Run the same Mann-Whitney U + Cohen's d for ALL proteins, not just checkpoints
   - Add PT_Lung vs PN_Lung comparison (the gap)
   - All cell types, not just T Cell + Macrophage

4. **Spatial gene detection**: Squidpy `spatial_autocorr` (Moran's I) for top DEGs
   - Validates that DE genes show spatial patterning

### PHASE 3: Spatial Domain & BANKSY Analysis (NEW, or verify existing)

**Script:** `experiments/phase3_banksy.py`

The metadata says "squidpy + banksy pre-computed" but no results were reported.

1. **Verify pre-computed domains**: What exactly exists in `adata.obs`?
   - Column name, number of domains, λ used
   - If results exist: characterize them (composition, size, spatial organization)
   - If NOT adequate: re-run BANKSY with λ sweep [0.2, 0.35, 0.5, 0.65, 0.8]

2. **Domain-level enrichment**: Extend existing nhood enrichment to BANKSY domains
   - Which cell types co-occur within each domain?
   - Domain-specific checkpoint expression (extend your checkpoint analysis per-domain)

3. **Tumor boundary analysis**:
   - Define tumor margin: cells within 100µm of any Epithelial cell
   - Compare immune composition: tumor core vs margin vs stroma
   - Gradient plots: immune cell density vs distance to nearest tumor cell

### PHASE 4: Cell-Cell Communication (ENTIRELY NEW)

**Script:** `experiments/phase4_ccc.py`

This is a major gap. You have spatial coordinates and cell types — CCI is the natural next analysis.

1. **COMMOT** (optimal transport-based, spatial-aware):
   - Use `commot.tl.spatial_signaling_ot`
   - Database: CellChatDB or OmniPath (via omnipath package already installed)
   - Per-sample analysis (too large for all-at-once)
   - Filter: only LR pairs where BOTH genes are in the 380-gene panel
   - Report: directional signaling (source → target cell type + spatial gradient)

2. **CellPhoneDB validation** (via existing `cellphonedb_analysis` tool in SpatialAgent):
   - Run on the same data
   - Compare COMMOT vs CellPhoneDB agreements

3. **Tumor-specific signaling**:
   - Focus: Epithelial → T Cell, Epithelial → Macrophage, CAF → Epithelial
   - Checkpoint-related LR pairs: PD1-PDL1, VISTA ligands, LAG3-MHCII

### PHASE 5: TLS Deep Dive (EXTEND existing)

**Script:** `experiments/phase5_tls.py`

Your TLS scoring (Section 3.3) is solid but descriptive. Extend to:

1. **TLS spatial gradients**: Gene/protein expression as a function of distance from TLS centroid
   - What changes as you move 0→50→100→200µm from a TLS?
   - Chemokine gradients, immune activation markers

2. **TLS maturity grading in PT_Lung**:
   - Score cells for GC markers (AICDA, BCL6, MKI67 — check panel coverage)
   - Classify TLS as early (B+T co-localization only), mature (+GC program), or regressed
   - Compare composition by maturity class

3. **Within-TLS cell communication**:
   - COMMOT restricted to cells within TLS
   - B cell → T cell signaling, Tfh → B cell interactions

4. **Peritumoral TLS**: Are TLS in PT_Lung tumor-proximal or distal?
   - Distance distribution: TLS centroid → nearest tumor epithelial cell

### PHASE 6: CAF Subtype Analysis (ENTIRELY NEW)

**Script:** `experiments/phase6_cafs.py`

1. **Verify CAF subtypes exist**: `CAF_subtype` column — unique values, counts per sample
2. **Spatial distribution**: Per-subtype scatter plots
3. **Tumor proximity**: Distance of each CAF subtype to nearest Epithelial cell → statistical comparison
4. **CAF-immune interactions**: What immune cells co-localize with each CAF subtype?
   - nhood_enrichment per CAF subtype
5. **CAF checkpoint expression**: Protein-level checkpoints per CAF subtype
   - Extension of your existing checkpoint analysis

### PHASE 7: Multi-Patient Comparison (ENTIRELY NEW)

**Script:** `experiments/phase7_patients.py`

All analyses so far use data from both patients pooled. Need to validate reproducibility.

1. **Composition consistency**: Compare cell type proportions H27259T vs H29433T
2. **DE replication**: Run Phase 2 DE per-patient, compare overlap
3. **TLS reproducibility**: Compare PT_Lung TLS metrics between patients
4. **Report**: Patient-level concordance metrics; flag patient-specific findings

### PHASE 8: Pathway Enrichment (ENTIRELY NEW)

**Script:** `experiments/phase8_pathways.py`

With only 380 genes, standard GSEA is underpowered. Use methods designed for targeted panels:

1. **PROGENy** (14 pathways) — via `decoupler-py`:
   - Scores every cell for pathway activity from panel genes
   - Compare Tumor vs Normal per pathway

2. **ssGSEA** for hallmark gene sets:
   - Use genes present in the 380-gene panel
   - Report only gene sets with ≥5 overlapping genes

3. **Per-cell-type pathway analysis**:
   - PROGENy scores stratified by cell type and condition

### PHASE 9: Publication Figures (INTEGRATE ALL)

**Script:** `experiments/phase9_figures.py`

Build multi-panel figures pulling from all completed phases.

**Figure 1 — Study Overview**: Schematic, UMAP, composition bars with CIs
**Figure 2 — Spatial Organization**: Spatially-colored scatter plots, BANKSY domains, nhood enrichment (re-use your existing Z-score heatmaps!)
**Figure 3 — RNA + Protein DE**: Volcano plots (RNA) + Cohen's d barplots (protein) side by side
**Figure 4 — Cell-Cell Communication**: COMMOT chord diagrams + CellPhoneDB heatmap
**Figure 5 — TLS Architecture**: PT_Lung TLS spatial maps + maturity grading + gradient plots
**Figure 6 — Immune Checkpoint Landscape**: Extend your Section 3.4 with Lung data + all cell types
**Supplementary**: QC, BANKSY λ sweep, patient-level replicates, full DE tables

---

## 2. What NOT To Do

These analyses from the original plan are now **SKIPPED** because you've already done them:

- ❌ QC filtering (done: MAD-based, RNA≥10, neg probe<0.2)
- ❌ Normalization (done: log1p RNA + CLR protein + Harmony)
- ❌ Cell type annotation (done: `cell_type_v2` via Leiden + protein CLR rescue)
- ❌ B cell definition (done: CD20 CLR>1.0 AND MS4A1>0)
- ❌ Basic composition table for PT_Lung/PT_Breast/PN_Breast (done)
- ❌ Neighborhood enrichment for 3 samples (done: permutation Z-scores at 50µm)
- ❌ Checkpoint protein analysis for PT_Breast vs PN_Breast (done: MWU + Cohen's d)
- ❌ TLS scoring for 3 samples (done: B cell % + TLS score + T→B distance)
- ❌ RNA–protein concordance (done: Spearman ρ)

---

## 3. Package Requirements (Updated)

### Already Installed

```
scanpy 1.11.5, squidpy 1.8.1, anndata 0.12.13
scvi-tools 1.4.2, omnipath 1.0.12, spatialdata 0.7.3
```

### Must Install (6 packages)

```bash
~/miniforge3/envs/spatial_agent/bin/pip install \
  commot \
  pydeseq2 \
  decoupler-py \
  gseapy \
  adjustText \
  statannotations
```

| Package | Used In | Priority |
|---|---|---|
| **commot** | Phase 4 (CCI) | CRITICAL |
| **pydeseq2** | Phase 2 (RNA DE) | CRITICAL |
| **decoupler-py** | Phase 8 (Pathways) | HIGH |
| **gseapy** | Phase 8 (ssGSEA) | HIGH |
| **adjustText** | Phase 9 (Figures) | MED |
| **statannotations** | Phase 9 (Figures) | MED |

**BANKSY**: Check if pre-computed domains are sufficient. Only install if re-running.
**Cell2location**: NOT needed (cell types already annotated).
**Tangram**: NOT needed this round (already in SpatialAgent tools if needed later).

### Memory Strategy

1.28M cells × 380 genes + protein columns. Key tactics:

- Sparse CSR matrices for RNA counts
- Per-sample subsetting for BANKSY and COMMOT (these are O(N²))
- Pseudobulk aggregation early in Phase 2 (reduces N by 100-1000×)
- Use the conda env's Python for `scipy.sparse` acceleration

---

## 4. Execution Order

```
Phase 0 (recon) ← RUN FIRST — determines everything else
    │
    ├── Phase 1 (composition gaps) ← quick win, fills table
    ├── Phase 2 (RNA DE) ← computationally heavy, start early
    ├── Phase 3 (BANKSY domains) ← verify then extend
    │
    ├── Phase 4 (CCI) ← depends on Phase 0 column names
    ├── Phase 5 (TLS deep dive) ← extends existing Section 3.3
    ├── Phase 6 (CAFs) ← new
    ├── Phase 7 (patients) ← runs after Phase 1+2 have results
    ├── Phase 8 (pathways) ← runs after Phase 2 has DEGs
    │
    └── Phase 9 (figures) ← INTEGRATES ALL
```

**Parallelizable**: Phases 1, 2, 3, 4, 5, 6 can all start after Phase 0.
**Sequential**: Phase 7 after 1+2, Phase 8 after 2, Phase 9 after everything.

---

## 5. File Structure (Revised)

```
~/SpatialAgent/
├── experiments/
│   ├── phase0_recon.py                # NEW: data inventory
│   ├── phase0_recon_report.txt        # Output
│   ├── phase1_composition.py          # NEW: complete the table
│   ├── phase2_de.py                   # NEW: RNA + full protein DE
│   ├── phase3_banksy.py               # NEW: domain characterization
│   ├── phase4_ccc.py                  # NEW: COMMOT + CellPhoneDB
│   ├── phase5_tls.py                  # NEW: TLS deep dive
│   ├── phase6_cafs.py                 # NEW: CAF spatial analysis
│   ├── phase7_patients.py             # NEW: multi-patient validation
│   ├── phase8_pathways.py             # NEW: PROGENy + ssGSEA
│   ├── phase9_figures.py              # NEW: publication figures
│   └── existing/                      # Move existing analysis here
│       └── (your existing notebook/scripts)
├── .hermes/
│   └── plans/
│       └── 2026-05-09_154500-xenium-full-pipeline.md  # Original (superseded)
│       └── 2026-05-09_160000-xenium-revised-pipeline.md # THIS PLAN
└── spatialagent/                      # Agent code (unchanged)
```

---

## 6. Open Questions (Resolved by Phase 0 Recon)

| Question | Why It Matters |
|---|---|
| Exact column names for cell_type, TLS, CAF, BANKSY | Every script references these |
| Where are protein values stored? | Affects Phase 2 protein DE |
| Is `adata.X` the normalized (log1p) RNA? | Affects Phase 2 pseudobulk (need raw counts) |
| Does PN_Lung exist? How many cells? | Fills composition table gap |
| What pre-computed domains exist? | Phase 3 — verify vs re-run |
| What are the CAF subtypes? | Phase 6 |
| Slide/section identifiers | Batch correction awareness |
| Where is RNA-protein concordance stored? | Retrieve for reporting |

---

## 7. What Makes This "Published"

Based on the literature review (2 parallel subagents, 2020-2026 spatial transcriptomics methods):

| Publication Standard | How We Meet It |
|---|---|
| Cell typing validated by 2+ methods | Your Leiden + protein CLR rescue; add BANKSY validation |
| Spatial autocorrelation accounted for | Pseudobulk DE (neighborhoods = replicates) |
| Compositional statistics | scCODA + Dirichlet regression (not just barplots) |
| Effect sizes alongside p-values | Cohen's d for proteins; log2FC for RNA |
| Multiple testing correction | BH FDR throughout |
| Spatial cell communication | COMMOT (Nature Methods 2023) + CellPhoneDB validation |
| Reproducibility | Per-patient replication; conda env; pinned versions |
| Multi-modal integration | RNA + protein concordance (already done!) + parallel analysis |
| Code availability | All scripts in `experiments/`; session_info.txt |

**Your existing analysis is already strong.** The checkpoint finding (VISTA down in PT_Breast, not up) is genuinely interesting and counterintuitive — that's a publication-worthy result. The new phases fill the gaps:

- RNA-level DE to complement protein checkpoints
- Cell-cell communication to explain the nhood enrichment patterns you already found
- TLS deep dive because PT_Lung's 83.5% TLS score is striking
- Multi-patient validation for rigor
- Publication-quality figures that integrate everything

---

*Revised plan written by Hermes. Original plan superseded. Key change: shifted from "run everything from scratch" to "extend your substantial existing analysis with 9 targeted new phases."*
