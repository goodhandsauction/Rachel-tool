import os
import pandas as pd
import streamlit as st

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PBS Drug Search – FSH Rehab",
    page_icon="💊",
    layout="wide",
)

# ── Password protection ───────────────────────────────────────────────────────
APP_PASSWORD = os.environ.get("APP_PASSWORD", "fshrehab")

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("PBS Drug Search – FSH Rehab")
    st.caption("⚕️ **Clinical tool for FSH Rehab pharmacists. Verify with MIMS/AMH.**")
    pwd = st.text_input("Enter password to continue", type="password")
    if st.button("Login"):
        if pwd == APP_PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect password.")
    st.stop()

# ── Load data ─────────────────────────────────────────────────────────────────
DATA_PATH = os.path.join(os.path.dirname(__file__), "pbs_search_data.csv")

@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str).fillna("")
    # Normalise text for case-insensitive search
    df["_generic_lower"] = df["generic_name"].str.lower()
    df["_brand_lower"]   = df["brand_name"].str.lower()
    df["_atc_lower"]     = df["atc_description"].str.lower()
    return df

df = load_data(DATA_PATH)

# ── Header ────────────────────────────────────────────────────────────────────
st.title("PBS Drug Search")
st.caption(
    "⚕️ **Clinical tool for FSH Rehab pharmacists. Verify with MIMS/AMH.**"
)
st.divider()

# ── Search bar ────────────────────────────────────────────────────────────────
col_search, col_route, col_prog = st.columns([3, 1, 1])

with col_search:
    query = st.text_input(
        "Search by generic name, brand name, or drug class",
        placeholder="e.g. metformin, Glucophage, biguanide…",
    )

with col_route:
    routes = ["All routes"] + sorted(df["route"].unique().tolist())
    route_filter = st.selectbox("Route", routes)

with col_prog:
    programs = ["All programs"] + sorted(df["program"].unique().tolist())
    prog_filter = st.selectbox("Program", programs)

# ── Filter logic ──────────────────────────────────────────────────────────────
results = df.copy()

if query.strip():
    q = query.strip().lower()
    mask = (
        results["_generic_lower"].str.contains(q, regex=False)
        | results["_brand_lower"].str.contains(q, regex=False)
        | results["_atc_lower"].str.contains(q, regex=False)
        | results["pbs_code"].str.lower().str.contains(q, regex=False)
    )
    results = results[mask]

if route_filter != "All routes":
    results = results[results["route"] == route_filter]

if prog_filter != "All programs":
    results = results[results["program"] == prog_filter]

# ── Results ───────────────────────────────────────────────────────────────────
st.markdown(f"**{len(results):,} result(s)**")

display_cols = {
    "pbs_code":       "PBS Code",
    "generic_name":   "Generic Name",
    "brand_name":     "Brand Name",
    "formulation":    "Formulation",
    "route":          "Route",
    "pack_size":      "Pack Size",
    "program":        "Program",
    "atc_code":       "ATC Code",
    "atc_description":"ATC Description",
}

if results.empty:
    st.info("No results found. Try a different search term.")
else:
    show = results[list(display_cols.keys())].rename(columns=display_cols)
    st.dataframe(
        show,
        use_container_width=True,
        hide_index=True,
        height=min(600, 50 + 35 * len(show)),
    )

    # ── Detail expander ───────────────────────────────────────────────────────
    with st.expander("Show schedule form (full label text)"):
        detail = results[["pbs_code", "generic_name", "brand_name", "schedule_form"]].rename(
            columns={
                "pbs_code":      "PBS Code",
                "generic_name":  "Generic Name",
                "brand_name":    "Brand Name",
                "schedule_form": "Schedule Form",
            }
        )
        st.dataframe(detail, use_container_width=True, hide_index=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.caption(
    f"Data source: PBS API export (2026-05-01) · {len(df):,} PBS items loaded · "
    "**Clinical tool for FSH Rehab pharmacists. Verify with MIMS/AMH.**"
)
