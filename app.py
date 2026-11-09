
import streamlit as st
import pandas as pd
import pydeck as pdk
# ==================================================
# PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="RoA Command Centre",
    page_icon="🏛️",
    layout="wide"
)

# ==================================================
# CUSTOM DESIGN
# ==================================================

st.markdown("""
<style>

.stApp {
    background-color: #101318;
    color: #e8e3d5;
}

h1, h2, h3 {
    color: #d6b56d !important;
    font-family: Georgia, serif;
}

[data-testid="stMetric"] {
    background-color: #1c222b;
    border: 1px solid #39332a;
    padding: 20px;
    border-radius: 8px;
}

[data-testid="stMetricValue"] {
    color: #d6b56d;
}

[data-testid="stMetricLabel"] {
    color: #b8b8b8;
}

hr {
    border-color: #39332a;
}

</style>
""", unsafe_allow_html=True)

# ==================================================
# HEADER
# ==================================================

st.title("🏛️ RoA")
st.subheader("Alliance Command Centre")

st.divider()

# ==================================================
# LOAD AND PROCESS DATA
# ==================================================

@st.cache_data
def load_data():

    # Load cluster assignments
    alliance = pd.read_csv(
        "data/alliance.csv",
        keep_default_na=False
    )

    # Load player coordinates
    centers = pd.read_csv(
        "data/player_centers.csv",
        keep_default_na=False
    )

    # Clean column names
    for frame in [alliance, centers]:
        frame.columns = (
            frame.columns
            .str.strip()
            .str.replace("\ufeff", "", regex=False)
        )

    # Validate required columns
    required_alliance = {"playerName", "cluster"}
    required_centers = {"playerName", "x", "y", "city_count"}

    if not required_alliance.issubset(alliance.columns):
        raise ValueError("alliance.csv must contain playerName and cluster")

    if not required_centers.issubset(centers.columns):
        raise ValueError("player_centers.csv must contain playerName, x, y and city_count")

    # Clean player names
    alliance["playerName"] = alliance["playerName"].astype(str).str.strip()
    centers["playerName"] = centers["playerName"].astype(str).str.strip()

    # Remove genuinely empty rows
    alliance = alliance[
        (alliance["playerName"] != "") &
        (alliance["cluster"].astype(str).str.strip() != "")
    ]

    centers = centers[centers["playerName"] != ""]

    # Convert coordinate data to numbers
    for column in ["x", "y", "city_count"]:
        centers[column] = pd.to_numeric(
            centers[column],
            errors="coerce"
        )

    # Remove duplicate player centers
    centers = centers.drop_duplicates(
        subset=["playerName"]
    )

    # Combine datasets
    df = alliance.merge(
        centers,
        on="playerName",
        how="left",
        validate="many_to_one"
    )

    return df


df = load_data()

# ==================================================
# STATISTICS
# ==================================================

st.subheader("Alliance Statistics")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Players",
    df["playerName"].nunique()
)

col2.metric(
    "Clusters",
    df["cluster"].nunique()
)

col3.metric(
    "Total Cities",
    int(df["city_count"].sum())
)

col4.metric(
    "Players with Coordinates",
    df.loc[df["x"].notna() & df["y"].notna(), "playerName"].nunique()
)

st.divider()

# ==================================================
# CLUSTER OVERVIEW
# ==================================================

st.subheader("Cluster Overview")

cluster_counts = (
    df.groupby("cluster")
    .agg(
        Players=("playerName", "nunique"),
        Cities=("city_count", "sum")
    )
    .reset_index()
    .sort_values("cluster")
)

st.dataframe(
    cluster_counts,
    use_container_width=True,
    hide_index=True
)

# ==================================================
# DATA QUALITY
# ==================================================

missing_coordinates = df[
    df["x"].isna() | df["y"].isna()
]["playerName"].nunique()

if missing_coordinates > 0:
    st.warning(
        f"{missing_coordinates} players have no matching coordinates."
    )

st.divider()

# ==================================================
# PLAYER SEARCH
# ==================================================

st.subheader("Player Search")

search = st.text_input(
    "Search player",
    placeholder="Enter player name..."
)

if search:
    results = df[
        df["playerName"].str.contains(
            search,
            case=False,
            na=False
        )
    ]

    st.dataframe(
        results,
        use_container_width=True,
        hide_index=True
    )

# ==================================================
# CLUSTER FILTER
# ==================================================

st.subheader("Cluster Members")

clusters = sorted(df["cluster"].unique())

selected_cluster = st.selectbox(
    "Select cluster",
    ["All clusters"] + list(clusters)
)

if selected_cluster == "All clusters":
    filtered_df = df
else:
    filtered_df = df[
        df["cluster"] == selected_cluster
    ]

st.dataframe(
    filtered_df,
    use_container_width=True,
    hide_index=True
)

# ==================================================
# GEOGRAPHICAL CLUSTER MAP
# ==================================================

st.divider()

st.subheader("🗺️ Alliance Territory Map")

# One marker per player
map_df = df.drop_duplicates(subset=["playerName"]).copy()

# Apply cluster filter to map
if selected_cluster != "All clusters":
    map_df = map_df[
        map_df["cluster"].astype(str) == str(selected_cluster)
    ]

# Remove players without coordinates
map_df = map_df.dropna(subset=["x", "y"])

# Five distinct cluster colours
cluster_colors = {
    "1": [255, 80, 80, 200],
    "2": [60, 140, 255, 200],
    "3": [50, 200, 120, 200],
    "4": [230, 180, 50, 200],
    "5": [180, 90, 230, 200]
}

# Assign colours
map_df["color"] = map_df["cluster"].astype(str).map(
    cluster_colors
)

# Remove any unexpected clusters without assigned colours
map_df = map_df.dropna(subset=["color"])

if not map_df.empty:

    # Calculate map centre
    center_x = map_df["x"].mean()
    center_y = map_df["y"].mean()

    # Create player markers
    layer = pdk.Layer(
        "ScatterplotLayer",
        data=map_df,
        get_position=["x", "y"],
        get_fill_color="color",
        get_radius=1,
        radius_min_pixels=5,
        radius_max_pixels=12,
        pickable=True,
        auto_highlight=True
    )

    # Map camera
    view_state = pdk.ViewState(
        target=[center_x, center_y, 0],
        zoom=0
    )

    # Render map
    deck = pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        views=[pdk.View(type="OrbitView", controller=True)],
        tooltip={
            "html": "<b>{playerName}</b><br/>Cluster: {cluster}<br/>Cities: {city_count}",
            "style": {
                "backgroundColor": "#222222",
                "color": "white"
            }
        }
    )

    st.pydeck_chart(
        deck,
        use_container_width=True
    )

else:
    st.warning("No players with valid coordinates found.")

# Cluster legend
st.markdown("**Cluster Legend**")

legend_cols = st.columns(5)

for i, cluster in enumerate(["1", "2", "3", "4", "5"]):
    color = cluster_colors[cluster]
    hex_color = "#{:02x}{:02x}{:02x}".format(*color[:3])

    legend_cols[i].markdown(
        f"<span style='color:{hex_color}'>●</span> Cluster {cluster}",
        unsafe_allow_html=True
    )

# ==================================================
# FOOTER
# ==================================================

st.divider()

st.caption(
    "RoA Command Centre | Alliance Intelligence"
)
