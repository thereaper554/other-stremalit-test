import pandas as pd

SEV_ORDER = {"CRITICAL": 0, "WARN": 1, "INFO": 2}

def make_alerts(tool_master: pd.DataFrame, tool_pred_latest: pd.DataFrame) -> pd.DataFrame:
    """
    Alert rules:
    - predicted_risk_level == HIGH
    - attempt_tool_life_pct >= 80 (WARN) / >= 90 (CRITICAL)
    - sudden acceleration: accel_ratio > 1.30
    - predicted_remaining_shots < 50k
    - inactive tool still receiving qty (anomaly)
    """
    df = tool_pred_latest.merge(
        tool_master[["tool_id","active_flag","related_cost","supplier","casco_facility","oem","tool_origin","injection_system_type","shared_tool_flag","warranty_shots"]],
        on="tool_id",
        how="left"
    )

    alerts = []

    for _, r in df.iterrows():
        reasons = []
        severity = None

        if r["predicted_risk_level"] == "HIGH":
            reasons.append("AI risk model = HIGH")

        if r["attempt_tool_life_pct"] >= 90:
            reasons.append("Tool life >= 90% (near failure)")
            severity = "CRITICAL"
        elif r["attempt_tool_life_pct"] >= 80:
            reasons.append("Tool life >= 80% (warning)")
            severity = severity or "WARN"

        if r.get("accel_ratio", 1.0) > 1.30:
            reasons.append(f"Sudden acceleration detected (accel_ratio={r['accel_ratio']:.2f})")
            severity = severity or "WARN"

        if r["predicted_remaining_shots"] < 50_000:
            reasons.append("Predicted remaining shots < 50k")
            severity = "CRITICAL" if (severity == "CRITICAL" or r["attempt_tool_life_pct"] >= 85) else (severity or "WARN")

        if (r["active_flag"] == "Inactive") and (r["received_qty"] > 0):
            reasons.append("Data anomaly: inactive tool still receiving qty")
            severity = "WARN" if severity != "CRITICAL" else severity

        if reasons:
            if severity is None:
                severity = "INFO"
            alerts.append({
                "severity": severity,
                "tool_id": r["tool_id"],
                "period_start_date": r["period_start_date"],
                "supplier": r["supplier"],
                "facility": r["casco_facility"],
                "oem": r["oem"],
                "origin": r["tool_origin"],
                "injection_type": r["injection_system_type"],
                "shared_tool": r["shared_tool_flag"],
                "attempt_tool_life_pct": float(r["attempt_tool_life_pct"]),
                "predicted_remaining_shots": int(r["predicted_remaining_shots"]),
                "recommended_action": r.get("recommended_action", ""),
                "recommended_replacement_quarter": r.get("recommended_replacement_quarter", ""),
                "reason": " | ".join(reasons),
                "cost_exposure_usd": int(r.get("related_cost", 0))
            })

    out = pd.DataFrame(alerts)
    if out.empty:
        return out

    out["sev_rank"] = out["severity"].map(SEV_ORDER).fillna(99).astype(int)
    out = out.sort_values(["sev_rank", "attempt_tool_life_pct"], ascending=[True, False]).drop(columns=["sev_rank"])
    return out