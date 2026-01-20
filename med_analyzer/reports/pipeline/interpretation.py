import re
def classify_abnormality(value, reference_range):
    """
    Classify test value as low / normal / high
    """
    if not reference_range:
        return "unknown"

    try:
        low, high = re.split(r"[-–]", reference_range)
        low, high = float(low.strip()), float(high.strip())
    except Exception:
        return "unknown"

    if value < low:
        return "low"
    elif value > high:
        return "high"
    else:
        return "normal"


def assign_risk_level(status):
    if status in ("high", "low"):
        return "needs_attention"
    elif status == "normal":
        return "no_action"
    return "unknown"


def generate_reason(test):
    if test['status']=='high':
        return f"The value is above the normal reference range ({test['reference_range']})."
    elif test["status"] == "low":
        return f"The value is below the normal reference range ({test['reference_range']})."
    elif test["status"] == "normal":
        return f"The value is within the normal reference range ({test['reference_range']})."
    else:
        return "Reference range not available to determine status."
    
    
def enrich_tests_with_interpretation(tests):
    enriched = []

    for t in tests:
        status = classify_abnormality(t["value"], t["reference_range"])
        reason = generate_reason({
            "status": status,
            "reference_range": t["reference_range"]
        })
        risk = assign_risk_level(status)

        enriched.append({
            **t,
            "status": status,
            "reason": reason,
            "risk_level": risk
        })

    return enriched