import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import logging

load_dotenv()

def create_spotify_client():
    
    try:
        client_id = os.getenv("CLIENT_ID")  
        client_secret = os.getenv("CLIENT_SECRET")  
        
        if not client_id or not client_secret:
            logging.error("Missing Spotify credentials in environment variables")
            return None
            
        # Client Credentials Flow (for app-level access)
        client_credentials_manager = SpotifyClientCredentials(
            client_id=client_id,
            client_secret=client_secret
        )
        
        sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
        
        # Test the connection
        sp.search(q="test", type="track", limit=1)
        logging.info("Spotify client authenticated successfully")
        return sp
        
    except Exception as e:
        logging.error(f"Failed to create Spotify client: {str(e)}")
        return None

def get_track_features(sp, track_id):
    """
    Get audio features for a track with error handling
    """
    try:
        features = sp.audio_features([track_id])
        if features and features[0]:
            return features[0]
        return None
    except Exception as e:
        logging.warning(f"Could not get features for track {track_id}: {str(e)}")
        # Return default values if API fails
        return {
            'tempo': 120.0,
            'energy': 0.5,
            'danceability': 0.5,
            'valence': 0.5,
            'acousticness': 0.5,
            'instrumentalness': 0.0,
            'liveness': 0.1,
            'speechiness': 0.1,
            'loudness': -10.0
        }

def search_tracks(sp, query, limit=20):
    """
    Search for tracks with error handling
    """
    try:
        results = sp.search(q=query, type='track', limit=limit)
        return results.get('tracks', {}).get('items', [])
    except Exception as e:
        logging.error(f"Search failed for query '{query}': {str(e)}")
        return []

def get_recommendations(sp, seed_tracks=None, seed_artists=None, seed_genres=None, limit=20, **kwargs):
    """
    Get recommendations with error handling
    """
    try:
        return sp.recommendations(
            seed_tracks=seed_tracks,
            seed_artists=seed_artists, 
            seed_genres=seed_genres,
            limit=limit,
            **kwargs
        )
    except Exception as e:
        logging.error(f"Recommendations failed: {str(e)}")
        return {'tracks': []}
