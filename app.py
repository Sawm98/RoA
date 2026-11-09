
import streamlit as st
import pandas as pd


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="RoA Command Centre",
    page_icon="🏛️",
    layout="wide"
)


# --------------------------------------------------
# DESIGN
# --------------------------------------------------

st.markdown("""
<style>

.stApp {
    background-color: #EEEEEE;
    color: #252525;
}

.block-container {
    padding-top: 2rem;
}

h1, h2, h3 {
    color: #9C7938 !important;
    font-family: Georgia, serif;
}

[data-testid="stMetric"] {
    background-color: #FFFFFF;
    border: 1px solid #DADADA;
    padding: 20px;
    border-radius: 8px;
}

[data-testid="stMetricValue"] {
    color: #9C7938;
}

[data-testid="stMetricLabel"] {
    color: #666666;
}

hr {
    border-color: #D5D5D5;
}

[data-testid="stDataFrame"] {
    background-color: #FFFFFF;
    border-radius: 8px;
}

.stTextInput input,
.stSelectbox div[data-baseweb="select"] {
    background-color: #FFFFFF;
    color: #252525;
}

.stCaption {
    color: #777777;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #E5E5E5;
    border-right: 1px solid #D5D5D5;
}

/* Sidebar text */
[data-testid="stSidebar"] * {
    color: #252525;
}

/* Radio navigation */
[data-testid="stSidebar"] .stRadio label {
    font-size: 16px;
}

/* Gold radio selection */
[data-testid="stSidebar"] [aria-checked="true"] {
    color: #9C7938;
}

</style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# PASSWORD PROTECTION
# --------------------------------------------------

def check_password():

    def password_entered():

        if st.session_state["password"] == st.secrets["APP_PASSWORD"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]

        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:

        st.title("🔐 RoA Command Centre")
        st.write("Please enter the alliance access password.")

        st.text_input(
            "Password",
            type="password",
            on_change=password_entered,
            key="password"
        )

        return False

    elif not st.session_state["password_correct"]:

        st.title("🔐 RoA Command Centre")
        st.write("Incorrect password. Please try again.")

        st.text_input(
            "Password",
            type="password",
            on_change=password_entered,
            key="password"
        )

        return False

    return True


if not check_password():
    st.stop()


# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

@st.cache_data
def load_data():

    alliance = pd.read_csv(
        "data/alliance2.csv",
        keep_default_na=False
    )

    centers = pd.read_csv(
        "data/player_centers.csv",
        keep_default_na=False
    )

    # Clean column names
    alliance.columns = (
        alliance.columns
        .str.strip()
        .str.replace("\ufeff", "", regex=False)
    )

    centers.columns = (
        centers.columns
        .str.strip()
        .str.replace("\ufeff", "", regex=False)
    )

    # Clean player names
    alliance["playerName"] = (
        alliance["playerName"].astype(str).str.strip()
    )

    centers["playerName"] = (
        centers["playerName"].astype(str).str.strip()
    )

    # Remove empty player names
    alliance = alliance[
        alliance["playerName"] != ""
    ].copy()

    centers = centers[
        centers["playerName"] != ""
    ].copy()

    # Clean cluster values
    alliance["cluster"] = (
        alliance["cluster"].astype(str).str.strip()
    )

    # Convert army score
    alliance["army_score"] = pd.to_numeric(
        alliance["army_score"],
        errors="coerce"
    )

    # Convert coordinates and city count
    centers["x"] = pd.to_numeric(
        centers["x"],
        errors="coerce"
    )

    centers["y"] = pd.to_numeric(
        centers["y"],
        errors="coerce"
    )

    centers["city_count"] = pd.to_numeric(
        centers["city_count"],
        errors="coerce"
    )

    # One coordinate record per player
    centers = centers.drop_duplicates(
        subset=["playerName"]
    )

    # Merge data
    df = alliance.merge(
        centers,
        on="playerName",
        how="left",
        validate="many_to_one"
    )

    return df


df = load_data()


# --------------------------------------------------
# SIDEBAR MENU
# --------------------------------------------------

st.sidebar.title("🏛️ RoA")
st.sidebar.caption("COMMAND CENTRE")

st.sidebar.divider()

page = st.sidebar.radio(
    "Navigation",
    [
        "🏠 Dashboard",
        "⚔️ Clusters"
    ],
    label_visibility="collapsed"
)

st.sidebar.divider()

st.sidebar.caption(
    "Alliance intelligence • Strategic overview"
)


# --------------------------------------------------
# HEADER
# --------------------------------------------------

st.title("🏛️ RoA Command Centre")

st.caption(
    "Alliance intelligence • Player organisation • Strategic overview"
)

st.divider()


# ==================================================
# DASHBOARD PAGE
# ==================================================

if page == "🏠 Dashboard":

    # ----------------------------------------------
    # OVERVIEW STATISTICS
    # ----------------------------------------------

    total_players = df["playerName"].nunique()

    total_clusters = df["cluster"].nunique()

    total_cities = int(
        df["city_count"].sum(skipna=True)
    )

    players_with_coordinates = (
        df["x"].notna() & df["y"].notna()
    ).sum()

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Alliance members",
        total_players
    )

    col2.metric(
        "Clusters",
        total_clusters
    )

    col3.metric(
        "Total cities",
        total_cities
    )

    col4.metric(
        "Players with coordinates",
        players_with_coordinates
    )

    st.divider()

    # ----------------------------------------------
    # PLAYER SEARCH
    # ----------------------------------------------

    st.header("Player Search")

    search = st.text_input(
        "Search for a player",
        placeholder="Enter player name..."
    )

    if search:

        search_results = df[
            df["playerName"].str.contains(
                search,
                case=False,
                na=False
            )
        ]

        if not search_results.empty:

            st.dataframe(
                search_results[
                    [
                        "playerName",
                        "cluster",
                        "army_score",
                        "x",
                        "y",
                        "city_count"
                    ]
                ].rename(columns={
                    "playerName": "Player",
                    "cluster": "Cluster",
                    "army_score": "Army Score",
                    "x": "X",
                    "y": "Y",
                    "city_count": "Cities"
                }),
                use_container_width=True,
                hide_index=True
            )

        else:

            st.warning("No player found.")

    st.divider()

    # ----------------------------------------------
    # PLAYER INTELLIGENCE
    # ----------------------------------------------

    st.header("Player Intelligence")

    player_options = sorted(
        df["playerName"].unique().tolist()
    )

    if player_options:

        selected_player = st.selectbox(
            "Select a player",
            player_options
        )

        player = df[
            df["playerName"] == selected_player
        ].iloc[0]

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Cluster",
            player["cluster"]
        )

        city_count = player["city_count"]

        col2.metric(
            "Cities",
            int(city_count)
            if pd.notna(city_count)
            else "Unknown"
        )

        army_score = player["army_score"]

        col3.metric(
            "Army Score",
            f"{int(army_score):,}"
            if pd.notna(army_score)
            else "Unknown"
        )

        coordinates_available = (
            pd.notna(player["x"])
            and pd.notna(player["y"])
        )

        if coordinates_available:

            coordinates = (
                f"{player['x']}, {player['y']}"
            )

        else:

            coordinates = "Unknown"

        col4.metric(
            "Centre Coordinates",
            coordinates
        )

    else:

        st.warning("No players available.")

        
# ==================================================
# CLUSTERS PAGE
# ==================================================

elif page == "⚔️ Clusters":

    st.header("⚔️ Cluster Command Centre")

    st.caption(
        "Military strength • Cluster organisation • Member intelligence"
    )

    st.divider()

    # ----------------------------------------------
    # CLUSTER MILITARY STATISTICS
    # ----------------------------------------------

    st.header("Cluster Military Strength")

    military_df = df.dropna(
        subset=["army_score"]
    ).copy()

    if not military_df.empty:

        military_stats = (
            military_df
            .groupby("cluster")
            .agg(
                total_army=("army_score", "sum"),
                average_army=("army_score", "mean"),
                players_with_score=("playerName", "nunique")
            )
            .reset_index()
        )

        all_members = (
            df.groupby("cluster")["playerName"]
            .nunique()
            .reset_index(name="total_members")
        )

        cluster_stats = military_stats.merge(
            all_members,
            on="cluster",
            how="left"
        )

        cluster_stats = cluster_stats.sort_values(
            "cluster"
        )

        # Total army
        st.subheader("Total Army Strength")

        total_chart = cluster_stats.set_index(
            "cluster"
        )[["total_army"]]

        st.bar_chart(total_chart)

        # Average army
        st.subheader("Average Army Strength")

        average_chart = cluster_stats.set_index(
            "cluster"
        )[["average_army"]]

        st.bar_chart(average_chart)

        # Military overview table
        st.subheader("Cluster Military Overview")

        display_stats = cluster_stats.copy()

        display_stats["total_army"] = (
            display_stats["total_army"]
            .round(0)
            .astype(int)
        )

        display_stats["average_army"] = (
            display_stats["average_army"]
            .round(0)
            .astype(int)
        )

        display_stats.columns = [
            "Cluster",
            "Total Army",
            "Average Army",
            "Players With Score",
            "Total Members"
        ]

        st.dataframe(
            display_stats,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.warning(
            "No army score data is currently available. "
            "Check alliance2.csv."
        )

    st.divider()

    # ----------------------------------------------
    # CLUSTER OVERVIEW
    # ----------------------------------------------

    st.header("Cluster Overview")

    cluster_summary = (
        df.groupby("cluster")
        .agg(
            Members=("playerName", "nunique"),
            Cities=("city_count", "sum")
        )
        .reset_index()
        .sort_values("cluster")
    )

    cluster_summary.columns = [
        "Cluster",
        "Members",
        "Cities"
    ]

    st.dataframe(
        cluster_summary,
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    # ----------------------------------------------
    # CLUSTER MEMBERS
    # ----------------------------------------------

    st.header("Cluster Members")

    available_clusters = sorted(
        df["cluster"].unique().tolist()
    )

    cluster_options = (
        ["All clusters"] + available_clusters
    )

    selected_cluster = st.selectbox(
        "Select a cluster",
        cluster_options
    )

    if selected_cluster == "All clusters":

        cluster_df = df.copy()

    else:

        cluster_df = df[
            df["cluster"] == selected_cluster
        ].copy()

    cluster_df = cluster_df.sort_values(
        "playerName"
    )

    st.caption(
        f"{cluster_df['playerName'].nunique()} members"
    )

    st.dataframe(
        cluster_df[
            [
                "playerName",
                "cluster",
                "army_score",
                "x",
                "y",
                "city_count"
            ]
        ].rename(columns={
            "playerName": "Player",
            "cluster": "Cluster",
            "army_score": "Army Score",
            "x": "X",
            "y": "Y",
            "city_count": "Cities"
        }),
        use_container_width=True,
        hide_index=True
    )


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()

st.caption(
    "RoA Command Centre • Data maintained by the alliance"
)
