"""Quick inspection of the user's Xenium h5ad file"""
import sys
sys.path.insert(0, '/Users/tommytran/SpatialAgent')
import anndata, numpy as np

print("Loading /Users/tommytran/Downloads/xenium_atlas_v2/data/adata_v4.h5ad...")
adata = anndata.read_h5ad('/Users/tommytran/Downloads/xenium_atlas_v2/data/adata_v4.h5ad')

print(f"\nShape: {adata.shape[0]} cells x {adata.shape[1]} genes")
print(f"Size in memory: {adata.n_obs * adata.n_vars * 4 / 1e6:.1f} MB (dense)")
print(f"\nObs columns ({len(adata.obs.columns)}):")
for c in adata.obs.columns[:20]:
    print(f"  {c}: {adata.obs[c].dtype}")
if len(adata.obs.columns) > 20:
    print(f"  ... and {len(adata.obs.columns) - 20} more")

print(f"\nVar columns ({len(adata.var.columns)}):")
for c in adata.var.columns:
    print(f"  {c}: {adata.var[c].dtype}")

print(f"\nObs sample values:")
for c in adata.obs.columns[:8]:
    vals = adata.obs[c].dropna().unique()
    if len(vals) < 20:
        print(f"  {c}: {sorted(vals)}")
    else:
        print(f"  {c}: {len(vals)} unique values, e.g. {vals[:3]}...")

print(f"\nTop 10 genes by mean expression:")
means = np.array(adata.X.mean(axis=0)).flatten()
top_idx = np.argsort(means)[::-1][:10]
for i in top_idx:
    print(f"  {adata.var_names[i]}: {means[i]:.3f}")
