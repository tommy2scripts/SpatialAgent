# Plan: Phase 3 (Structural Units & Physical Spatial Mapping) and Publication Prep

## Goal
Characterize the Xenium spatial domains, aggregate them into higher-order biologically meaningful "Structural Units", and generate physical spatial maps (X/Y coordinates) to provide true spatial awareness of where VISTA-high macrophages reside. Synthesize findings into a strictly formatted manuscript skeleton.

## Current Context & Data Lessons
- We have 3 pre-computed domain clusterings: `spatial_domain_banksy` (34), `banksy_domain` (98), and `spatial_domain_squidpy` (24).
- Reporting on 34 arbitrary numbered domains is biologically uninterpretable.
- The dataset contains physical coordinates `adata.obsm['spatial']` which have not yet been plotted to show the actual tissue architecture.
- We must maintain the "matched-case" and "effect-size-first" constraints established in earlier phases.

---

## Step-by-Step Plan

### Part A: Domain Concordance & "Structural Unit" Meta-Clustering
Instead of treating 34 domains as arbitrary numbers, we will group them functionally.
1. **Concordance Audit:** Calculate Adjusted Rand Index (ARI) between BANKSY (34) and Squidpy (24) per sample to see if they capture the same structures. Select the most robust one (likely Squidpy 24 or BANKSY 34).
2. **Composition Profiling:** Calculate the mean cell-type fractions for each domain (e.g., % Tumour Epithelial, % Fibroblast, % T_Cell).
3. **Structural Unit Categorization:** Use hierarchical clustering on the composition matrix to group the fine domains into 5–6 high-level **Structural Units** (e.g., *Tumor Core, Stroma, Immune Infiltrate/TLS, Normal Epithelium, Tumor-Stroma Interface*).
4. **Output:** `structural_units_dictionary.csv` mapping arbitrary domain IDs to functional Structural Units.

### Part B: Spatial Awareness Visualization (Physical Tissue Maps)
Generate publication-ready physical tissue maps using `adata.obsm['spatial']`.
1. **Whole-Tissue Structural Maps:** Plot the 4 samples (PN_Breast, PT_Breast, PN_Lung, PT_Lung) in 2D physical space, colored by the new Structural Units to show the macroscopic tissue architecture.
2. **VISTA-Macrophage Overlays:** Plot VISTA-high vs. VISTA-low macrophages directly onto the physical tissue maps. 
3. **Spatial Zoom-Ins (Insets):** Generate cropped zoom-in panels of key regions (e.g., a Mature TLS, a Tumor-Stroma boundary, a Normal Epithelial gland) highlighting the physical localization of VISTA-high macrophages.
4. **Format Standards:** Vector outputs (`.pdf`/`.svg`), `seaborn.set_context("paper")`, fixed aspect ratio (`equal`) so tissue isn't distorted, minus axis ticks/spines for a clean histological look.

### Part C: Structural Unit Enrichment (Statistical)
1. **Map VISTA Cells to Units:** Map the within-sample VISTA-high/low macrophages to the new Structural Units.
2. **Null Model Testing:** Rerun the 25-permutation null model from Phase 2B to verify if VISTA-high macrophages are statistically enriched or depleted in specific Structural Units (e.g., mathematically confirming they avoid the "Tumor Core" and enrich in "Normal Epithelium" or "Immune Infiltrate").
3. **Min-Count Filtering:** Require ≥20 macrophages per Structural Unit to report enrichment.

### Part D: Manuscript Skeleton Generation
1. Consolidate Phase 2A, Phase 2B v2, and Phase 3 Structural Niche findings.
2. **Strict Language Constraints:** Enforce Tommy's contract: "hypothesis-generating", "matched-case", and "effect-size-first". Prohibit "validated", "population-level", or "reveals".
3. Write `FIGURE_3_LEGEND.md` documenting the physical spatial maps and structural meta-clustering.

---

## Files Likely to Change
- `experiments/phase3_spatial_architecture/phase3_structural_units.py` (Domain clustering & mapping)
- `experiments/phase3_spatial_architecture/phase3_tissue_maps.py` (Physical X/Y plotting)
- `collaboration/FIGURE_3_LEGEND.md`
- `collaboration/MANUSCRIPT_SKELETON.md`

## Risks, Tradeoffs, and Open Questions
- **Memory/Plotting Bottleneck:** Plotting 1.2 million points (all cells) across 4 samples can crash matplotlib or generate massive PDFs. We will plot points as rasterized layers (`rasterized=True` for scatter) inside the PDF, or use datashader/hexbins if scatterplots are too dense, while keeping axes/text as vectors.
- **Interface Definition:** "Tumor-Stroma Interface" might not fall neatly into a single spatial domain. If the clustering doesn't naturally produce an "Interface" unit, we will define it computationally (cells within *X* µm of both Tumor and Stroma units).