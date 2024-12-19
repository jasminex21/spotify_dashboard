import streamlit as st
import os
from dotenv import load_dotenv
import pandas as pd
from st_aggrid import AgGrid, JsCode, ColumnsAutoSizeMode, AgGridTheme
from st_aggrid.grid_options_builder import GridOptionsBuilder
from datetime import datetime, timedelta
import pytz
from pytz import timezone
import requests
from concurrent.futures import ThreadPoolExecutor
import plotly.graph_objects as go
import plotly.express as px
from wordcloud import WordCloud
import matplotlib.pyplot as plt

### ENV. VARIABLES ###
load_dotenv()

TIMEZONE = pytz.timezone("US/Central")
NOW = datetime.now(TIMEZONE)
MONDAY = (NOW - timedelta(days = NOW.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)

USER_AGENT = os.getenv('LASTFM_USER_AGENT')
API_KEY = os.getenv('LASTFM_API_KEY')
LASTFM_USER = "jasminexx18"

THEME = {"background_color": "#082D1B",
         "button_color": "#0E290E",
         "inputs": "#547054",
         "text_color": "white"}
long_periods = ["Last 7 days", "Last month", "Last 3 months", 
                "Last 6 months", "Last year", "Overall"]
short_periods = ["7day", "1month", "3month", 
                 "6month", "12month", "overall"]
PERIOD_MAPPING = dict(zip(long_periods, short_periods))

### FUNCTIONS ###
def apply_theme(selected_theme):
    css = f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@100..900&family=Poppins:ital,wght@0,100;0,200;0,300;0,400;0,500;0,600;0,700;0,800;0,900;1,100;1,200;1,300;1,400;1,500;1,600;1,700;1,800;1,900&display=swap');

    .stApp > header {{
        background-color: transparent;
    }}
    .stApp {{
        color: {selected_theme["text_color"]};
        font-family: 'Outfit', sans-serif;
    }}
    div[data-baseweb="select"] > div, div[data-baseweb="base-input"] > input, div[data-baseweb="base-input"] > textarea {{
        color: {selected_theme["text_color"]};
        -webkit-text-fill-color: {selected_theme["text_color"]} !important;
        font-weight: 600 !important;
        font-family: 'Outfit', sans-serif;
    }}
    p, ul, li {{
        color: {selected_theme["text_color"]};
        font-weight: 600 !important;
        font-size: large !important;
        font-family: 'Outfit', sans-serif;
    }}
    h3, h2, h1, strong, h4 {{
        color: {selected_theme["text_color"]};
        font-weight: 900 !important;
        font-family: 'Outfit', sans-serif;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

def lastfm_get(payload):
    """Function to streamline API calls"""

    headers = {'user-agent': USER_AGENT}
    url = 'https://ws.audioscrobbler.com/2.0/'

    # Add API key and format to the payload
    payload['api_key'] = API_KEY
    payload['format'] = 'json'

    response = requests.get(url, headers=headers, params=payload)
    
    return response

def process_track(track):

    track_info = {
        "Rank": track["@attr"]["rank"],
        # "track_image": get_track_coverart(track["mbid"]) if track["mbid"] else track["image"][1]["#text"],
        "Track": track["name"],
        "Artist": track["artist"]["name"],
        "Streams": track["playcount"]
        # "Duration": track["duration"]
    }

    return track_info

def extract_track_data(track): 
    """Extracts track data for user.getRecentTracks"""

    track_info = {
        "Track": track["name"],
        "Artist": track["artist"]["#text"],
        "Album": track["album"]["#text"],
        "Listened at": track["date"]["#text"]
    }

    return track_info

def get_recently_played(): 
    """Retrieve the last 100 most recently-played tracks"""

    all_tracks = []

    response = lastfm_get({'method': 'user.getRecentTracks', 
                           'user': "jasminexx18",
                           'from': int(MONDAY.timestamp()),
                           'limit': '100', 
                           'page': '1'})
        
    for track in response.json()["recenttracks"]["track"]:
        if "@attr" not in track.keys():
            all_tracks.append(extract_track_data(track))

    return pd.DataFrame(all_tracks)

def get_this_week_tracks():

    all_tracks = []
    i = 1

    initial_response = lastfm_get({'method': 'user.getRecentTracks', 
                                    'user': "jasminexx18",
                                    'from': int(MONDAY.timestamp()),
                                    'limit': '1', 
                                    'page': i})
    total_tracks = int(initial_response.json()["recenttracks"]["@attr"]["total"])

    while len(all_tracks) < total_tracks:
        response = lastfm_get({'method': 'user.getRecentTracks', 
                                'user': "jasminexx18",
                                'from': int(MONDAY.timestamp()),
                                'limit': '200', 
                                'page': i})
        
        for track in response.json()["recenttracks"]["track"]:
            if "@attr" not in track.keys():
                all_tracks.append(extract_track_data(track))
        
        i += 1

    return pd.DataFrame(all_tracks)

def get_track_top_tags(track, artist):

    remove = ["seen live", "love", "favorites", "favorite", 'favorite songs']

    r = lastfm_get({'method': 'track.getTopTags', 
                    'user': "jasminexx18",
                    'artist': artist,
                    'track': track})
    
    tags = r.json()["toptags"]["tag"]
    tags = [tag["name"].lower() for tag in tags] if len(tags) else []
    tags = [tag for tag in tags if tag not in remove]
    
    return tags

# page configurations
st.set_page_config(
    page_title="Spotify Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded")

st.set_option('deprecation.showPyplotGlobalUse', False)

### UI ###
st.title(":bar_chart: Jasmine's *Custom* Streaming Dashboard")

apply_theme(THEME)

(tab_this_week, 
 tab_top_artists, 
 tab_top_tracks,
 tab_recently_played) = st.tabs(["This Week", "Top Artists", "Top Tracks", "Recently Played"])

with tab_this_week: 

    all_tracks = get_this_week_tracks()

    col1, col2 = st.columns([1.5, 1])

    with col1: 
        this_week_tracks = all_tracks.groupby(["Track", "Artist", "Album"])["Track"].count().reset_index(name="Streams").sort_values("Streams", ascending=False)
        this_week_tracks["Rank"] = list(range(1, this_week_tracks.shape[0] + 1))
        this_week_tracks = this_week_tracks[["Rank", "Track", "Artist", "Album", "Streams"]]
        
        st.markdown(f"### Your Top Tracks since {MONDAY.date()}")
        builder = GridOptionsBuilder.from_dataframe(this_week_tracks)
        builder.configure_column("Track",
                                 cellStyle={"fontWeight": "bold"})
                                 #maxWidth=250)  
        # builder.configure_column("Artist",
        #                          maxWidth=200)  
        # builder.configure_column("Album",
        #                          maxWidth=250)  
        # builder.configure_column("Rank",
        #                          maxWidth=100)  
        # builder.configure_column("Streams",
        #                          maxWidth=120)  
        
        builder.configure_grid_options(rowHeight=50, suppressColumnVirtualisation=True) 
        builder.configure_grid_options(onFirstDataRendered="function() { gridOptions.api.sizeColumnsToFit(); }")

        options = builder.build()

        grid = AgGrid(this_week_tracks, 
                        gridOptions=options,
                        columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS,
                        allow_unsafe_jscode=True, 
                        theme=AgGridTheme.ALPINE,
                        height=800)
    
    with col2: 
        st.markdown("#### Artist Representation")
        artist_counts = this_week_tracks.value_counts().reset_index()
        labels = artist_counts["Artist"]
        values = artist_counts["count"]

        fig = go.Figure(data=[go.Pie(labels=labels, 
                                     values=values, 
                                     hole=.3,
                                     marker=dict(colors=px.colors.qualitative.Alphabet),
                                     hovertemplate=('<b>%{label}</b><br>' 
                                                    '# of tracks: %{value}<br>' 
                                                    'Pct.: %{percent:.2%}<br>' 
                                                    '<extra></extra>'))])
        
        #fig.update_layout(title = {"text": "<h4>Artist Representation</h4>"})
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("#### Top Tags")
        top_tags = []

        for i, row in this_week_tracks.iterrows(): 

            artist = row["Artist"]
            track = row["Track"]

            top_tags += get_track_top_tags(track, artist)

        text = " ".join(top_tags)
        wordcloud = WordCloud().generate(text)
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis("off")
        plt.show()
        st.pyplot()
    
with tab_recently_played: 

    recently_played = get_recently_played()
    recently_played["Listened at"] = pd.to_datetime(recently_played["Listened at"], format="%d %b %Y, %H:%M").dt.tz_localize("UTC")
    recently_played["Listened at"] = recently_played["Listened at"].dt.tz_convert(timezone("US/Central"))
    recently_played["Listened at"] = recently_played["Listened at"].dt.strftime("%d %b %Y, %H:%M %Z")

    st.markdown(f"### Recently Played")
    builder = GridOptionsBuilder.from_dataframe(recently_played)
    builder.configure_column("Track",
                             cellStyle={"fontWeight": "bold"})
    
    builder.configure_grid_options(rowHeight=50, suppressColumnVirtualisation=True) 
    builder.configure_grid_options(onFirstDataRendered="function() { gridOptions.api.sizeColumnsToFit(); }")

    options = builder.build()

    grid = AgGrid(recently_played, 
                  gridOptions=options,
                  columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS,
                  allow_unsafe_jscode=True, 
                  theme=AgGridTheme.ALPINE,
                  height=800)