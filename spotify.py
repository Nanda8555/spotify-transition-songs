import os
import logging
from flask import Flask, render_template, jsonify, request, session
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials
import spotipy
import spotify_client
import database
import transition_algorithms

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'

# Configure logging
logging.basicConfig(level=logging.INFO)

def get_spotify_client():
    return spotify_client.create_spotify_client()

@app.route('/')
def home():
    return render_template('search.html')

@app.route('/api/search_tracks')
def search_tracks():
    query = request.args.get('query', '')
    if not query:
        return jsonify([]), 400
    
    try:
        sp = get_spotify_client()
        if not sp:
            return jsonify({"error": "authentication_failed"}), 401
        
        # Search for tracks
        results = sp.search(q=query, type='track', limit=10)
        
        tracks = []
        for track in results['tracks']['items']:
            track_data = {
                'id': track['id'],
                'name': track['name'],
                'artist': track['artists'][0]['name'] if track['artists'] else 'Unknown',
                'album': track['album']['name'] if track.get('album') else 'Unknown',
                'preview_url': track.get('preview_url'),
                'popularity': track.get('popularity', 0),
                'external_urls': track.get('external_urls', {})
            }
            tracks.append(track_data)
        
        return jsonify(tracks)
    
    except Exception as e:
        logging.error(f"Search error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/popular_tracks")
def get_popular_tracks():
    """Get popular tracks with aggressive strategies to find ones with preview URLs"""
    sp = get_spotify_client()
    if not sp:
        return jsonify({"error": "authentication_failed"}), 401
    
    try:
        tracks = []
        tracks_with_preview = 0
        strategies_used = []
        
        print("Starting aggressive preview search...")
        
        # Strategy 1: Search for specific popular songs known to have previews
        known_hits = [
            "flowers miley cyrus", "as it was harry styles", "heat waves glass animals",
            "stay the kid laroi", "good 4 u olivia rodrigo", "blinding lights the weeknd",
            "watermelon sugar harry styles", "positions ariana grande", "drivers license olivia rodrigo",
            "levitating dua lipa", "save your tears the weeknd", "peaches justin bieber",
            "industry baby lil nas x", "ghost justin bieber", "bad habits ed sheeran",
            "shivers ed sheeran", "enemy imagine dragons", "cold heart elton john",
            "about damn time lizzo", "running up that hill kate bush", "sunroof nicky youre"
        ]
        
        for track_search in known_hits[:12]:  # Search first 12
            try:
                search_results = sp.search(q=track_search, type="track", limit=3, market="US")
                if search_results and search_results.get("tracks", {}).get("items"):
                    for track in search_results["tracks"]["items"]:
                        if len(tracks) >= 20:  # Limit
                            break
                            
                        # Skip duplicates
                        if any(t["id"] == track["id"] for t in tracks):
                            continue
                            
                        track_info = {
                            "id": track["id"],
                            "name": track["name"],
                            "artist": track["artists"][0]["name"] if track.get("artists") else "",
                            "album": track["album"]["name"] if track.get("album") else "",
                            "preview_url": track.get("preview_url"),
                            "popularity": track.get("popularity", 0),
                            "duration_ms": track.get("duration_ms", 0),
                            "external_urls": track.get("external_urls", {})
                        }
                        
                        tracks.append(track_info)
                        if track.get("preview_url"):
                            tracks_with_preview += 1
                            print(f"✓ Found preview: {track['name']} by {track['artists'][0]['name']}")
                
                if len(tracks) >= 15:
                    break
                    
            except Exception as e:
                print(f"Search for '{track_search}' failed: {e}")
                continue
        
        if tracks:
            strategies_used.append("Known Hit Songs")
        
        # Strategy 2: Search for radio edits and official versions
        if tracks_with_preview < 8:
            print("Searching radio edits and official versions...")
            special_queries = [
                'track:"radio edit" year:2020-2024',
                'track:"official video" year:2021-2024',
                'track:"single version" year:2020-2024',
                'track:"remix" year:2022-2024',
                '"greatest hits" year:2020-2024'
            ]
            
            for query in special_queries[:3]:
                try:
                    search_results = sp.search(q=query, type="track", limit=12, market="US")
                    if search_results and search_results.get("tracks", {}).get("items"):
                        found_in_query = 0
                        for track in search_results["tracks"]["items"]:
                            if len(tracks) >= 20:
                                break
                                
                            # Skip duplicates
                            if any(t["id"] == track["id"] for t in tracks):
                                continue
                                
                            track_info = {
                                "id": track["id"],
                                "name": track["name"],
                                "artist": track["artists"][0]["name"] if track.get("artists") else "",
                                "album": track["album"]["name"] if track.get("album") else "",
                                "preview_url": track.get("preview_url"),
                                "popularity": track.get("popularity", 0),
                                "duration_ms": track.get("duration_ms", 0),
                                "external_urls": track.get("external_urls", {})
                            }
                            
                            tracks.append(track_info)
                            if track.get("preview_url"):
                                tracks_with_preview += 1
                                found_in_query += 1
                                print(f"✓ Preview from special search: {track['name']}")
                        
                        if found_in_query > 0 and "Special Versions" not in strategies_used:
                            strategies_used.append("Special Versions")
                except Exception as e:
                    print(f"Special search failed: {e}")
                    continue
        
        # Strategy 3: Featured playlists (often have preview tracks)
        if tracks_with_preview < 5:
            print("Searching featured playlists...")
            try:
                playlists = sp.featured_playlists(limit=5, country="US")
                if playlists and playlists.get("playlists", {}).get("items"):
                    for playlist in playlists["playlists"]["items"][:3]:
                        try:
                            playlist_tracks = sp.playlist_tracks(playlist["id"], limit=15)
                            if playlist_tracks and playlist_tracks.get("items"):
                                found_in_playlist = 0
                                for item in playlist_tracks["items"]:
                                    track = item.get("track")
                                    if track and len(tracks) < 20:
                                        # Skip duplicates
                                        if any(t["id"] == track["id"] for t in tracks):
                                            continue
                                            
                                        track_info = {
                                            "id": track["id"],
                                            "name": track["name"],
                                            "artist": track["artists"][0]["name"] if track.get("artists") else "",
                                            "album": track["album"]["name"] if track.get("album") else "",
                                            "preview_url": track.get("preview_url"),
                                            "popularity": track.get("popularity", 0),
                                            "duration_ms": track.get("duration_ms", 0),
                                            "external_urls": track.get("external_urls", {})
                                        }
                                        
                                        tracks.append(track_info)
                                        if track.get("preview_url"):
                                            tracks_with_preview += 1
                                            found_in_playlist += 1
                                            print(f"✓ Preview from playlist '{playlist['name']}': {track['name']}")
                                
                                if found_in_playlist > 0 and "Featured Playlists" not in strategies_used:
                                    strategies_used.append("Featured Playlists")
                                    
                        except Exception as e:
                            print(f"Playlist '{playlist['name']}' failed: {e}")
                            continue
            except Exception as e:
                print(f"Featured playlists strategy failed: {e}")
        
        # Strategy 4: Popular artist albums
        if tracks_with_preview < 3:
            print("Searching popular artist albums...")
            popular_artists = ["drake", "taylor swift", "ariana grande", "post malone", "billie eilish"]
            
            for artist_name in popular_artists[:3]:
                try:
                    artist_results = sp.search(q=artist_name, type="artist", limit=1)
                    if artist_results["artists"]["items"]:
                        artist_id = artist_results["artists"]["items"][0]["id"]
                        albums = sp.artist_albums(artist_id, album_type="album,single", limit=3)
                        
                        for album in albums["items"]:
                            try:
                                album_tracks = sp.album_tracks(album["id"], limit=8)
                                for track in album_tracks["items"]:
                                    if len(tracks) >= 20:
                                        break
                                    
                                    # Get full track details
                                    full_track = sp.track(track["id"])
                                    
                                    # Skip duplicates
                                    if any(t["id"] == full_track["id"] for t in tracks):
                                        continue
                                        
                                    track_info = {
                                        "id": full_track["id"],
                                        "name": full_track["name"],
                                        "artist": full_track["artists"][0]["name"] if full_track.get("artists") else artist_name,
                                        "album": full_track["album"]["name"] if full_track.get("album") else "",
                                        "preview_url": full_track.get("preview_url"),
                                        "popularity": full_track.get("popularity", 0),
                                        "duration_ms": full_track.get("duration_ms", 0),
                                        "external_urls": full_track.get("external_urls", {})
                                    }
                                    
                                    tracks.append(track_info)
                                    if full_track.get("preview_url"):
                                        tracks_with_preview += 1
                                        print(f"✓ Preview from {artist_name} album: {full_track['name']}")
                                
                                if len(tracks) >= 18:
                                    break
                            except Exception as e:
                                print(f"Album tracks failed: {e}")
                                continue
                        
                        if tracks_with_preview > 0 and "Popular Artists" not in strategies_used:
                            strategies_used.append("Popular Artists")
                            
                except Exception as e:
                    print(f"Artist {artist_name} search failed: {e}")
                    continue
        
        # Remove exact duplicates and prioritize tracks with previews
        unique_tracks = {}
        for track in tracks:
            if track["id"] not in unique_tracks:
                unique_tracks[track["id"]] = track
        
        final_tracks = list(unique_tracks.values())
        
        # Sort: preview tracks first, then by popularity
        final_tracks.sort(key=lambda x: (x.get("preview_url") is not None, x.get("popularity", 0)), reverse=True)
        
        # Limit to 12 tracks
        final_tracks = final_tracks[:12]
        final_preview_count = sum(1 for t in final_tracks if t.get("preview_url"))
        
        print(f"Final result: {len(final_tracks)} tracks, {final_preview_count} with previews")
        
        return jsonify({
            "tracks": final_tracks,
            "total_found": len(final_tracks),
            "preview_count": final_preview_count,
            "strategies_used": strategies_used if strategies_used else ["Basic Search"]
        })
        
    except Exception as e:
        print(f"Error in get_popular_tracks: {e}")
        logging.error(f"Popular tracks error: {str(e)}")
        return jsonify({"error": f"Failed to fetch popular tracks: {str(e)}"}), 500

@app.route('/api/track_features/<track_id>')
def get_track_features(track_id):
    try:
        sp = get_spotify_client()
        if not sp:
            return jsonify({"error": "authentication_failed"}), 401
        
        features = spotify_client.get_track_features(sp, track_id)
        return jsonify(features)
    
    except Exception as e:
        logging.error(f"Track features error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/basic_recommendations', methods=['POST'])
def basic_recommendations():
    try:
        data = request.json
        track_ids = data.get('track_ids', [])
        
        if not track_ids or len(track_ids) != 2:
            return jsonify({"error": "Please provide exactly 2 track IDs"}), 400
        
        sp = get_spotify_client()
        if not sp:
            return jsonify({"error": "authentication_failed"}), 401
        
        # Get basic recommendations using our algorithm with correct parameters
        result = transition_algorithms.basic_transition_algorithm(sp, track_ids)
        
        return jsonify(result)
    
    except Exception as e:
        logging.error(f"Basic recommendations error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/smart_recommendations', methods=['POST'])
def smart_recommendations():
    try:
        data = request.json
        track_ids = data.get('track_ids', [])
        
        if not track_ids or len(track_ids) != 2:
            return jsonify({"error": "Please provide exactly 2 track IDs"}), 400
        
        sp = get_spotify_client()
        if not sp:
            return jsonify({"error": "authentication_failed"}), 401
        
        # Get smart recommendations using our algorithm with correct parameters
        result = transition_algorithms.smart_transition_algorithm(sp, track_ids)
        
        return jsonify(result)
    
    except Exception as e:
        logging.error(f"Smart recommendations error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/playlist_preview', methods=['POST'])
def playlist_preview():
    """Create a playlist preview for transition simulation"""
    try:
        data = request.json
        track_ids = data.get('track_ids', [])
        
        if not track_ids:
            return jsonify({"error": "Track IDs are required"}), 400
        
        sp = get_spotify_client()
        if not sp:
            return jsonify({"error": "authentication_failed"}), 401
        
        playlist_tracks = []
        tracks_with_preview = 0
        
        for track_id in track_ids:
            try:
                track = sp.track(track_id)
                if track:
                    track_info = {
                        "id": track["id"],
                        "name": track["name"],
                        "artist": track["artists"][0]["name"] if track.get("artists") else "",
                        "album": track["album"]["name"] if track.get("album") else "",
                        "preview_url": track.get("preview_url"),
                        "external_urls": track.get("external_urls", {}),
                        "popularity": track.get("popularity", 0),
                        "duration_ms": track.get("duration_ms", 0)
                    }
                    playlist_tracks.append(track_info)
                    
                    if track.get("preview_url"):
                        tracks_with_preview += 1
                        
            except Exception as e:
                print(f"Error fetching track {track_id}: {e}")
                continue
        
        return jsonify({
            "playlist": playlist_tracks,
            "tracks_with_preview": tracks_with_preview,
            "total_tracks": len(playlist_tracks),
            "simulation_mode": tracks_with_preview == 0
        })
        
    except Exception as e:
        logging.error(f"Playlist preview error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/save_settings', methods=['POST'])
def save_settings():
    try:
        data = request.json
        track_id = data.get('track_id')
        settings = data.get('settings', {})
        
        if not track_id:
            return jsonify({"error": "Track ID is required"}), 400
        
        # Save settings to database
        database.save_track_settings(track_id, settings)
        
        return jsonify({"success": True, "message": "Settings saved successfully"})
    
    except Exception as e:
        logging.error(f"Save settings error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/get_settings/<track_id>')
def get_settings(track_id):
    try:
        settings = database.get_track_settings(track_id)
        return jsonify({"settings": settings})
    
    except Exception as e:
        logging.error(f"Get settings error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    database.init_database()
    app.run(host='0.0.0.0', port=5001, debug=True)
