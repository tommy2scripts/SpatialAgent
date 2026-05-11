# Plan: Phase 2B Publication Prep, Phase 3 (BANKSY Domains), and Manuscript Skeleton

## Goal
Elevate the Phase 2B remediation to strict publication-ready standards, execute Phase 3 (BANKSY spatial domain characterization) with rigorous domain-concordance checks, and synthesize the findings into an "effect-size-first" manuscript skeleton that adheres to the matched-case analysis contract.

## Data Lessons & Improvements Applied
Based on our Phase 2B findings, we must apply the following improvements to this next phase:
1. **Confounding Awareness:** Tissue and condition (Breast vs. Lung) completely drive baseline distributions. Phase 3 must characterize domains *per-sample* or use mapping strategies to align cross-tissue archetypes before making claims.
2. **Domain Redundancy Check:** The dataset contains `spatial_domain_banksy` (34 domains), `banksy_domain` (98 domains!), and `spatial_domain_squidpy` (24 domains). Before running endless enrichment stats, we must quantify their overlap.
3. **Publication-Ready Figures:** Current PNG outputs are insufficient. We need vector formats (PDF/SVG), colorblind-safe palettes (Okabe-Ito), consistent paneling, and the mandatory "matched-case" caveat hardcoded into the plots.

---

## Step-by-Step Plan

### Part A: Phase 2B Main Figure Finalization (Publication Ready)
Instead of just tweaking the PNG, we will build a professional, multi-panel figure script.
- **Actions:**
  1. Update scripts to export `.pdf` and `.svg` alongside high-res (300 DPI) `.png`.
  2. Enforce `seaborn.set_context("paper")` and uniform typography (e.g., Helvetica/Arial).
  3. Ensure color mapping is consistent (e.g., PN_Breast and PT_Breast use paired colors).
  4. Fix the permutation null model text (standardize to 25 or scale up to 100 permutations explicitly).
  5. Add a standalone markdown file (`FIGURE_2B_LEGEND.md`) with a properly structured academic legend (Title, description of panels A-G, stats tests used, effect size reporting, and the matched-case caveat).

### Part B: Phase 3 (BANKSY vs. Squidpy Spatial Domains)
We will not blindly mirror Phase 2B. Spatial domains require structural validation first.
- **Actions:**
  1. **Redundancy/Concordance Audit:** Calculate the Adjusted Rand Index (ARI) and normalized mutual information (NMI) between `spatial_domain_banksy`, `banksy_domain`, and `spatial_domain_squidpy` per sample. 
  2. **Domain Annotation:** For the chosen domain system, compute the cell-type composition of each domain (e.g., "Domain 1 = 80% Tumour Epithelial + 10% Fibroblast → Tumor Core").
  3. **VISTA Mapping:** Map the VISTA-high macrophages (using the within-sample thresholds from Phase 2B v2) into these newly annotated functional domains. 
  4. **Enrichment Stats:** Apply the Phase 2B v2 standards: permutation null testing and min-count ≥20 filtering.

### Part C: Manuscript Skeleton Generation
Consolidate Phase 2A (VISTA PN > PT), Phase 2B v2 (Non-resident, immunoregulatory state), and Phase 3 (Spatial niches).
- **Actions:**
  1. Draft `MANUSCRIPT_SKELETON.md`.
  2. **Strict Language Constraints:** Enforce Tommy's contract. Use "hypothesis-generating", "matched-case", and "effect-size-first". Prohibit "validated", "population-level", or "reveals".
  3. Outline Introduction, Results (split by Phase), Methods Summary (highlighting the thresholding and null models), and Caveats/Limitations.

---

## Files Likely to Change
- `experiments/phase2B_v2_vista_macrophage_remediation/phase2b_pub_figure.py` (New script for vector graphics)
- `experiments/phase3_banksy_domains/phase3_domain_concordance.py`
- `experiments/phase3_banksy_domains/phase3_vista_mapping.py`
- `collaboration/FIGURE_2B_LEGEND.md`
- `collaboration/MANUSCRIPT_SKELETON.md`

## Risks, Tradeoffs, and Open Questions
- **Domain Fragmentation:** 98 BANKSY domains is severe over-clustering for 4 samples. We will likely drop `banksy_domain` and focus on the 34-domain `spatial_domain_banksy` versus the 24-domain Squidpy output. If ARI is high (>0.7), we will consolidate and report on just one to avoid redundant panels.
- **Visual Clutter:** A 7-panel figure for Phase 2B might be too dense for a single page print. If necessary, we will plan to split it into a Main Figure (4 panels) and a Supplemental Figure (3 panels).