# Xenium Atlas Project State

## Dataset
Path:
`./data/adata_v4.h5ad` (located at `~/Downloads/xenium_atlas_v2/data/adata_v4.h5ad`)

Samples:
- PN_Breast
- PT_Breast
- PN_Lung
- PT_Lung

Design:
- 2-patient / 4-sample matched-case Xenium atlas
- Breast tumor-normal pair is one matched case
- Lung tumor-normal pair is one matched case
- Tissue and patient are confounded
- No biological replication
- Cells are not biological replicates

## Required interpretation language
Use:
- matched-case
- hypothesis-generating
- within-dataset
- effect-size-first
- main-figure candidate

Avoid:
- validated
- significant across patients
- population-level inference
- tumor suppresses VISTA
- breast/lung generalized conclusion

## Cleared completed work
Phase 0.5:
- RNA counts: layers["rna_counts"]
- RNA log-normalized: layers["rna_log_norm"] or adata.X
- Raw protein: obsm["protein_counts"]
- CLR protein: obsm["protein_clr"]
- Use complete spatial/QC mask for spatial analyses
- Do not use old checkpoint_n_positive
- neg_ctrl_rate excluded from QC
- B-lineage handled as derived flag, not 9th broad cell type

Phase 1:
- Composition atlas complete
- Safe as descriptive matched-case composition analysis

Phase 2A:
- PASS with conservative interpretation
- Stale-output/schema issue resolved
- Current files verified
- VISTA/VSIR can proceed to Phase 2B/main-figure candidacy
- VISTA raw protein supports PN > PT in both matched cases
- VISTA CLR supports PN > PT in both matched cases
- VSIR RNA supports VISTA protein at sample level
- Not simply global all-protein shift
- Still no population-level claims

## Current next task
Run Phase 2B:
VISTA/VSIR macrophage-state and spatial-niche analysis.

Main question:
What macrophage state or spatial niche does the VISTA/VSIR matched-case signal mark?
