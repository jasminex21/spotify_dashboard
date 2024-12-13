import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
from dotenv import load_dotenv
import pandas as pd
from st_aggrid import AgGrid, JsCode, ColumnsAutoSizeMode, AgGridTheme
from st_aggrid.grid_options_builder import GridOptionsBuilder
from datetime import datetime, timedelta
import pytz

# load environmental vars - includes spotify API credentials
load_dotenv()

SCOPES = ["user-read-currently-playing", # read access to a user’s currently playing content
          "user-top-read", # read access to a user's top artists and tracks
          "user-read-recently-played", # read access to a user’s recently played tracks
          "user-read-email"] # read access to user’s email address

TIME_FRAMES = ["Short term", 
               "Medium term", 
               "Long term"]

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

THEME = {"background_color": "#082D1B",
         "button_color": "#0E290E",
         "inputs": "#547054",
         "text_color": "white"}

# page configurations
st.set_page_config(
    page_title="Spotify Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded")

st.title(":bar_chart: Jasmine's *Custom* Streaming Dashboard")

apply_theme(THEME)

col01, col02, col03 = st.columns(3)
platform = col01.selectbox("Select platform",
                           options=["last.fm", "Spotify"])

if platform == "Spotify":

    OAUTH = SpotifyOAuth(client_id=os.getenv('CLIENT_ID'), 
                            client_secret=os.getenv('CLIENT_SECRET'), 
                            redirect_uri=os.getenv('SPOTIPY_REDIRECT_URI'), 
                            scope=SCOPES)

    # the 'code' param in the URL indicates a successful login
    if "code" in st.query_params:

        code = st.query_params["code"]
        token_info = OAUTH.get_access_token(code)
        access_token = token_info["access_token"]

        # use access token to create a Spotify client
        # SPOTIFY = spotipy.Spotify(auth_manager=sp_oauth)
        SPOTIFY = spotipy.Spotify(auth=access_token)

        user_dict = SPOTIFY.current_user()
        st.markdown(f"#### :wave: Hi {user_dict['display_name']}!")

        (tab_summary, 
        tab_top_artists, 
        tab_top_tracks, 
        tab_recently_played) = st.tabs(["Summary", "Top Artists", "Top Tracks", "Recently Played"])
        
        with tab_top_artists:
            col1, col2, col3 = st.columns(3)
            time_frame = col1.selectbox("Select a time frame",
                                    options=TIME_FRAMES,
                                    key="time_frame_artists")
            st.markdown(f"### Your Top Artists: {time_frame}")
            time_frame = "_".join(time_frame.split(" ")).lower()

            top_artists = []

            for i, item in enumerate(SPOTIFY.current_user_top_artists(limit=50, time_range=time_frame)["items"]):

                artist_info = {
                    "rank": i + 1,
                    "name": item["name"], 
                    "uri": item["uri"],
                    "genres": ', '.join(item["genres"]),
                    "popularity": item["popularity"],
                    "followers": item["followers"]["total"],
                    "image_url": item["images"][1]["url"]
                }

                top_artists.append(artist_info)

            TOP_ARTISTS = pd.DataFrame(top_artists)
            cols = ["rank", "image_url", "name", "genres", "popularity"]

            builder = GridOptionsBuilder.from_dataframe(TOP_ARTISTS[cols])
            # TODO: center row contents vertically in their cells

            # allows for artist images to be displayed in the dataframe
            builder.configure_column("image_url",
                                    headerName="", 
                                    width=300,
                                    cellRenderer=JsCode("""
                                        class UrlCellRenderer {
                                        init(params) {
                                            this.eGui = document.createElement('img');
                                            this.eGui.setAttribute('src', params.value);
                                            this.eGui.setAttribute('style', "width:65px;height:65px");
                                        }
                                        getGui() {
                                            return this.eGui;
                                        }
                                        }"""
                                    )
                                )   
            builder.configure_grid_options(rowHeight=65) #suppressColumnVirtualisation=True)
            options = builder.build()
            grid = AgGrid(TOP_ARTISTS[cols], 
                        gridOptions=options,
                        # columns_auto_size_mode=ColumnsAutoSizeMode.NO_AUTOSIZE,
                        allow_unsafe_jscode=True, 
                        theme=AgGridTheme.ALPINE,
                        height=800)
            
            with tab_top_tracks:
                col1, col2, col3 = st.columns(3)
                time_frame = col1.selectbox("Select a time frame",
                                        options=TIME_FRAMES)
                st.markdown(f"### Your Top Tracks: {time_frame}")
                time_frame = "_".join(time_frame.split(" ")).lower()

                top_tracks = []

                for i, item in enumerate(SPOTIFY.current_user_top_tracks(limit=50, time_range=time_frame)["items"]):
                    track_info = {
                        "rank": i + 1,
                        "name": item["name"],
                        "artists": ", ".join([art["name"] for art in item["artists"]]),
                        "album": item["album"]["name"],
                        "uri": item["uri"],
                        "image_url": item["album"]["images"][1]["url"],
                        "popularity": item["popularity"]
                        
                    }

                    top_tracks.append(track_info)

                TOP_TRACKS = pd.DataFrame(top_tracks)
                cols = ["rank", "image_url", "name", "artists", "popularity"]

                builder = GridOptionsBuilder.from_dataframe(TOP_TRACKS[cols])
                # TODO: center row contents vertically in their cells

                # allows for artist images to be displayed in the dataframe
                builder.configure_column("image_url",
                                        headerName="", 
                                        width=300,
                                        cellRenderer=JsCode("""
                                            class UrlCellRenderer {
                                            init(params) {
                                                this.eGui = document.createElement('img');
                                                this.eGui.setAttribute('src', params.value);
                                                this.eGui.setAttribute('style', "width:65px;height:65px");
                                            }
                                            getGui() {
                                                return this.eGui;
                                            }
                                            }"""
                                        )
                                    )   
                builder.configure_grid_options(rowHeight=65) #suppressColumnVirtualisation=True)
                options = builder.build()
                grid = AgGrid(TOP_TRACKS[cols], 
                            gridOptions=options,
                            # columns_auto_size_mode=ColumnsAutoSizeMode.NO_AUTOSIZE,
                            allow_unsafe_jscode=True, 
                            theme=AgGridTheme.ALPINE,
                            height=800)
            
            with tab_recently_played:

                # TODO: enable date range
                # st.markdown("## Select Date Range to Analyze")
                # st.date_input("Date range", 
                #             value=(last_date - default_diff, last_date), 
                #             min_value=datetime.date(2024, 1, 13),
                #             max_value=last_date,
                #             format="MM/DD/YYYY",
                #             key="date_range")

                recently_played = []

                for i, item in enumerate(SPOTIFY.current_user_recently_played(limit=50)["items"]):

                    song_info = {
                        "played_at": item["played_at"],
                        "name": item["track"]["name"],
                        "artists": ", ".join([art["name"] for art in item["track"]["artists"]])
                    }

                    recently_played.append(song_info)

                RECENTLY_PLAYED = pd.DataFrame(recently_played)
                RECENTLY_PLAYED["played_at"] = pd.to_datetime(RECENTLY_PLAYED["played_at"]).dt.tz_convert('America/Chicago')
                RECENTLY_PLAYED["played_at"] = RECENTLY_PLAYED["played_at"].dt.strftime('%Y/%m/%d\t\t%H:%M:%S')
                
                builder = GridOptionsBuilder.from_dataframe(RECENTLY_PLAYED)
                builder.configure_grid_options(rowHeight=30) #suppressColumnVirtualisation=True)
                options = builder.build()

                AgGrid(RECENTLY_PLAYED,
                    columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS, 
                    gridOptions=options,
                    theme=AgGridTheme.ALPINE,
                    height=800)

    # not currently logged in
    else: 
        AUTH_URL = OAUTH.get_authorize_url()
        st.markdown(f'<h4>🌞 <a href="{AUTH_URL}" target="_self" style="text-decoration:none;">Log in with Spotify</a></h4>',
                    unsafe_allow_html=True)

# lastfm
else: 

    # can change the tab options - keeping it this for now
    (tab_summary, 
     tab_top_artists, 
     tab_top_tracks, 
     tab_recently_played) = st.tabs(["Summary", "Top Artists", "Top Tracks", "Recently Played"])