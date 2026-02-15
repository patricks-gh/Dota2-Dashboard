import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(page_title="Dota 2 Insights Dashboard", layout="wide")
st.title("Dota 2 Insights Dashboard")

# Only show the "Hero Pick vs Win Rate" tab
tab1 = st.tabs([ "Hero Pick vs Win Rate" ])[0]

# --- TAB 1: Hero Pick vs Win Rate ---
with tab1:
    st.subheader("Hero Pick Rate vs Win Rate")
    
    st.info(
        "Why it matters: Pro players set the meta. Heroes with high pick and win rates are proven strong choices, "
        "and knowing them can guide your hero selection in RANKED games."
    )

    @st.cache_data(ttl=3600)
    def fetch_hero_stats():
        url = "https://api.opendota.com/api/heroStats"
        data = requests.get(url).json()
        df = pd.DataFrame(data)
        
        # Pro pick/win rate
        df['pick_rate'] = df['pro_pick'] / df['pro_pick'].sum()
        df['win_rate'] = df['pro_win'] / df['pro_pick']
        df['pick_rate_pct'] = df['pick_rate'] * 100
        df['win_rate_pct'] = df['win_rate'] * 100

        # Hero icon URLs
        df['img_url'] = df['name'].apply(
            lambda x: f"https://cdn.cloudflare.steamstatic.com/apps/dota2/images/heroes/{x.split('npc_dota_hero_')[1]}_full.png"
        )
        return df

    df = fetch_hero_stats()

    total_pro_games = df['pro_pick'].sum()

    # Dynamic x-axis max
    x_max = df['pick_rate_pct'].max() * 1.05

    fig = go.Figure()

    # Invisible markers for hover
    fig.add_trace(go.Scatter(
        x=df['pick_rate_pct'],
        y=df['win_rate_pct'],
        mode="markers+text",
        marker=dict(size=20, color='rgba(0,0,0,0)'),
        text=df['localized_name'],
        textposition="top center",
        hovertext=df.apply(
            lambda row: f"{row['localized_name']}<br>Pick Rate: {row['pick_rate_pct']:.1f}%<br>Win Rate: {row['win_rate_pct']:.1f}%",
            axis=1
        ),
        hoverinfo="text"
    ))

    # Overlay hero icons with proper sizing
    icon_size_pct = 0.05  # relative fraction of x-axis range
    x_range = df['pick_rate_pct'].max() * 1.05
    y_range = df['win_rate_pct'].max() * 1.05

    for _, row in df.iterrows():
        fig.add_layout_image(
            dict(
                source=row['img_url'],
                x=row['pick_rate_pct'],
                y=row['win_rate_pct'],
                xref="x",
                yref="y",
                xanchor="center",
                yanchor="middle",
                sizex=icon_size_pct * x_range,
                sizey=icon_size_pct * y_range,
                sizing="contain",
                layer="above"
            )
        )

    fig.update_xaxes(range=[0, x_range])
    fig.update_yaxes(range=[0, y_range])
    
    fig.update_layout(
        xaxis_title="Pro Pick Rate (%)",
        yaxis_title="Pro Win Rate (%)",
        xaxis=dict(range=[0, x_max], gridcolor="gray"),
        yaxis=dict(gridcolor="gray"),
        width=1000,
        height=700,
        paper_bgcolor="#1e1e1e",
        plot_bgcolor="#1e1e1e",
        font=dict(color="white")
    )

    fig.add_annotation(
        x=0.95 * x_max,
        y=1 * y_range,
        text=f"Total Pro Games: {total_pro_games:,}",
        showarrow=False,
        font=dict(size=14, color="yellow"),
        align="right",
        bgcolor="rgba(0,0,0,0.5)",
        bordercolor="white",
        borderwidth=1
    )    

    # --- Display Date Range Above the Graph ---
    today = datetime.today()
    last_week = today - timedelta(weeks=1)
    st.markdown(f"**Data Range: {last_week.strftime('%b %d, %Y')} to {today.strftime('%b %d, %Y')}**")
    
    st.plotly_chart(fig, use_container_width=True)

    # --- Compute Weighted Stats --- 
    df['win_pick_ratio'] = df['win_rate_pct'] / df['pick_rate_pct']

    # --- Get Top & Bottom Heroes by Pick Rate and Win Rate --- 
    top3_pick = df.nlargest(3, 'pick_rate_pct') 

    # Sorting bottom heroes
    bottom3_pick = df.sort_values(by=['win_rate_pct', 'pick_rate_pct'], ascending=[True, True]).head(3)

    # --- Hero Stats Showcase ---
    st.markdown("---")
    st.subheader("Dota 2 Hero Stats Showcase")

    # Create 3 horizontal panels: Top, Bottom, Insights
    col1, col2, col3 = st.columns([1, 1, 1])

    # --- Top Heroes Panel ---
    with col1:
        st.markdown("### Top Heroes")
        for hero in top3_pick.itertuples():
            st.image(hero.img_url, width=100)
            st.markdown(f"**{hero.localized_name}**")
            st.markdown(f"Pick Rate: {hero.pick_rate_pct:.1f}% | Win Rate: {hero.win_rate_pct:.1f}%")
            st.markdown("---")

    # --- Bottom Heroes Panel ---
    with col2:
        st.markdown("### Bottom Heroes")
        for hero in bottom3_pick.itertuples():
            st.image(hero.img_url, width=100)
            st.markdown(f"**{hero.localized_name}**")
            st.markdown(f"Pick Rate: {hero.pick_rate_pct:.1f}% | Win Rate: {hero.win_rate_pct:.1f}%")
            st.markdown("---")
    

    # --- Top Pick Logic --- 
    top_pick_hero = df.nlargest(1, 'pick_rate_pct').iloc[0]
    top_pick_rate_percentage = top_pick_hero['pick_rate_pct']
    top_pick_rate_games = (top_pick_rate_percentage / 100) * total_pro_games

    # --- Get top 2-10 most picked heroes ---
    top_2_to_10_pick = df.nlargest(10, 'pick_rate_pct').iloc[1:10]
    top_2_to_10_list = top_2_to_10_pick[['localized_name', 'img_url']].reset_index(drop=True)

    # --- Insights Panel ---
    with col3:
        st.markdown("### Insights")
        st.markdown(f"""
        - **Top Pick Rate Hero:** {top_pick_hero.localized_name} ({top_pick_rate_percentage:.1f}% of pro games, ~{top_pick_rate_games:,.0f} games)
        - **High Ratio Heroes:** Picked efficiently, winning more than expected
        - **Low Ratio Heroes:** Either over-picked or underperforming
        - **Strategic Recommendation:** Choosing heroes with a high win-to-pick ratio is a proven way to follow the meta.
        
        ### Top 2-10 Picked Heroes for Ranked Play:
        """)

        # Create horizontal row for heroes 2-10
        cols = st.columns(9) 
        for idx, (col, hero) in enumerate(zip(cols, top_2_to_10_list.itertuples()), 2):
            with col:
                st.image(hero.img_url, width=50)
                st.markdown(f"**{hero.localized_name}**")
        
        # --- Add Hero Guides Section ---
        st.markdown("### Hero Guides")
        st.markdown("Reference sites for detailed guides and strategies:")

        st.markdown(
            """
            - [Dota 2 Wiki](https://dota2.fandom.com/wiki/Dota_2_Wiki)  
            - [Dotabuff](https://www.dotabuff.com/heroes)  
            - [Liquipedia](https://liquipedia.net/dota2/Main_Page)  
            - [Gamepedia](https://dota2.gamepedia.com/Dota_2_Wiki)  
            - [ProGuides](https://www.proguides.com/dota-2)  
            """
        )

# --- Data Source & Description ---
st.markdown(
    """
    **Data Source**: [OpenDota API](https://www.opendota.com/)  
    This data is sourced from the OpenDota API, which provides comprehensive statistics on Dota 2 matches, including hero performance metrics, pick rates, and win rates. Data is refreshed periodically.
    """
)