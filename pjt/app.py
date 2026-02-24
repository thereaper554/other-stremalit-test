import plotly.express as px

from data import load_data, latest_period_view
from alerts import make_alerts

st.set_page_config(page_title="Tool Life Tracker (AI Alerts)", layout="wide")

@st.cache_data
def _load():
    return load_data("data")

tool_master, tool_usage, tool_pred = _load()
latest = latest_period_view(tool_pred)

# Sidebar filters
st.sidebar.header("Filters")
facility = st.sidebar.multiselect("Facility", sorted(tool_master["casco_facility"].dropna().unique().tolist()))
supplier = st.sidebar.multiselect("Supplier", sorted(tool_master["supplier"].dropna().unique().tolist()))
oem = st.sidebar.multiselect("OEM", sorted(tool_master["oem"].dropna().unique().tolist()))
active_flag = st.sidebar.multiselect("Active Flag", sorted(tool_master["active_flag"].dropna().unique().tolist()))
origin = st.sidebar.multiselect("Origin", sorted(tool_master["tool_origin"].dropna().unique().tolist()))
inj = st.sidebar.multiselect("Injection Type", sorted(tool_master["injection_system_type"].dropna().unique().tolist()))

master_f = tool_master.copy()
if facility: master_f = master_f[master_f["casco_facility"].isin(facility)]
if supplier: master_f = master_f[master_f["supplier"].isin(supplier)]
if oem: master_f = master_f[master_f["oem"].isin(oem)]
if active_flag: master_f = master_f[master_f["active_flag"].isin(active_flag)]
if origin: master_f = master_f[master_f["tool_origin"].isin(origin)]
if inj: master_f = master_f[master_f["injection_system_type"].isin(inj)]

latest_f = latest.merge(master_f[["tool_id"]], on="tool_id", how="inner")

# KPIs
total_tools = master_f["tool_id"].nunique()
high_risk = (latest_f["predicted_risk_level"] == "HIGH").sum()
nearing_eol = (latest_f["attempt_tool_life_pct"] >= 80).sum()
replacement_required = ((latest_f["predicted_risk_level"] == "HIGH") | (latest_f["attempt_tool_life_pct"] >= 90) | (latest_f["predicted_remaining_shots"] < 50_000)).sum()
cost_exposure = master_f["related_cost"].sum()

st.title("Intelligent Tool Life Tracker + Alert System")

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Tools", f"{total_tools}")
c2.metric("High Risk (AI)", f"{high_risk}")
c3.metric("Nearing EOL (>=80%)", f"{nearing_eol}")
c4.metric("Replacement Required", f"{replacement_required}")
c5.metric("Total Cost Exposure ($)", f"{cost_exposure:,}")

# Alerts panel
st.subheader("Alerts (AI + Rules)")
alerts_df = make_alerts(master_f, latest_f)

if alerts_df.empty:
    st.info("No alerts triggered for the current filters.")
else:
    st.dataframe(alerts_df, use_container_width=True, height=260)
    st.download_button(
        "Download Alerts CSV",
        data=alerts_df.to_csv(index=False).encode("utf-8"),
        file_name="alerts.csv",
        mime="text/csv"
    )

# Tool table
st.subheader("Tool Table (Latest Period)")
tool_table = latest_f.merge(
    master_f[["tool_id","supplier","casco_facility","oem","tool_origin","injection_system_type","active_flag","related_cost","warranty_shots"]],
    on="tool_id",
    how="left"
)

search = st.text_input("Search tool_id / supplier / facility", "")
if search.strip():
    s = search.strip().lower()
    tool_table = tool_table[
        tool_table["tool_id"].str.lower().str.contains(s) |
        tool_table["supplier"].str.lower().str.contains(s) |
        tool_table["casco_facility"].str.lower().str.contains(s)
    ]

show_cols = [
    "tool_id","supplier","casco_facility","oem","active_flag",
    "attempt_tool_life_pct","forecast_remaining_life_pct",
    "predicted_risk_level","predicted_remaining_shots",
    "recommended_action","recommended_replacement_quarter",
    "related_cost"
]
tool_table = tool_table[show_cols].sort_values(["predicted_risk_level","attempt_tool_life_pct"], ascending=[True, False])
st.dataframe(tool_table, use_container_width=True, height=320)

# Tool detail
st.subheader("Tool Detail")
selected_tool = st.selectbox("Select a tool", sorted(master_f["tool_id"].unique().tolist()))
detail_pred = tool_pred[tool_pred["tool_id"] == selected_tool].sort_values("period_start_date")
detail_master = tool_master[tool_master["tool_id"] == selected_tool].iloc[0]

d1, d2, d3, d4 = st.columns(4)
d1.metric("Supplier", str(detail_master["supplier"]))
d2.metric("Warranty Shots", f"{int(detail_master['warranty_shots']):,}")
d3.metric("Origin", str(detail_master["tool_origin"]))
d4.metric("Shared Tool", str(detail_master["shared_tool_flag"]))

fig1 = px.line(detail_pred, x="period_start_date", y="cumulative_realized_shots", title="Cumulative Realized Shots")
st.plotly_chart(fig1, use_container_width=True)

fig2 = px.line(detail_pred, x="period_start_date", y="attempt_tool_life_pct", title="Attempt Tool Life % Over Time")
st.plotly_chart(fig2, use_container_width=True)

fig3 = px.line(detail_pred, x="period_start_date", y="predicted_remaining_shots", title="Predicted Remaining Shots Over Time")
st.plotly_chart(fig3, use_container_width=True)

st.write("Latest Recommendation:")

st.success(detail_pred.tail(1)[["predicted_risk_level","recommended_action","recommended_replacement_quarter"]].to_string(index=False))
