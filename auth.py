import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import requests
from PIL import Image
import os
from dotenv import load_dotenv
import pandas as pd

# load environmental vars - includes spotify API credentials
load_dotenv()

SCOPES = ["user-read-currently-playing", # read access to a user’s currently playing content
          "user-top-read", # read access to a user's top artists and tracks
          "user-read-recently-played", # read access to a user’s recently played tracks
          "user-read-email"] # read access to user’s email address

st.title("Spotify Dashboard")

sp_oauth = SpotifyOAuth(client_id=os.getenv('CLIENT_ID'), 
                        client_secret=os.getenv('CLIENT_SECRET'), 
                        redirect_uri=os.getenv('SPOTIPY_REDIRECT_URI'), 
                        scope=SCOPES)
auth_url = sp_oauth.get_authorize_url()
# if not still logged in
st.markdown(f'<a href="{auth_url}" target="_self"><b>Log in with Spotify</b></a>', unsafe_allow_html=True)

# Check for the 'code' parameter in the URL, which indicates a successful login
if "code" in st.query_params:
    code = st.query_params["code"]
    token_info = sp_oauth.get_access_token(code)
    access_token = token_info["access_token"]

    # Use the access token to create a Spotify client
    SPOTIFY = spotipy.Spotify(auth_manager=sp_oauth)

    # Confirm successful login to the user
    st.success("You have successfully logged in to Spotify!")

    top_artists = []

    for item in SPOTIFY.current_user_top_artists(limit=50, time_range="short_term")["items"]:
        
        artist_info = {
            "name": item["name"], 
            "uri": item["uri"],
            "genres": item["genres"],
            "popularity": item["popularity"],
            "followers": item["followers"]["total"],
            "image_url": item["images"][1]["url"]
        }

        top_artists.append(artist_info)

    TOP_ARTISTS = pd.DataFrame(top_artists)
    st.write(TOP_ARTISTS)