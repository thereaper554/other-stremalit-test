from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

def load_data():
    tool_master = pd.read_csv(
        DATA_DIR / "tool_master.csv",
        parse_dates=["sop_date", "transfer_date"]
    )
    tool_usage = pd.read_csv(
        DATA_DIR / "tool_usage.csv",
        parse_dates=["period_start_date"]
    )
    tool_pred = pd.read_csv(
        DATA_DIR / "tool_predictions.csv",
        parse_dates=["period_start_date"]
    )

    for df in (tool_master, tool_usage, tool_pred):
        df.columns = [c.strip() for c in df.columns]

    return tool_master, tool_usage, tool_pred

def latest_period_view(tool_pred: pd.DataFrame) -> pd.DataFrame:
    tool_pred = tool_pred.sort_values(["tool_id", "period_start_date"])
    latest = tool_pred.groupby("tool_id").tail(1).reset_index(drop=True)
    return latest
