# SpatialAgent Full Pipeline — Xenium 1.28M Cell Atlas Analysis

**Date:** 2026-05-09 15:45 PDT
**Status:** Plan (no execution)
**Goal:** Publication-ready spatial transcriptomics analysis of 1.28M Xenium cells (380 genes) across 4 sample types × 2 patients.

---

## 1. Data Inventory

| Asset | Value |
|---|---|
| **File** | `~/Downloads/xenium_atlas_v2/data/adata_v4.h5ad` |
| **Cells** | 1,280,000 |
| **Genes** | ~380 (Xenium panel) |
| **Sample types** | PN_Breast, PN_Lung, PT_Breast, PT_Lung (Primary Normal + Tumor) |
| **Patients** | H27259T, H29433T |
| **Pre-annotated** | `cell_type_v2` column (cell types), `x_centroid`, `y_centroid` (spatial) |
| **Pre-computed** | Squidpy + BANKSY spatial domains, TLS classification, CAF subtypes |

### Data Exploration First Step

Run `inspect_data.py` (already exists at `~/SpatialAgent/inspect_data.py`) to get exact column names, unique values, and spatial coordinate metadata before any analysis.

---

## 2. Literature-Backed Pipeline Design

Based on deep literature review (2 subagent passes across 2020-2026 spatial transcriptomics), the publication-grade pipeline combines:

| Phase | Method | Citation | Why |
|---|---|---|---|
| QC + Normalization | Scanpy + scran pooling | Luecken & Theis (2019) | Gold standard for single-cell QC |
| Cell type validation | BANKSY (λ sweep) + reference labels | Singhal et al. (2024) *Nature Genetics* | Validate pre-annotated labels with spatial coherence |
| Spatial domain discovery | BANKSY + Squidpy | Singhal (2024) + Palla (2022) *Nature Methods* | BANKSY finds domains, Squidpy characterizes interactions |
| Composition analysis | scCODA + Dirichlet regression | Büttner et al. (2021) *Nature Comms* | Compositional-aware statistical testing |
| Spatial differential expression | Pseudobulk neighborhoods + SPARK-X | Crowell et al. (2020) + Zhu et al. (2021) *Nature Methods* | Handles spatial autocorrelation; pseudobulk = statistical rigor |
| Neighborhood enrichment | Squidpy `nhood_enrichment` | Palla et al. (2022) | Permutation-based, well-cited |
| Cell-cell communication | COMMOT (primary) + CellPhoneDB (validation) | Cang & Nie (2023) *Nature Methods* + Efremova et al. (2020) | COMMOT models spatial distance decay; CellPhoneDB validates |
| TLS characterization | Gene signature scoring + BANKSY domain validation | Cabrita et al. (2020) *Nature* + Helmink et al. (2020) *Nature* | 12-chemokine + GC signatures |
| CAF spatial analysis | Squidpy neighborhood + distance-to-tumor | — | CAF subtypes already annotated |
| Publication figures | Scanpy/Squidpy/Matplotlib | scverse ecosystem | Reproducible, script-based (no manual adjustments) |

---

## 3. Package Installation Phase

### Currently Installed (conda env `spatial_agent` @ `~/miniforge3/envs/spatial_agent/`)

| Package | Version | Status |
|---|---|---|
| scanpy | 1.11.5 | READY |
| squidpy | 1.8.1 | READY |
| anndata | 0.12.13 | READY |
| scvi-tools | 1.4.2 | READY |
| omnipath | 1.0.12 | READY |
| spatialdata | 0.7.3 | READY |

### Must Install (for publication pipeline)

```bash
~/miniforge3/envs/spatial_agent/bin/pip install \
  banksy \
  commot \
  pydeseq2 \
  decoupler-py \
  celltypist \
  harmonypy \
  gseapy \
  adjustText \
  statannotations
```

| Package | Purpose | Priority |
|---|---|---|
| **banksy** | Spatial domain identification + λ stability analysis | CRITICAL |
| **commot** | Optimal-transport spatial cell-cell communication | CRITICAL |
| **pydeseq2** | Pseudobulk differential expression (DESeq2 in Python) | CRITICAL |
| **decoupler-py** | Pathway enrichment (PROGENy, ssGSEA for limited gene panels) | HIGH |
| **harmonypy** | Batch correction (patient/slide effects) | HIGH |
| **gseapy** | Gene set enrichment for publication tables | HIGH |
| **adjustText** | Label positioning on spatial plots | MED |
| **statannotations** | Statistical annotation on figures | MED |

### Cell2location

NOT needed. Data already has pre-annotated `cell_type_v2`. Skip unless we want de novo validation against a reference atlas.

### SPARK-X / nnSVG

SPARK-X is R-only. Use **SpatialDE** or **Squidpy's `spatial_autocorr`** (Moran's I) for spatial gene detection in Python. nnSVG is also R-only. Pseudobulk approach (below) is the recommended substitute for spatial DE in Python.

---

## 4. Phase-by-Phase Analysis Plan

### PHASE 0: Data Exploration & QC

**Script:** `experiments/phase0_qc.py`

1. Load `adata_v4.h5ad`
2. Print full column inventory (obs, var, obsm, uns)
3. QC metrics: n_genes_by_counts, total_counts, % mitochondrial (if MT genes in panel)
4. Filter: min 3 transcripts/cell (Xenium threshold)
5. Spatial QC: identify cells near tissue edges (lower quality)
6. Batch assessment: per-patient, per-sample distributions
7. Normalize: scran pooling via `sc.pp.normalize_total(target_sum=1e4)` + `sc.pp.log1p()`
8. Output: `experiments/phase0_exploration_report.txt` + `experiments/adata_qc.h5ad`

### PHASE 1: Cell Type Composition Analysis

**Script:** `experiments/phase1_composition.py`

Goal: Characterize cell type abundance across samples/tissues/conditions.

1. **Validate pre-annotated cell types**
   - Compare `cell_type_v2` to marker gene expression (dotplot per cell type)
   - BANKSY de novo clustering (λ=0.3-0.5) vs. `cell_type_v2` → ARI score
   - Report agreement; flag discordant populations

2. **Compositional profiling**
   - Per-sample cell type proportions (stacked barplot)
   - Per-tissue (Breast vs Lung) comparison
   - Tumor vs Normal enrichment per tissue

3. **Statistical testing**
   - scCODA for compositional differences (accounts for compositionality)
   - Fisher's exact test per cell type (with BH correction)
   - Dirichlet regression for tissue + condition effects

4. **Spatial composition**
   - Squidpy spatial scatter of cell types (one plot per sample)
   - Cell type density heatmaps (kernel density on x_centroid, y_centroid per sample)

**Outputs:**
- `experiments/phase1_composition_barplots.png`
- `experiments/phase1_spatial_scatter.png`
- `experiments/phase1_scCODA_results.csv`
- `experiments/phase1_fisher_results.csv`

### PHASE 2: Differential Expression — Tumor vs Normal

**Script:** `experiments/phase2_de.py`

THIS IS THE MOST STATISTICALLY DEMANDING PHASE. Pseudobulk is the gold standard.

1. **Spatial neighborhood definition**
   - For each sample, define spatial microdomains (50-100 cell neighborhoods)
   - Method: Leiden clustering on KNN spatial graph (k=30 neighbors)
   - Each neighborhood = one pseudobulk replicate

2. **Pseudobulk aggregation**
   - Sum counts within each neighborhood
   - Create pseudobulk count matrix: neighborhoods × genes

3. **Differential expression with PyDESeq2**
   - Design: `~ tissue + condition` (Breast/Lung + Tumor/Normal)
   - Contrast: Tumor vs Normal, stratified by tissue
   - Cutoffs: |log2FC| > 0.5, FDR < 0.05
   - Per cell-type DE: pseudobulk within each cell type, then Tumor vs Normal

4. **Spatial gene detection (complementary)**
   - Squidpy `spatial_autocorr` (Moran's I) for top DEGs
   - Validate that DE genes are spatially patterned

5. **Pathway enrichment** (decoupler-py)
   - PROGENy pathway scores (14 pathways) on pseudobulk
   - ssGSEA for Hallmark gene sets on per-cell scores

**Outputs:**
- `experiments/phase2_de_tumor_vs_normal.csv` (per-tissue and combined)
- `experiments/phase2_volcano_plots.png`
- `experiments/phase2_morans_I_heatmap.png`
- `experiments/phase2_pathway_enrichment.csv`

### PHASE 3: Spatial Neighborhood Analysis

**Script:** `experiments/phase3_spatial.py`

1. **Squidpy neighborhood enrichment**
   - Build spatial graph (`sq.gr.spatial_neighbors`, radius=50μm or Delaunay)
   - `sq.gr.nhood_enrichment` with 1000 permutations
   - Per-sample and per-tissue enrichment heatmaps

2. **BANKSY spatial domain discovery**
   - Already pre-computed (verify: λ parameter used, resolution)
   - If not adequate: re-run with λ sweep [0.2, 0.35, 0.5, 0.65, 0.8]
   - Select λ by ARI stability across the sweep
   - AGF filter: enable for structured tissues (breast ducts, lung alveoli)

3. **Domain characterization**
   - Cell type composition per BANKSY domain
   - Domain enrichment analysis (which cell types define each domain)
   - Domain size distribution and spatial organization

4. **Cell-cell communication within domains**
   - COMMOT: spatial-constrained LR analysis per domain
   - CellPhoneDB (via existing `cellphonedb_analysis` tool): validation
   - Focus on LR pairs where BOTH partners are in the 380-gene panel

**Outputs:**
- `experiments/phase3_nhood_enrichment_heatmaps.png`
- `experiments/phase3_banksy_domains.png`
- `experiments/phase3_domain_composition.csv`
- `experiments/phase3_commot_interactions.csv`

### PHASE 4: TLS Characterization

**Script:** `experiments/phase4_tls.py`

Since TLS classification is pre-computed:

1. **TLS spatial localization**
   - Spatial scatter colored by TLS status
   - TLS density per sample: TLS count / tissue area (mm²)
   - Distance-to-nearest-TLS for all cells (heatmap)

2. **TLS composition**
   - Cell type composition within TLS vs non-TLS regions
   - B:T cell ratio within TLS
   - Germinal center signature scoring (AICDA, BCL6, MKI67 if in panel)

3. **TLS neighborhood analysis**
   - What cell types surround TLS? (distance-binned composition)
   - nhood_enrichment: TLS cells vs all other cell types
   - Peritumoral vs intratumoral TLS comparison

4. **TLS maturity classification**
   - Score cells for 12-chemokine signature
   - GC score for mature TLS identification
   - Compare TLS maturity between Breast and Lung

**Outputs:**
- `experiments/phase4_tls_spatial.png`
- `experiments/phase4_tls_composition.csv`
- `experiments/phase4_tls_maturity.csv`

### PHASE 5: CAF Subtype Spatial Analysis

**Script:** `experiments/phase5_cafs.py`

1. **CAF subtype spatial distribution**
   - Per-CAF-subtype spatial scatter plots
   - CAF density relative to tumor border (distance gradient)
   - Which CAF subtypes are tumor-proximal vs distal?

2. **CAF-tumor cell communication**
   - COMMOT: CAF → tumor LR interactions
   - Focus: FAP, PDPN, COL1A1, TGFB1, PDGFRA/B (check panel coverage)
   - Squidpy ligrec for CAF-tumor enrichment

3. **CAF neighborhood composition**
   - What cell types co-localize with each CAF subtype?
   - nhood_enrichment per CAF subtype

**Outputs:**
- `experiments/phase5_caf_spatial.png`
- `experiments/phase5_caf_interactions.csv`

### PHASE 6: Integrated Publication Figures

**Script:** `experiments/phase6_figures.py`

1. **Figure 1: Study overview**
   - Schematic of samples (Breast/Lung × Normal/Tumor × 2 patients)
   - UMAP of all 1.28M cells colored by cell type
   - Cell type composition barplot across conditions

2. **Figure 2: Spatial organization**
   - Representative spatial scatter plots (1 per tissue type)
   - BANKSY spatial domains with cell type overlay
   - Neighborhood enrichment heatmap

3. **Figure 3: Differential expression**
   - Volcano plots (Tumor vs Normal, per tissue)
   - Top DEG heatmap
   - Pathway enrichment dotplot

4. **Figure 4: Cell-cell communication**
   - COMMOT LR chord diagrams for enriched interactions
   - CellPhoneDB validation heatmap
   - Spatial gradient of key LR pairs

5. **Figure 5: TLS and CAF analysis**
   - TLS spatial maps with cell type composition
   - CAF subtype spatial organization
   - Distance-to-tumor gradients

6. **Supplementary:**
   - QC metrics per sample
   - λ stability analysis for BANKSY
   - All statistical test results tables

---

## 5. SpatialAgent LLM Integration

SpatialAgent's LLM agent (via `make_llm("opencode-go/deepseek-v4-flash")`) will be used for:

| Task | Agent Role | Why |
|---|---|---|
| **Pipeline orchestration** | High-level decision making | Which tool to call, parameter selection |
| **Biological interpretation** | Result explanation | "Interpret these DEGs in the context of breast cancer" |
| **Literature context** | Background research | "Find papers on CAF subtypes in lung cancer" |
| **Figure caption writing** | Publication polish | Draft figure captions in Nature Methods style |
| **Error recovery** | Debugging tool failures | Detect tool errors, adjust parameters, retry |

### Agent Workflow Pattern

```python
from spatialagent.agent.spatialagent import SpatialAgent
from spatialagent.agent.make_llm import make_llm

llm = make_llm("opencode-go/deepseek-v4-flash")
agent = SpatialAgent(
    llm=llm,
    tools=[preprocess_spatial_data, summarize_celltypes, ...],  # from analytics.py
    act_timeout=3600,  # 1 hour for large analyses
)

# Phase-by-phase:
agent.run("""
    Load the QC'd data from experiments/adata_qc.h5ad.
    Run phase 1: cell type composition analysis.
    Generate composition barplots per sample and tissue.
    Run scCODA for statistical testing.
    Save results to experiments/phase1_*.
""")
```

### Co-agent delegation for code-intensive phases

For phases requiring complex custom code (Phase 2 DE, Phase 3 BANKSY):

```python
# In SpatialAgent REPL:
delegate_to_codex(task="""
    Write a Python script that performs pseudobulk DE analysis
    using PyDESeq2. Aggregate cells into spatial microdomains
    of 50-100 cells each using KNN spatial graph.
    Input: experiments/adata_qc.h5ad
    Output: experiments/phase2_de.py + results CSVs
""")
```

---

## 6. Execution Strategy

### Order Matters — Dependencies:

```
Phase 0 (QC) → Phase 1 (Composition) ──┐
                                        ├→ Phase 4 (TLS)
Phase 0 (QC) → Phase 2 (DE) ───────────┤
                                        ├→ Phase 5 (CAFs)
Phase 0 (QC) → Phase 3 (Spatial) ──────┤
                                        ├→ Phase 6 (Figures)
                                        └── ALL phases feed Phase 6
```

Phases 1, 2, 3 can run in parallel after Phase 0.
Phases 4 and 5 depend on Phase 3 results (spatial graph + domains).

### Per-Phase Checklist

For each phase:

- [ ] Install required packages
- [ ] Dedicated Python script in `experiments/phase{N}_{name}.py`
- [ ] All paths relative (no hardcoded `/Users/tommytran`)
- [ ] Checkpoint outputs (intermediate .h5ad saves)
- [ ] Logging: timestamp + duration + cell counts
- [ ] Error handling: try/except on heavy imports, memory-aware chunking for 1.28M cells
- [ ] Memory: use sparse matrices, subsetting when possible (1.28M cells × 380 genes is ~4GB dense)

---

## 7. Risks, Tradeoffs, and Open Questions

### Risks

| Risk | Mitigation |
|---|---|
| 1.28M cells → OOM on MacBook Air (8-16 GB RAM) | Use `.X` as sparse CSR; subset to 100K cells for development; use pseudobulk aggregation early |
| BANKSY O(N²) on 1M+ cells | Use ARD (approximate) mode; subset or run per-sample |
| COMMOT memory for optimal transport | Run per-sample, coarsen spatial graph |
| Missing packages may conflict with existing env | Use `--no-deps` cautiously; consider separate env if conflicts arise |
| Pre-computed domains may use unknown parameters | Re-run BANKSY ourselves for reproducibility |
| Cell types may be wrong/mislabeled | Phase 1 validation via BANKSY + marker gene dotplots |

### Open Questions (to resolve before execution)

1. **What exactly is in `adata.obs`?** Need to run `phase0_qc.py` first — likely columns include `sample`, `tissue`, `condition`, `patient`, `cell_type_v2`, `x_centroid`, `y_centroid`, `TLS_status`, `CAF_subtype`, `BANKSY_domain`, `squidpy_domain`.

2. **Spatial coordinates:** Are `x_centroid`/`y_centroid` in μm or pixels? In `obsm['spatial']` or `obs`? This affects neighborhood radius selection.

3. **Multiple sections per sample?** If each sample has multiple tissue sections, we need section-aware batch correction (Harmony).

4. **Is `adata.X` counts or normalized?** Phase 0 QC must check — raw counts needed for pseudobulk DE. If already normalized, need to locate raw counts (likely in `adata.raw` or `adata.layers['counts']`).

5. **BANKSY λ and resolution used for pre-computed domains?** If unknown, re-run to ensure reproducibility.

6. **Are there paired scRNA-seq references?** Not needed for cell typing (already pre-annotated) but valuable for validation.

---

## 8. File Structure

```
~/SpatialAgent/
├── experiments/
│   ├── phase0_qc.py                    # Data exploration + QC
│   ├── phase1_composition.py           # Cell type composition analysis
│   ├── phase2_de.py                    # Differential expression
│   ├── phase3_spatial.py               # Neighborhood analysis + BANKSY
│   ├── phase4_tls.py                   # TLS characterization
│   ├── phase5_cafs.py                  # CAF subtype spatial analysis
│   ├── phase6_figures.py               # Publication figures
│   ├── adata_qc.h5ad                   # QC'd AnnData
│   ├── phase0_exploration_report.txt   # Column inventory
│   ├── phase1_*.csv / phase1_*.png
│   ├── phase2_*.csv / phase2_*.png
│   ├── ...                             # All outputs
│   └── session_info.txt                # Package versions for reproducibility
├── .hermes/
│   └── plans/
│       └── 2026-05-09_154500-xenium-full-pipeline.md  # THIS PLAN
└── spatialagent/                       # Agent code (existing)
```

---

## 9. Next Actions

1. [ ] **Install missing packages** — `banksy`, `commot`, `pydeseq2`, `decoupler-py`, `harmonypy`, `gseapy`
2. [ ] **Run Phase 0** — `inspect_data.py` first, then full QC script
3. [ ] **Confirm column names** from Phase 0 output before writing Phase 1-5 scripts
4. [ ] **Resolve open questions** (Section 7) from Phase 0 exploration
5. [ ] **Execute Phase 1** (composition) — fastest win, validates data integrity
6. [ ] **Parallel Phases 2 + 3** — DE + spatial neighborhoods
7. [ ] **Phases 4 + 5** — TLS + CAFs (dependent on Phase 3 spatial graph)
8. [ ] **Phase 6** — publication figures from all results

---

*Plan written by Hermes using deepseek-v4-pro, informed by two parallel literature search subagents covering 2020-2026 spatial transcriptomics methods.*
