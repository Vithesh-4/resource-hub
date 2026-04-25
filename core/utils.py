import pandas as pd


# Convert list of recommendation objects into a DataFrame
def recommendations_to_dataframe(results):
    rows = []

    for r in results:
        rows.append({
            "resource_id": getattr(r, "resource_id", ""),
            "name": getattr(r, "name", ""),
            "category": getattr(r, "category", ""),
            "address": getattr(r, "address", ""),
            "city": getattr(r, "city", ""),
            "state": getattr(r, "state", ""),
            "zip_code": getattr(r, "zip_code", ""),
            "phone": getattr(r, "phone", ""),
            "website": getattr(r, "website", ""),
            "match_score": getattr(r, "match_score", 0),
            "explanation": getattr(r, "explanation", "")
        })

    # Return empty DataFrame if no results
    if not rows:
        return pd.DataFrame()

    return pd.DataFrame(rows)