
def load_data(data_dir: str = "data"):
    tool_master = pd.read_csv(f"{data_dir}/tool_master.csv", parse_dates=["sop_date", "transfer_date"], dayfirst=False)
    tool_usage = pd.read_csv(f"{data_dir}/tool_usage.csv", parse_dates=["period_start_date"])
    tool_pred = pd.read_csv(f"{data_dir}/tool_predictions.csv", parse_dates=["period_start_date"])

    # Basic cleanup
    for df in (tool_master, tool_usage, tool_pred):
        df.columns = [c.strip() for c in df.columns]

    return tool_master, tool_usage, tool_pred

def latest_period_view(tool_pred: pd.DataFrame) -> pd.DataFrame:
    # pick latest row per tool
    tool_pred = tool_pred.sort_values(["tool_id", "period_start_date"])
    latest = tool_pred.groupby("tool_id").tail(1).reset_index(drop=True)

    return latest
