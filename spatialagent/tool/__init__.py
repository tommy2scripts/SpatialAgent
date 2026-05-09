"""
Modern function-based tools for SpatialAgent.

Exports are resolved lazily so lightweight imports such as
``from spatialagent.tool import delegate_to_codex`` do not require the full
scientific analysis stack.
"""

_EXPORT_MODULES = {
    # Database Tools
    "search_panglao": "databases",
    "search_cellmarker2": "databases",
    "search_czi_datasets": "databases",
    "extract_czi_markers": "databases",
    "download_czi_reference": "databases",
    "query_tissue_expression": "databases",
    "query_celltype_genesets": "databases",
    "validate_genes_expression": "databases",
    "query_disease_genes": "databases",
    # Literature Research Tools
    "query_pubmed": "literature",
    "query_arxiv": "literature",
    "search_semantic_scholar": "literature",
    "web_search": "literature",
    "extract_url_content": "literature",
    "extract_pdf_content": "literature",
    "fetch_supplementary_from_doi": "literature",
    # Analytics Tools
    "preprocess_spatial_data": "analytics",
    "harmony_transfer_labels": "analytics",
    "run_utag_clustering": "analytics",
    "aggregate_gene_voting": "analytics",
    "infer_dynamics": "analytics",
    "summarize_conditions": "analytics",
    "summarize_celltypes": "analytics",
    "summarize_tissue_regions": "analytics",
    "tangram_preprocess": "analytics",
    "tangram_map_cells": "analytics",
    "tangram_project_annotations": "analytics",
    "tangram_project_genes": "analytics",
    "tangram_evaluate": "analytics",
    "cellphonedb_prepare": "analytics",
    "cellphonedb_analysis": "analytics",
    "cellphonedb_degs_analysis": "analytics",
    "cellphonedb_filter": "analytics",
    "cellphonedb_plot": "analytics",
    "liana_tensor": "analytics",
    "liana_inference": "analytics",
    "liana_spatial": "analytics",
    "liana_misty": "analytics",
    "liana_plot": "analytics",
    "squidpy_spatial_neighbors": "analytics",
    "squidpy_nhood_enrichment": "analytics",
    "squidpy_co_occurrence": "analytics",
    "squidpy_spatial_autocorr": "analytics",
    "squidpy_ripley": "analytics",
    "squidpy_centrality": "analytics",
    "squidpy_interaction_matrix": "analytics",
    "squidpy_ligrec": "analytics",
    "destvi_deconvolution": "analytics",
    "cell2location_mapping": "analytics",
    "stereoscope_deconvolution": "analytics",
    "gimvi_imputation": "analytics",
    "spagcn_clustering": "analytics",
    "graphst_clustering": "analytics",
    "scanpy_score_genes": "analytics",
    "scanpy_ingest": "analytics",
    "scanpy_bbknn": "analytics",
    "scvelo_velocity": "analytics",
    "scvelo_velocity_embedding": "analytics",
    "cellrank_terminal_states": "analytics",
    "cellrank_fate_probabilities": "analytics",
    "paga_trajectory": "analytics",
    "totalvi_integration": "analytics",
    "multivi_integration": "analytics",
    "mofa_integration": "analytics",
    # Interpretation Tools
    "annotate_cell_types": "interpretation",
    "annotate_tissue_niches": "interpretation",
    "interpret_figure": "interpretation",
    # Subagent Tools
    "report_subagent": "subagent",
    "verification_subagent": "subagent",
    # CodeAct and external coding agents
    "create_python_repl_tool": "coding",
    "create_bash_tool": "coding",
    "delegate_to_claude_code": "coding",
    "delegate_to_codex": "coding",
    "delegate_to_opencode": "coding",
    # Support
    "inspect_tool_code": "foundry",
}

__all__ = list(_EXPORT_MODULES)


def __getattr__(name):
    if name not in _EXPORT_MODULES:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    from importlib import import_module

    module = import_module(f".{_EXPORT_MODULES[name]}", __name__)
    value = getattr(module, name)
    globals()[name] = value
    return value
