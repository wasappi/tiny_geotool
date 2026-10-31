from statistics import fmean

CATEGORY_KEYS = ["water_pct", "built_bare_pct", "sparse_veg_pct", "dense_veg_pct"]

def summarize(measures: list[dict]) -> dict:
    """Average land-cover composition over the usable (clear) measures."""
    usable = [m for m in measures if m["usable"]]
    summary = None
    if usable:
        summary = {key: fmean(m[key] for m in usable) for key in CATEGORY_KEYS}
    return {"summary": summary, "usable_count": len(usable)}