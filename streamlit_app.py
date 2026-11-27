import json
import math
from pathlib import Path

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

ROOT = Path(__file__).parent
SEGMENTS = ["Lower spend", "Moderate spend", "High value"]
COLORS = ["#5888b8", "#168975", "#c62828"]
REQUIRED = ["CustomerID", "InvoiceNo", "Quantity", "UnitPrice"]

st.set_page_config(page_title="Segmint", layout="wide")
st.markdown("""
<style>
[data-testid="stSidebar"] {background: linear-gradient(155deg, #edf3e9, #daeade);}
.segmint-brand {display:flex; align-items:center; gap:14px; font-size:30px;
    font-weight:800; letter-spacing:-.04em; color:#101820;
    border-bottom:1px solid #becfc4; padding-bottom:18px; margin-bottom:10px;}
.segmint-mark {display:inline-flex; align-items:flex-end; gap:4px; height:26px;}
.segmint-mark i {display:block; width:6px; border-radius:2px; background:#087653;}
.segmint-mark i:nth-child(1) {height:10px;}
.segmint-mark i:nth-child(2) {height:17px;}
.segmint-mark i:nth-child(3) {height:25px;}
[data-testid="stMain"] h1 {font-size:clamp(2.5rem, 4.8vw, 3.6rem); font-weight:850; letter-spacing:-.045em;}
[data-testid="stMain"] h3 {font-size:clamp(1.35rem, 2.2vw, 1.9rem); font-weight:800; letter-spacing:-.035em;}
.segment-card {border-left:6px solid var(--segment); background:var(--tint); padding:18px 22px;
    border-radius:12px; color:#46545a; font-size:1.08rem; line-height:1.5;}
.segment-card strong {display:block; color:#101820; font-size:1.45rem; font-weight:800; letter-spacing:-.035em;}
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {
    position:relative; min-height:168px; display:flex; flex-direction:column; justify-content:center;
    text-align:center; background:#f6faf45c; border:1.5px dashed #7d9589; border-radius:12px; padding:16px;}
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzoneInstructions"] {display:none;}
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"]::before {
    content:"↑"; font-size:34px; font-weight:800; line-height:1; color:#375b4d; pointer-events:none;}
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"]::after {
    content:"CSV or Excel (.csv, .xlsx, .xls)"; color:#465b51; font-size:.8rem; pointer-events:none;}
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button {
    background:transparent; border:0; color:#10201b; white-space:normal; min-height:58px;}
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button > * {
    position:absolute; width:1px; height:1px; overflow:hidden; clip-path:inset(50%);}
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button::after {
    content:"Drop a CSV or Excel file here, or click to browse"; max-width:185px; font-size:.95rem;}
.segment-legend {display:flex; flex-wrap:wrap; justify-content:space-between; gap:8px 16px; padding:5px 6px 8px;}
.segment-legend span {display:inline-flex; align-items:center; gap:8px; font-size:.92rem;}
.segment-legend i {width:12px; height:12px; border-radius:50%; background:var(--segment);}
</style>
""", unsafe_allow_html=True)
st.sidebar.markdown(
    '<div class="segmint-brand"><span class="segmint-mark" aria-hidden="true">'
    '<i></i><i></i><i></i></span>Segmint</div>',
    unsafe_allow_html=True,
)
source = st.sidebar.radio("**Data source**", ["Sample dataset", "Upload file"], key="source")
upload = st.sidebar.file_uploader(
    "Upload invoice history", type=["csv", "xlsx", "xls"], label_visibility="collapsed",
    on_change=lambda: st.session_state.update(source="Upload file"),
)
subtitle = "Dec 2010 to Dec 2011 · Online Retail sample"

if source == "Sample dataset":
    profiles = pd.read_csv(ROOT / "sample_profiles.csv")
else:
    st.sidebar.caption("Use approximately 12 months of invoice history.")
    if upload is None:
        st.title("Customer segments")
        st.info("Upload a CSV or Excel workbook with CustomerID, InvoiceNo, Quantity and UnitPrice.")
        st.stop()
    try:
        dtype = {"CustomerID": "string", "InvoiceNo": "string"}
        data = pd.read_csv(upload, dtype=dtype) if upload.name.lower().endswith(".csv") else pd.read_excel(upload, dtype=dtype)
        missing = set(REQUIRED) - set(data.columns)
        if missing:
            raise ValueError("Missing columns: " + ", ".join(sorted(missing)))
        original_rows = len(data)
        data = data.drop_duplicates().copy()
        for column in ["Quantity", "UnitPrice"]:
            data[column] = pd.to_numeric(data[column], errors="coerce").replace([np.inf, -np.inf], np.nan)
        for column in ["CustomerID", "InvoiceNo"]:
            data[column] = data[column].str.strip().replace("", pd.NA)
        data = data.dropna(subset=REQUIRED).copy()
        data["Spend"] = data.Quantity * data.UnitPrice
        data = data[np.isfinite(data.Spend)]
        profiles = data.groupby("CustomerID", as_index=False).agg(Spend=("Spend", "sum"), Invoices=("InvoiceNo", "nunique"))
        profiles = profiles[(profiles.Spend > 0) & np.isfinite(profiles.Spend)].copy()
        if profiles.empty:
            raise ValueError("No customers with positive net sales remain after cleaning.")
        model = json.loads((ROOT / "model.json").read_text())
        scaled = (profiles[["Spend", "Invoices"]].to_numpy() - model["mean"]) / model["scale"]
        distances = np.linalg.norm(scaled[:, None] - model["centers"], axis=2)
        profiles["Segment"] = np.asarray(SEGMENTS)[distances.argmin(axis=1)]
        subtitle = f"Uploaded batch · {len(data):,} invoice lines used"
        st.sidebar.caption(f"{original_rows - len(data):,} duplicate or incomplete lines excluded.")
    except (ValueError, OSError, ImportError, KeyError) as error:
        st.error(f"Unable to analyse this file. {error}")
        st.stop()

st.title("Customer segments")
st.caption(f"{len(profiles):,} customers · {subtitle}")
total_sales = profiles.Spend.sum()
counts = profiles.Segment.value_counts()
for column, segment, color in zip(st.columns(3), SEGMENTS, COLORS):
    group = profiles[profiles.Segment == segment]
    with column:
        st.markdown(
            f'<div class="segment-card" style="--segment:{color};--tint:{color}18">'
            f'<strong>{segment}</strong>{len(group):,} customers<br>'
            f'{group.Spend.sum()/total_sales:.1%} of net sales</div>',
            unsafe_allow_html=True,
        )

st.write("")
plot, campaign = st.columns([2, 1])
with plot:
    with st.container(border=True):
        st.subheader("Spend and invoice frequency")
        minimum = 100 if profiles.Spend.max() >= 100 else profiles.Spend.min()
        visible = profiles[profiles.Spend >= minimum]
        x_step = max(50, 50 * math.ceil(profiles.Invoices.max() / 300))
        x_max = x_step * math.ceil(profiles.Invoices.max() / x_step)
        low = math.floor(math.log10(minimum))
        high = max(low + 1, math.ceil(math.log10(profiles.Spend.max())))
        y_ticks = [10.0**power for power in range(low, high + 1, max(1, math.ceil((high - low) / 8)))]
        chart = alt.Chart(visible).mark_circle(size=40, opacity=0.65, clip=True).encode(
            x=alt.X("Invoices:Q", title="Invoice count", scale=alt.Scale(domain=[0, x_max], nice=False),
                    axis=alt.Axis(values=list(range(0, x_max + 1, x_step)), format="d")),
            y=alt.Y("Spend:Q", title="Net sales (log scale)",
                    scale=alt.Scale(type="log", domain=[10.0**low, 10.0**high], nice=False),
                    axis=alt.Axis(values=y_ticks, format="~s")),
            color=alt.Color("Segment:N", scale=alt.Scale(domain=SEGMENTS, range=COLORS), legend=None),
            tooltip=["Segment:N", "Invoices:Q", alt.Tooltip("Spend:Q", format=",.2f")],
        ).properties(height=380).interactive()
        with alt.data_transformers.enable("default", max_rows=None):
            st.altair_chart(chart, use_container_width=True)
        legend = "".join(
            f'<span style="--segment:{color}"><i aria-hidden="true"></i>{segment} ({counts.get(segment, 0):,})</span>'
            for segment, color in zip(SEGMENTS, COLORS)
        )
        st.markdown(f'<div class="segment-legend">{legend}</div>', unsafe_allow_html=True)
with campaign:
    with st.container(border=True):
        st.subheader("Campaign audience")
        target = st.selectbox("Segment", SEGMENTS, index=1)
        audience = profiles[profiles.Segment == target].sort_values("Spend", ascending=False)
        campaign_type = {"Lower spend": "Re-engagement", "Moderate spend": "Cross-selling", "High value": "Retention"}
        st.write(f"{len(audience):,} customers · {campaign_type[target]}")
        export = audience.copy()
        export["CustomerID"] = export.CustomerID.astype(str).str.replace(r"^([=+@\-\t\r])", r"'\1", regex=True)
        st.download_button("Download audience CSV", export.to_csv(index=False), "segmint-audience.csv", "text/csv", disabled=audience.empty, type="primary")
        st.dataframe(audience.head(8), hide_index=True)
