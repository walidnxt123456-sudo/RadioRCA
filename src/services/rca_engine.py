from .analytics import nr_coverage, lte_anchor, endc_analysis, geospatial

def execute_selected_rca(rca_code, context):
    """Routes the RCA request to the specialized module."""
    print(f"\n" + "-"*30)
    print(f"🚀 ROUTING TO: {rca_code}")
    print("-"*30)

    # Dictionary routing is cleaner than if/elif
    router = {
        "NR_COV": nr_coverage.analyze,
        "LTE_COV": lte_anchor.analyze,
        "ENDC_FAIL": endc_analysis.analyze,
        "GEO_DIST": geospatial.analyze
    }

    action = router.get(rca_code)
    if action:
        results = action(context)
    else:
        print(f"⚠️  RCA Code {rca_code} has no registered analyst.")
    
    # If we are in CLI, we format the dictionary back into a table
    if isinstance(results, dict) and "cells" in results:
        print("\n--- CLI TABLE VIEW ---")
        for cell in results["cells"]:
            print(f"{cell['cell_name']} | {cell['h_status']} | {cell['v_status']}")
        print(f"\nVERDICT: {results['verdict']}")