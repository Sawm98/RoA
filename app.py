
import streamlit as st
import pandas as pd


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Reign of Atlas",
    page_icon="🏛️",
    layout="wide"
)


# --------------------------------------------------
# DESIGN
# --------------------------------------------------

st.markdown("""
<style>

/* Main background */
.stApp {
    background-color: #EEEEEE;
    color: #252525;
}

/* Main content */
.block-container {
    padding-top: 2rem;
}

/* Headings */
h1, h2, h3 {
    color: #9C7938 !important;
    font-family: Georgia, serif;
}

/* Metrics */
[data-testid="stMetric"] {
    background-color: #FFFFFF;
    border: 1px solid #DADADA;
    padding: 20px;
    border-radius: 8px;
}

/* Metric values */
[data-testid="stMetricValue"] {
    color: #9C7938;
}

/* Metric labels */
[data-testid="stMetricLabel"] {
    color: #666666;
}

/* Dividers */
hr {
    border-color: #D5D5D5;
}

/* Dataframes */
[data-testid="stDataFrame"] {
    background-color: #FFFFFF;
    border-radius: 8px;
}

/* Input fields */
.stTextInput input,
.stSelectbox div[data-baseweb="select"] {
    background-color: #FFFFFF;
    color: #252525;
}

/* Captions */
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

/* Sidebar navigation */
[data-testid="stSidebar"] .stRadio label {
    font-size: 16px;
}

/* Selected navigation item */
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

        st.write(
            "Please enter the alliance access password."
        )

        st.text_input(
            "Password",
            type="password",
            on_change=password_entered,
            key="password"
        )

        return False

    elif not st.session_state["password_correct"]:

        st.title("🔐 RoA Command Centre")

        st.write(
            "Incorrect password. Please try again."
        )

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

@st.cache_data(ttl=300)
def load_data():

    # ----------------------------------------------
    # LOAD ALLIANCE ROSTER
    # ----------------------------------------------

    alliance = pd.read_csv(
        "data/alliance2.csv",
        keep_default_na=False
    )

    # ----------------------------------------------
    # LOAD PLAYER COORDINATES
    # ----------------------------------------------

    centers = pd.read_csv(
        "data/player_centers.csv",
        keep_default_na=False
    )

    # ----------------------------------------------
    # LOAD LATEST ARMY SCORES
    # ----------------------------------------------

    army_scores = pd.read_csv(
        "data/latest_army_scores.csv"
    )

    # ----------------------------------------------
    # CLEAN COLUMN NAMES
    # ----------------------------------------------

    for table in [alliance, centers, army_scores]:

        table.columns = (
            table.columns
            .str.strip()
            .str.replace("\ufeff", "", regex=False)
        )

    # ----------------------------------------------
    # CLEAN PLAYER NAMES
    # ----------------------------------------------

    alliance["playerName"] = (
        alliance["playerName"]
        .astype(str)
        .str.strip()
    )

    centers["playerName"] = (
        centers["playerName"]
        .astype(str)
        .str.strip()
    )

    army_scores["playerName"] = (
        army_scores["playerName"]
        .astype(str)
        .str.strip()
    )

    # Remove empty player names
    alliance = alliance[
        alliance["playerName"] != ""
    ].copy()

    centers = centers[
        centers["playerName"] != ""
    ].copy()

    army_scores = army_scores[
        army_scores["playerName"] != ""
    ].copy()

    # ----------------------------------------------
    # CLEAN CLUSTERS
    # ----------------------------------------------

    alliance["cluster"] = (
        alliance["cluster"]
        .astype(str)
        .str.strip()
    )

    # ----------------------------------------------
    # CONVERT NUMERIC COLUMNS
    # ----------------------------------------------

    army_scores["army_score"] = pd.to_numeric(
        army_scores["army_score"],
        errors="coerce"
    )

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

    # ----------------------------------------------
    # REMOVE DUPLICATE PLAYER RECORDS
    # ----------------------------------------------

    centers = centers.drop_duplicates(
        subset=["playerName"]
    )

    army_scores = army_scores.drop_duplicates(
        subset=["playerName"],
        keep="last"
    )

    # ----------------------------------------------
    # MERGE PLAYER COORDINATES
    # ----------------------------------------------

    df = alliance.merge(
        centers,
        on="playerName",
        how="left",
        validate="many_to_one"
    )

    # ----------------------------------------------
    # MERGE LATEST ARMY SCORES
    # ----------------------------------------------

    df = df.drop(
        columns=["army_score"],
        errors="ignore"
    )

    df = df.merge(
        army_scores[
            ["playerName", "army_score"]
        ],
        on="playerName",
        how="left",
        validate="many_to_one"
    )

    return df


df = load_data()


# --------------------------------------------------
# SIDEBAR NAVIGATION
# --------------------------------------------------

st.sidebar.title("🏛️ RoA")

st.sidebar.caption(
    "Page"
)

st.sidebar.divider()

page = st.sidebar.radio(
    "Navigation",
    [
        "🏠 Dashboard",
        "⚔️ Clusters",
        "👥 Players"
    ],
    label_visibility="collapsed"
)

st.sidebar.divider()

st.sidebar.caption(
    "Alliance intelligence • Strategic overview"
)


# --------------------------------------------------
# MAIN HEADER
# --------------------------------------------------

st.title("🏛️ Reign of Atlas")

st.caption(
    "Alliance intelligence • Player organisation • Strategic overview"
)

st.divider()


# ==================================================
# DASHBOARD
# ==================================================

if page == "🏠 Dashboard":

    st.header("Alliance Overview")

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
    # ARMY SCORE STATUS
    # ----------------------------------------------

    st.subheader("Military Intelligence")

    players_with_scores = df["army_score"].notna().sum()

    total_army = df["army_score"].sum()

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Players with army scores",
        f"{players_with_scores}/{total_players}"
    )

    col2.metric(
        "Total alliance army score",
        f"{int(total_army):,}"
    )

    col3.metric(
        "Players missing scores",
        total_players - players_with_scores
    )

    st.divider()

    st.caption(
        "Army scores are automatically updated every midnight. "
        "The website refreshes its data cache every 5 minutes."
    )

    st.caption(
        "Select a section from the sidebar to explore alliance intelligence."
    )


# ==================================================
# CLUSTERS
# ==================================================

elif page == "⚔️ Clusters":

    st.header("⚔️ Cluster Command Centre")

    st.caption(
        "Military strength • Cluster organisation"
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

        # Calculate military statistics
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

        # Count all members in each cluster
        all_members = (
            df.groupby("cluster")["playerName"]
            .nunique()
            .reset_index(name="total_members")
        )

        # Combine statistics
        cluster_stats = military_stats.merge(
            all_members,
            on="cluster",
            how="left"
        )

        cluster_stats = cluster_stats.sort_values(
            "cluster"
        )

        # ------------------------------------------
        # TOTAL ARMY STRENGTH
        # ------------------------------------------

        st.subheader("Total Army Strength")

        total_chart = cluster_stats.set_index(
            "cluster"
        )[["total_army"]]

        st.bar_chart(total_chart)

        # ------------------------------------------
        # AVERAGE ARMY STRENGTH
        # ------------------------------------------

        st.subheader("Average Army Strength")

        average_chart = cluster_stats.set_index(
            "cluster"
        )[["average_army"]]

        st.bar_chart(average_chart)

        # ------------------------------------------
        # MILITARY OVERVIEW TABLE
        # ------------------------------------------

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
            "Check latest_army_scores.csv."
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


# ==================================================
# PLAYERS
# ==================================================

elif page == "👥 Players":

    st.header("👥 Player Intelligence Centre")

    st.caption(
        "Player search • Individual intelligence • Cluster membership"
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

            st.caption(
                f"{search_results['playerName'].nunique()} players found"
            )

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

    st.header("Individual Player Intelligence")

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

        # Cluster
        col1.metric(
            "Cluster",
            player["cluster"]
        )

        # Cities
        city_count = player["city_count"]

        col2.metric(
            "Cities",
            int(city_count)
            if pd.notna(city_count)
            else "Unknown"
        )

        # Army score
        army_score = player["army_score"]

        col3.metric(
            "Army Score",
            f"{int(army_score):,}"
            if pd.notna(army_score)
            else "Unknown"
        )

        # Coordinates
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
        "Filter players by cluster",
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
