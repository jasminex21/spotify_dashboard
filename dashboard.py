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
import requests
from concurrent.futures import ThreadPoolExecutor
import plotly.graph_objects as go
import plotly.express as px


# load environmental vars - includes spotify API credentials
load_dotenv()

SCOPES = ["user-read-currently-playing", # read access to a user’s currently playing content
          "user-top-read", # read access to a user's top artists and tracks
          "user-read-recently-played", # read access to a user’s recently played tracks
          "user-read-email"] # read access to user’s email address

TIME_FRAMES = ["Short term", 
               "Medium term", 
               "Long term"]

TIMEZONE = pytz.timezone("US/Central")
NOW = datetime.now(TIMEZONE)
MONDAY = (NOW - timedelta(days = NOW.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)

USER_AGENT = os.getenv('LASTFM_USER_AGENT')
API_KEY = os.getenv('LASTFM_API_KEY')
LASTFM_USER = "jasminexx18"

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

def get_track_coverart(track_mbid):

    # time.sleep(0.1)

    try:
        musicbrainz_url = f"https://musicbrainz.org/ws/2/recording/{track_mbid}?inc=releases&fmt=json"
        response = requests.get(musicbrainz_url)

        if response.status_code == 200:
            data = response.json()
            releases = data.get("releases", [])

            if releases:
                release_mbid = releases[0].get("id")
                cover_art_url = f"https://coverartarchive.org/release/{release_mbid}/"
                cover_response = requests.get(cover_art_url)

                if cover_response.status_code == 200:
                    cover_data = cover_response.json()

                    for image in cover_data.get("images", []):

                        if image.get("front", False):
                            return image.get("thumbnails")["small"]       
                        
    except Exception as e:
        print(f"Error fetching cover art for {track_mbid}: {e}")

    return "https://lastfm.freetls.fastly.net/i/u/64s/2a96cbd8b46e442fc41c2b86b821562f.png"

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

THEME = {"background_color": "#082D1B",
         "button_color": "#0E290E",
         "inputs": "#547054",
         "text_color": "white"}
long_periods = ["Last 7 days", "Last month", "Last 3 months", 
                "Last 6 months", "Last year", "Overall"]
short_periods = ["7day", "1month", "3month", 
                 "6month", "12month", "overall"]
PERIOD_MAPPING = dict(zip(long_periods, short_periods))

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
    (tab_this_week, 
     tab_top_artists, 
     tab_top_tracks) = st.tabs(["This Week", "Top Artists", "Top Tracks"])
    
    with tab_this_week: 
        tab_top_this_week, tab_recently_played = st.tabs(["Top Tracks", "Recently Played"])

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

        all_tracks = pd.DataFrame(all_tracks)

        with tab_top_this_week:
            
            col1, col2 = st.columns([1.5, 1])
            with col1: 
                this_week_tracks = all_tracks.groupby(["Track", "Artist", "Album"])["Track"].count().reset_index(name="Streams").sort_values("Streams", ascending=False)
                this_week_tracks["Rank"] = list(range(1, this_week_tracks.shape[0] + 1))
                this_week_tracks = this_week_tracks[["Rank", "Track", "Artist", "Album", "Streams"]]
                
                st.markdown(f"### Your Top Tracks since {MONDAY.date()}")
                builder = GridOptionsBuilder.from_dataframe(this_week_tracks)
                builder.configure_column("Track",
                                         cellStyle={"fontWeight": "bold"},
                                         maxWidth=250)  
                builder.configure_column("Artist",
                                         maxWidth=200)  
                builder.configure_column("Album",
                                         maxWidth=250)  
                builder.configure_column("Rank",
                                         maxWidth=100)  
                builder.configure_column("Streams",
                                         maxWidth=120)  
                
                builder.configure_grid_options(rowHeight=50, suppressColumnVirtualisation=True) 
                # builder.configure_grid_options(onFirstDataRendered="function() { gridOptions.api.sizeColumnsToFit(); }")

                options = builder.build()

                grid = AgGrid(this_week_tracks, 
                              gridOptions=options,
                              columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS,
                              allow_unsafe_jscode=True, 
                              theme=AgGridTheme.ALPINE,
                              height=800)

        with tab_recently_played:

                st.markdown(f"### Your Recently Played since {MONDAY.date()}")
                builder = GridOptionsBuilder.from_dataframe(all_tracks)
                builder.configure_column("Track",
                                         cellStyle={"fontWeight": "bold"})  
                
                builder.configure_grid_options(rowHeight=50, suppressColumnVirtualisation=True) 
                # builder.configure_grid_options(onFirstDataRendered="function() { gridOptions.api.sizeColumnsToFit(); }")

                options = builder.build()

                grid = AgGrid(all_tracks, 
                              gridOptions=options,
                              columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS,
                              allow_unsafe_jscode=True, 
                              theme=AgGridTheme.ALPINE,
                              height=800)

    with tab_top_tracks:

        col1, col2 = st.columns([1.5, 1])
        with col1:
            period = st.selectbox("Select time period",
                                  options=long_periods)
            
            r = lastfm_get({'method': 'user.getTopTracks', 
                            'user': "jasminexx18",
                            'period': PERIOD_MAPPING[period]})
            week_tracks = r.json()["toptracks"]

            # with ThreadPoolExecutor(max_workers=2) as executor: 
            #     results = executor.map(process_track, [track for track in week_tracks["track"] if int(track["playcount"]) > 2])
            all_week_tracks = pd.DataFrame([process_track(track) for track in week_tracks["track"]])

            st.markdown(f"### Your Top Tracks: {period}")
            builder = GridOptionsBuilder.from_dataframe(all_week_tracks)
            builder.configure_column("Track",
                                     cellStyle={"fontWeight": "bold"})  
            
            builder.configure_grid_options(rowHeight=50, suppressColumnVirtualisation=True) 
            # builder.configure_grid_options(onFirstDataRendered="function() { gridOptions.api.sizeColumnsToFit(); }")

            options = builder.build()
            
            # custom_css = {
            #     ".ag-root.ag-unselectable.ag-layout-normal": {
            #         "font-family": "Outfit, sans-serif !important;"
            #     },
            #     ".ag-header-cell-text": {
            #         "font-family": "Outfit, sans-serif !important;",
            #         "font-weight": "bolder !important;", 
            #         "font-size": "larger !important;"
            #     }
            # }

            grid = AgGrid(all_week_tracks, 
                        gridOptions=options,
                        columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS,
                        # custom_css=custom_css,
                        allow_unsafe_jscode=True, 
                        theme=AgGridTheme.ALPINE,
                        height=800,
                        )
        with col2: 
            st.markdown("### ")
            st.markdown("### ")
            artist_counts = all_week_tracks.value_counts().reset_index()
            labels = artist_counts["Artist"]
            values = artist_counts["count"]

            fig = go.Figure(data=[go.Pie(labels=labels, 
                                         values=values, 
                                         hole=.3,
                                         marker=dict(colors=px.colors.qualitative.Alphabet),
                                         hovertemplate=(
        '<b>%{label}</b><br>' 
        '# of tracks: %{value}<br>' 
        'Pct.: %{percent:.2%}<br>' 
        '<extra></extra>'
    ))])
            fig.update_layout(title = "Artist Representation")
            st.plotly_chart(fig, use_container_width=True)

            # durations = all_week_tracks["Duration"].astype(int) / 60
            # durations_hist = go.Figure(data=[go.Histogram(x=durations, 
            #                                               xbins=dict(start=min(durations), end=max(durations), size=1))])
            # durations_hist.update_layout(title = "Distribution of Track Durations", 
            #                              hovermode='x unified')
            # st.plotly_chart(durations_hist, use_container_width=True)
            # extra stats maybe 
            # st.markdown(f"#### Additional Stats")
            # st.markdown(f"{len(all_week_tracks['Artist'].unique())} unique artists are represented")

            # artists weighted by rank or # of streams?

