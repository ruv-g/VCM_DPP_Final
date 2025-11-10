import streamlit as st
import json, os, urllib.parse

# --- PAGE SETUP ---
st.set_page_config(
    page_title="Virgin Atlantic — Digital Cabin Passports",
    layout="wide",
    page_icon="✈️"
)

# --- BRANDING ---
VIRGIN_RED = "#D50032"
VIRGIN_PLUM = "#4D0026"

st.markdown(f"""
<div style='display:flex;align-items:center;gap:16px;padding:12px 0'>
  <div style='width:64px;height:64px;background:{VIRGIN_RED};border-radius:8px;display:flex;align-items:center;justify-content:center;color:white;font-weight:bold'>VA</div>
  <div>
    <h1 style='margin:0;color:{VIRGIN_PLUM}'>Virgin Atlantic — Digital Cabin Passports</h1>
    <div style='color:#6b6b6b'>Circular cabin asset passports • Composition • Certifications • Repair history • End-of-life</div>
  </div>
</div>
<hr>
""", unsafe_allow_html=True)

# --- LOAD DATA ---
DATA_FILE = os.path.join(os.path.dirname(__file__), "data", "cabin_materials.json")
with open(DATA_FILE, "r", encoding="utf-8") as f:
    LISTINGS = json.load(f)

# --- SIDEBAR FILTERS ---
with st.sidebar:
    st.header("Filters & Search")
    aircrafts = sorted({l.get("aircraft", "Unknown") for l in LISTINGS})
    types = sorted({l.get("part_type", "Unknown") for l in LISTINGS})
    aircraft_filter = st.selectbox("Aircraft", options=["All"] + aircrafts)
    type_filter = st.selectbox("Part Type", options=["All"] + types)
    status_filter = st.selectbox("Status", options=["All", "available", "reserved", "sold"])
    q = st.text_input("Search by title or ID")

# --- QUERY PARAM (for QR / link) ---
query_params = st.experimental_get_query_params()
selected_id = query_params.get("id", [None])[0] if "id" in query_params else None

# --- QR CODE URL ---
BASE_URL = os.getenv("BASE_URL", "").rstrip("/")
def qr_url(part_id):
    target = f"{BASE_URL}/?id={urllib.parse.quote(part_id)}" if BASE_URL else f"/?id={urllib.parse.quote(part_id)}"
    enc = urllib.parse.quote(target, safe="")
    return f"https://chart.googleapis.com/chart?chs=220x220&cht=qr&chl={enc}&choe=UTF-8"

# --- KPI CARDS ---
col1, col2, col3 = st.columns(3)
col1.metric("Total Materials", len(LISTINGS))
col2.metric("Available", sum(1 for l in LISTINGS if l.get("status", "").lower() == "available"))
col3.metric("Total CO₂ Saved (kg)", f"{sum(int(l.get('co2_saved', 0)) for l in LISTINGS)}")

st.markdown("---")

# --- RENDER FUNCTION ---
def render_passport(item):
    st.markdown(f"## {item['title']} — `{item['id']}`")
    two = st.columns([1, 2])
    with two[0]:
        if item.get("image"):
            st.image(item["image"], use_container_width=True)
        st.write("### Scan to open passport")
        st.image(qr_url(item["id"]), width=180)
    with two[1]:
        st.write(f"**Aircraft:** {item.get('aircraft')}  •  **Part Type:** {item.get('part_type')}  •  **Status:** {item.get('status')}")
        st.write(item.get("description", ""))
        if item.get("fmv"):
            st.markdown(f"**Fair Market Value:** £{item.get('fmv')}")
        st.markdown(f"**Estimated CO₂ saved (kg):** {item.get('co2_saved', 0)}")
        st.markdown("### Composition")
        for k, v in item.get("dpp", {}).get("composition", {}).items():
            st.write(f"- **{k}**: {v}")
        st.markdown("### Certifications")
        for c in item.get("dpp", {}).get("certifications", []):
            st.write(f"- {c}")
        st.markdown("### Repair / Refurbishment History")
        for h in item.get("dpp", {}).get("repair_history", []):
            st.write(f"- {h}")
        st.markdown("### End-of-life Guidance")
        st.write(item.get("dpp", {}).get("end_of_life", ""))
        st.markdown("### Marketplace Link")
        link = f"https://vcm-marketplace.streamlit.app/?id={item['id']}"
        st.markdown(f"[View resale listing →]({link})")

# --- DISPLAY CONTENT ---
if selected_id:
    rec = next((r for r in LISTINGS if r["id"] == selected_id), None)
    if rec:
        render_passport(rec)
    else:
        st.warning(f"No passport found for ID: {selected_id}")
else:
    shown = 0
    for item in LISTINGS:
        if aircraft_filter != "All" and item.get("aircraft") != aircraft_filter:
            continue
        if type_filter != "All" and item.get("part_type") != type_filter:
            continue
        if status_filter != "All" and item.get("status") != status_filter:
            continue
        combined = (item.get("title", "") + " " + item.get("id", "") + " " + item.get("description", "")).lower()
        if q and q.lower() not in combined:
            continue

        c1, c2 = st.columns([1, 3])
        with c1:
            if item.get("image"):
                st.image(item["image"], width=240)
            st.image(qr_url(item["id"]), width=120)
        with c2:
            st.markdown(f"**{item['title']}** — `{item['id']}`")
            st.write(item.get("description", ""))
            st.write(f"**CO₂ saved:** {item.get('co2_saved', 0)} kg  •  **Status:** {item.get('status')}")
            if st.button("View Passport", key=f"view_{item['id']}"):
                st.experimental_set_query_params(id=item["id"])
                st.experimental_rerun()
        shown += 1

    if shown == 0:
        st.info("No items matched your filters.")

st.markdown("---")
st.caption("Virgin Atlantic — Digital Cabin Passports (VCM) Prototype")

