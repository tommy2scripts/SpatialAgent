# Plan v2: Phase 3 — Structural Units & Physical Spatial Mapping

**Date:** 2026-05-10 01:30  
**Status:** Planning (no execution)  
**Iterates on:** `2026-05-10_012000-phase3-structural-units-spatial-maps.md`  
**Parent plan:** `2026-05-10_010500-phase2b-finalize-phase3-banksy.md`

---

## Goal

Replace "enriched in PT_Lung_6" with "enriched in Tumor Core" by meta-clustering spatial domains into functional Structural Units. Then generate physical tissue maps (X/Y coordinates) to show WHERE VISTA-high macrophages actually sit in tissue space — the most spatially honest visualization possible.

---

## 1. Architecture Decision: One Script, Not Two

Phase 2B v2 succeeded as a single 1,182-line script with clearly labeled `[1/8]` through `[8/8]` sections. Phase 3 follows the same pattern:

- **Script:** `experiments/phase3_structural_units.py`
- **Output dir:** `experiments/phase3_structural_units/`
- **Figures subdir:** `experiments/phase3_structural_units/figures/`
- **Report:** `experiments/phase3_structural_units/phase3_structural_units_report.md`

Sections: `[1/8] Load & Setup`, `[2/8] Domain Concordance`, `[3/8] Structural Unit Meta-Clustering`, `[4/8] VISTA-to-Unit Mapping`, `[5/8] Spatial Tissue Maps`, `[6/8] Zoom-In Insets`, `[7/8] Statistical Enrichment`, `[8/8] Report & Handoff`

---

## 2. Part A: Domain Concordance & Structural Unit Meta-Clustering

### 2.1 Concordance Audit (Section [2/8])

Domains are sample-specific — PN_Breast has domains named `PN_Breast_0` through `PN_Breast_N`, and these do NOT correspond to `PT_Breast_0`. So we compute ARI **per sample**, comparing BANKSY (34 total) vs Squidpy (24 total) labelings of the same cells.

```
Per sample:
  cells_in_sample = adata[adata.obs['sample'] == s]
  ari = adjusted_rand_score(cells_in_sample.obs['spatial_domain_banksy'],
                             cells_in_sample.obs['spatial_domain_squidpy'])
```

**Decision tree:**
- If mean ARI > 0.6 across samples → domains are concordant; use Squidpy (24 domains, cleaner) as primary, BANKSY as supplemental
- If mean ARI < 0.4 → domains diverge meaningfully; analyze both, report divergence as a finding
- If ARI is intermediate → use Squidpy as primary (fewer domains = fewer multiple-testing issues), note BANKSY concordance in supplement

**Output CSV:** `domain_concordance.csv` — ARI per sample, choice justification.

### 2.2 Composition Profiling (Section [3/8])

For the chosen domain set (likely Squidpy 24), compute per-domain cell-type composition:

```
For each sample, for each domain:
  domain_cells = adata[adata.obs['spatial_domain_squidpy'] == domain]
  ct_fractions = domain_cells.obs['cell_type_v2'].value_counts(normalize=True)
```

Result: a (N_domains × N_cell_types) composition matrix, where rows sum to 1.0.

**Output CSV:** `domain_celltype_composition.csv`

### 2.3 Structural Unit Meta-Clustering (Section [3/8] continued)

Cluster the composition matrix using **Ward's linkage on Euclidean distance** of cell-type proportion vectors. Cut the dendrogram at k=5 or k=6.

**Cluster interpretation and labeling:**
For each cluster, examine the top 3 cell types by mean fraction. Assign a biologically meaningful label:

| Top Cell Types | Label |
|---|---|
| Tumour_Epithelial > 0.5 | **Tumor Core** |
| Fibroblast > 0.4 | **Stroma** |
| T_Cell + B_Cell + Plasma > 0.3 | **Immune Infiltrate** |
| Normal_Epithelial > 0.4 | **Normal Epithelium** |
| Mixed Tumor + Immune | **Tumor-Immune Interface** |
| Mixed Fibroblast + Immune + Tumor | **Tumor-Stroma Interface** |

If a cluster doesn't cleanly match, label it by its dominant component (e.g., "Mixed Stromal-Immune").

**Edge case — Interface definition:** If clustering doesn't naturally produce an Interface unit, compute it post-hoc: cells within 50µm of both a Tumor Core domain AND an Immune Infiltrate/Stroma domain get labeled "Interface." This is added as a computational annotation, not a clustered domain.

**Output CSV:** `structural_units_dictionary.csv` — maps each `sample|domain_id` pair to its Structural Unit label.

**Output figure:** `structural_unit_dendrogram.png` — dendrogram with k=5/6 cut line, colored by unit.

### 2.4 Sample-Level Structural Unit Composition (Section [3/8] continued)

Generate a stacked bar chart showing the proportion of each Structural Unit per sample. This provides the macroscopic architectural comparison: "PT_Breast is 60% Tumor Core, PN_Breast is 45% Normal Epithelium."

**Output figure:** `structural_unit_composition_by_sample.png`

---

## 3. Part B: Spatial Tissue Maps (Sections [5/8] & [6/8])

### 3.1 Whole-Tissue Structural Maps

For each of the 4 samples, generate a 2D scatter plot using `adata.obsm['spatial']` (x_centroid, y_centroid columns in obs).

**Critical rendering parameters to avoid 1.2M-point crash:**
```python
ax.scatter(x, y, c=colors, s=0.5, rasterized=True, linewidth=0, alpha=0.6)
ax.set_rasterization_zorder(1)  # rasterize scatter, keep everything else vector
fig.savefig('map.pdf', dpi=300)  # rasterized layer at 300 DPI inside vector PDF
```

`s=0.5` makes each cell a tiny dot. `rasterized=True` embeds the scatter as a raster layer while keeping axes/labels/legend as vector — critical for journal submission where PDFs must be <10 MB.

**Color palette:** 5-6 qualitative colors (Tableau 10 or custom), one per Structural Unit. Avoid red-green.

**Layout:** 2×2 grid, one panel per sample. Fixed aspect ratio (`ax.set_aspect('equal')`). No axis ticks/spines (clean histological look). Add 200µm scale bar in bottom-right of each panel.

**Output figure:** `tissue_structural_maps.png` (raster preview) + `tissue_structural_maps.pdf` (vector/raster hybrid)

### 3.2 VISTA Macrophage Overlays

Same 2×2 layout, but now:
- Background: all cells in light gray (`color='#E0E0E0'`, `s=0.3`, `rasterized=True`)
- Foreground: VISTA-high macrophages in **orange** (`s=2`, `rasterized=True`, `zorder=10`)
- Foreground: VISTA-low macrophages in **blue** (`s=2`, `rasterized=True`, `zorder=9`)

This directly shows: do VISTA-high macrophages cluster near normal epithelium? Avoid tumor cores? Hug TLS boundaries?

**Output figure:** `tissue_vista_macrophage_overlay.png` + `.pdf`

### 3.3 Zoom-In Insets (Section [6/8])

Select 3-4 biologically interesting regions algorithmically, then generate cropped high-res panels.

**Region selection strategy:**
1. **TLS region:** Find all cells with `tls_class != 'None'`. Pick the TLS with the most VISTA-high macrophages nearby. Crop a 500µm × 500µm box around its centroid.
2. **Tumor-Normal boundary:** Find domains where Normal_Epithelial and Tumour_Epithelial domain labels are adjacent (within 100µm). Crop the boundary region.
3. **Tumor-Stroma boundary:** Same logic for Tumor Core + Stroma adjacency.
4. **Immune hot spot:** Region with highest T_Cell + B_Cell density.

For each inset:
- Plot all cells colored by Structural Unit (or cell type for the immune hot spot)
- Overlay VISTA-high macrophages as larger dots
- Add scale bar, minimal labels
- 4×1 or 2×2 panel

**Output figure:** `tissue_zoom_insets.png` + `.pdf`

---

## 4. Part C: Statistical Enrichment (Section [7/8])

Mirror Phase 2B v2 enrichment framework exactly, but replace `annotation_type='Squidpy_domain'` with `annotation_type='Structural_Unit'`.

### 4.1 VISTA-to-Unit Mapping (Section [4/8])

For each sample, for each Structural Unit:
- Count VISTA-high macrophages in that unit
- Count VISTA-low macrophages in that unit
- Compute enrichment ratio: `(high_in_unit / total_high) / (low_in_unit / total_low)`

### 4.2 Null Model Testing

25 label permutations (matching Phase 2B v2). For each permutation:
- Shuffle VISTA-high/low labels across all macrophages
- Recompute enrichment ratios
- Build null distribution for each unit

Report z-scores and empirical p-values.

### 4.3 Min-Count Filtering

Require ≥20 macrophages (high + low) in a Structural Unit to report enrichment. Units with fewer macrophages are noted but their enrichment ratios are suppressed as unreliable.

**Output CSV:** `structural_unit_enrichment.csv` (all rows) + `structural_unit_enrichment_filtered.csv` (min-count pass)

**Output figure:** `structural_unit_enrichment_barplot.png` — horizontal bar chart, enrichment ratio with permutation significance stars.

---

## 5. Part D: Manuscript Integration

### 5.1 Figure 3 Legend

Write `FIGURE_3_LEGEND.md` documenting:
- Panel A: Whole-tissue structural maps (4 samples)
- Panel B: VISTA macrophage overlay
- Panel C: Zoom-in insets (TLS, tumor margin, immune hot spot)
- Panel D: Structural Unit enrichment barplot

### 5.2 Manuscript Skeleton

Replace Section C of the parent plan with this consolidated approach:
- `manuscript/MANUSCRIPT_SKELETON.md` — full integration of Phase 2A + Phase 2B v2 + Phase 3

---

## 6. File Manifest

| File | Action | Lines (est.) |
|------|--------|-------------|
| `experiments/phase3_structural_units.py` | **CREATE** | ~800 |
| `experiments/phase3_structural_units/domain_concordance.csv` | Output | ~10 rows |
| `experiments/phase3_structural_units/domain_celltype_composition.csv` | Output | ~24 rows × 15 cell types |
| `experiments/phase3_structural_units/structural_units_dictionary.csv` | Output | ~24 rows |
| `experiments/phase3_structural_units/structural_unit_enrichment.csv` | Output | ~30 rows |
| `experiments/phase3_structural_units/structural_unit_enrichment_filtered.csv` | Output | ~15 rows |
| `experiments/phase3_structural_units/figures/structural_unit_dendrogram.png` | Output | 1 panel |
| `experiments/phase3_structural_units/figures/structural_unit_composition_by_sample.png` | Output | 1 panel |
| `experiments/phase3_structural_units/figures/tissue_structural_maps.png` | Output | 2×2 |
| `experiments/phase3_structural_units/figures/tissue_structural_maps.pdf` | Output | 2×2 vector |
| `experiments/phase3_structural_units/figures/tissue_vista_macrophage_overlay.png` | Output | 2×2 |
| `experiments/phase3_structural_units/figures/tissue_vista_macrophage_overlay.pdf` | Output | 2×2 vector |
| `experiments/phase3_structural_units/figures/tissue_zoom_insets.png` | Output | 4×1 |
| `experiments/phase3_structural_units/figures/tissue_zoom_insets.pdf` | Output | 4×1 vector |
| `experiments/phase3_structural_units/figures/structural_unit_enrichment_barplot.png` | Output | 1 panel |
| `experiments/phase3_structural_units/phase3_structural_units_report.md` | Output | Report |
| `collaboration/FIGURE_3_LEGEND.md` | **CREATE** | Legend |
| `manuscript/MANUSCRIPT_SKELETON.md` | **CREATE** | Integration |

---

## 7. Risks, Tradeoffs, Open Questions

### Risks
| Risk | Mitigation |
|------|-----------|
| 1.2M points crash matplotlib | `rasterized=True`, `s=0.5`, save as rasterized-in-PDF |
| Structural Unit clustering produces uninterpretable clusters | Fallback: manual domain annotation based on top-3 cell types |
| All BANKSY and Squidpy domains are concordant (ARI > 0.8) | Accept; report concordance; use Squidpy; Phase 3 validates rather than discovers |
| No zoom-in regions have enough VISTA-high macrophages to show | Lower threshold; report emptiness as a finding (VISTA-high are spatially diffuse) |
| Interface unit not naturally produced by clustering | Compute post-hoc: cells within 50µm of both Tumor + Immune/Stroma domains |

### Tradeoffs
- **One script vs two:** Single script (Phase 2B v2 pattern) = simpler execution but ~800 lines. Two scripts = modular but more orchestration. **Decision: one script.**
- **Squidpy primary vs BANKSY primary:** Squidpy has fewer domains (24 vs 34) → fewer multiple testing issues → cleaner Structural Units. BANKSY is supplemental. If ARI > 0.6, this holds. If ARI < 0.4, analyze both.
- **k=5 vs k=6 clusters:** Fewer clusters = cleaner labels, coarser biology. More clusters = finer resolution, risk of unlabeled clusters. Start with k=5, inspect, adjust.

### Open Questions
1. Should zoom-in insets show cell-type colors or Structural Unit colors? (Recommend: cell-type for immune hot spot, Structural Unit for tumor margin.)
2. Should we use the fine BANKSY (98 domains) for zoom-in insets to show finer architectural detail? (Recommend: no — 98 colors is unreadable. Use Structural Units.)
3. What threshold defines a TLS for zoom-in selection? (Use existing `tls_class` column; pick the TLS with most VISTA-high macrophages in its 200µm vicinity.)

---

## 8. Execution Constraints

- **Stats language:** "matched-case," "effect-size-first," "hypothesis-generating." NO "validated," "population-level," "reveals."
- **Permutation count:** 25 (consistent with Phase 2B v2; caveat in methods that 1000 would be ideal)
- **Min-count filter:** ≥20 macrophages per Structural Unit
- **Color schemes:** Colorblind-friendly (Tableau 10 or viridis-derived). No red-green.
- **Output resolution:** 300 DPI for PNG, vector PDF with rasterized scatter layers

---

*Plan v2 written 2026-05-10 01:30. Iterates on 2026-05-10_012000-phase3-structural-units-spatial-maps.md. Next: execute upon user approval.*
