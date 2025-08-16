"""
Smart transition algorithms and recommendation logic
"""
import logging
from spotify_client import get_track_features, search_tracks, get_recommendations

def smart_transition_algorithm(sp, track_ids):
    """
    Advanced algorithm to find transition tracks between two songs
    Uses multiple strategies: related artists, albums, genres, and audio features
    """
    try:
        if len(track_ids) != 2:
            return {"error": "Please provide exactly 2 track IDs"}, 400

        track1_id, track2_id = track_ids
        suggestions = []
        strategies_used = []
        existing_ids = set([track1_id, track2_id])

        # Get track details and features
        track1 = sp.track(track1_id)
        track2 = sp.track(track2_id)
        features1 = get_track_features(sp, track1_id)
        features2 = get_track_features(sp, track2_id)

        if not track1 or not track2:
            return {"error": "Could not fetch track details"}, 500

        logging.info(f"Finding transition between '{track1['name']}' and '{track2['name']}'")

        # Strategy 1: Related Artists
        if len(suggestions) < 15:
            try:
                artist1_id = track1["artists"][0]["id"]
                artist2_id = track2["artists"][0]["id"]
                
                related1 = sp.artist_related_artists(artist1_id)["artists"][:3]
                related2 = sp.artist_related_artists(artist2_id)["artists"][:3]
                
                for artist in related1 + related2:
                    try:
                        albums = sp.artist_albums(artist["id"], limit=2)["items"]
                        for album in albums:
                            tracks = sp.album_tracks(album["id"], limit=3)["items"]
                            for track in tracks:
                                if track["id"] not in existing_ids and len(suggestions) < 15:
                                    suggestions.append({
                                        "id": track["id"],
                                        "name": track["name"],
                                        "artist": track["artists"][0]["name"],
                                        "preview_url": track.get("preview_url"),
                                        "strategy": "Related Artist",
                                        "popularity": sp.track(track["id"]).get("popularity", 0)
                                    })
                                    existing_ids.add(track["id"])
                    except Exception as e:
                        logging.warning(f"Related artist search failed: {str(e)}")
                        continue
                        
                if suggestions:
                    strategies_used.append("Related Artists")
                    
            except Exception as e:
                logging.warning(f"Related artists strategy failed: {str(e)}")

        # Strategy 2: Album-based recommendations
        if len(suggestions) < 15:
            try:
                album1_id = track1["album"]["id"]
                album2_id = track2["album"]["id"]
                
                for album_id in [album1_id, album2_id]:
                    try:
                        album_tracks = sp.album_tracks(album_id, limit=10)["items"]
                        for track in album_tracks:
                            if track["id"] not in existing_ids and len(suggestions) < 15:
                                suggestions.append({
                                    "id": track["id"],
                                    "name": track["name"],
                                    "artist": track["artists"][0]["name"],
                                    "preview_url": track.get("preview_url"),
                                    "strategy": "Same Album",
                                    "popularity": sp.track(track["id"]).get("popularity", 0)
                                })
                                existing_ids.add(track["id"])
                    except Exception as e:
                        continue
                        
                if len([s for s in suggestions if s["strategy"] == "Same Album"]) > 0:
                    strategies_used.append("Album Exploration")
                    
            except Exception as e:
                logging.warning(f"Album strategy failed: {str(e)}")

        # Strategy 3: Genre and audio feature matching (using search fallback)
        if len(suggestions) < 15:
            try:
                # First try the recommendations API
                try:
                    # Calculate average audio features
                    avg_tempo = (features1.get("tempo", 120) + features2.get("tempo", 120)) / 2
                    avg_energy = (features1.get("energy", 0.5) + features2.get("energy", 0.5)) / 2
                    avg_valence = (features1.get("valence", 0.5) + features2.get("valence", 0.5)) / 2
                    avg_danceability = (features1.get("danceability", 0.5) + features2.get("danceability", 0.5)) / 2
                    
                    # Get recommendations based on audio features
                    recommendations = get_recommendations(
                        sp,
                        seed_tracks=[track1_id, track2_id],
                        limit=10,
                        target_tempo=avg_tempo,
                        target_energy=avg_energy,
                        target_valence=avg_valence,
                        target_danceability=avg_danceability
                    )
                    
                    if recommendations and recommendations.get("tracks"):
                        for track in recommendations["tracks"]:
                            if track["id"] not in existing_ids and len(suggestions) < 15:
                                suggestions.append({
                                    "id": track["id"],
                                    "name": track["name"],
                                    "artist": track["artists"][0]["name"],
                                    "preview_url": track.get("preview_url"),
                                    "strategy": "Audio Features Match",
                                    "popularity": track.get("popularity", 0)
                                })
                                existing_ids.add(track["id"])
                        
                        if len([s for s in suggestions if s["strategy"] == "Audio Features Match"]) > 0:
                            strategies_used.append("Audio Features")
                except:
                    # Fallback to genre-based search if recommendations API fails
                    logging.info("Recommendations API failed, using genre-based search fallback")
                    genre_searches = ["electronic", "pop", "indie", "rock", "dance"]
                    
                    # Determine likely genre based on audio features
                    if avg_energy > 0.7:
                        genre_searches = ["electronic dance", "pop hits", "high energy"] + genre_searches
                    elif avg_valence > 0.6:
                        genre_searches = ["happy songs", "pop hits", "upbeat"] + genre_searches
                    elif avg_tempo > 140:
                        genre_searches = ["fast songs", "electronic", "dance"] + genre_searches
                    
                    for search_term in genre_searches[:3]:
                        try:
                            genre_results = search_tracks(sp, search_term, limit=4)
                            for track in genre_results:
                                if track["id"] not in existing_ids and len(suggestions) < 15:
                                    suggestions.append({
                                        "id": track["id"],
                                        "name": track["name"],
                                        "artist": track["artists"][0]["name"],
                                        "preview_url": track.get("preview_url"),
                                        "strategy": "Genre Match",
                                        "popularity": track.get("popularity", 0)
                                    })
                                    existing_ids.add(track["id"])
                        except Exception as e:
                            continue
                    
                    if len([s for s in suggestions if s["strategy"] == "Genre Match"]) > 0:
                        strategies_used.append("Genre Matching")
                        
            except Exception as e:
                logging.warning(f"Audio features strategy failed: {str(e)}")

        # Strategy 4: Popular tracks in similar style
        if len(suggestions) < 10:
            try:
                genre_searches = ["pop hits", "trending music", "indie favorites", "electronic dance"]
                for search_term in genre_searches[:2]:  # Limit to avoid too many API calls
                    try:
                        popular_results = search_tracks(sp, search_term, limit=5)
                        for track in popular_results:
                            if track["id"] not in existing_ids and len(suggestions) < 15:
                                suggestions.append({
                                    "id": track["id"],
                                    "name": track["name"],
                                    "artist": track["artists"][0]["name"],
                                    "preview_url": track.get("preview_url"),
                                    "strategy": "Popular Music",
                                    "popularity": track.get("popularity", 0)
                                })
                                existing_ids.add(track["id"])
                    except Exception as e:
                        continue
                        
                if len([s for s in suggestions if s["strategy"] == "Popular Music"]) > 0:
                    strategies_used.append("Popular Tracks")
                    
            except Exception as e:
                logging.warning(f"Popular search failed: {str(e)}")

        # Sort suggestions by preview availability and popularity
        suggestions.sort(key=lambda x: (
            x.get("preview_url") is not None,  # Preview tracks first
            x.get("popularity", 0),            # Then by popularity
            x.get("name", "").lower()          # Then alphabetically
        ), reverse=True)
        
        # Limit to top 8 suggestions
        suggestions = suggestions[:8]
        preview_count = sum(1 for s in suggestions if s.get("preview_url"))
        
        total_found = len(suggestions)
        logging.info(f"Smart transition found {total_found} suggestions ({preview_count} with previews) using strategies: {strategies_used}")

        return {
            "suggestions": suggestions,
            "strategies_used": strategies_used,
            "total_found": total_found,
            "preview_count": preview_count
        }

    except Exception as e:
        logging.error(f"Smart transition algorithm error: {str(e)}")
        return {"error": f"Smart transition failed: {str(e)}"}, 500

def basic_transition_algorithm(sp, track_ids):
    """
    Basic transition algorithm using search-based approach
    (Fallback for when Spotify recommendations API is not available)
    """
    try:
        if len(track_ids) != 2:
            return {"error": "Please provide exactly 2 track IDs"}, 400

        logging.info("Using search-based basic transition (recommendations API not available)")
        
        # Get track details
        try:
            track1 = sp.track(track_ids[0])
            track2 = sp.track(track_ids[1])
        except Exception as e:
            logging.error(f"Failed to fetch track details: {str(e)}")
            return {"error": "Could not fetch track details"}, 500

        suggestions = []
        existing_ids = set(track_ids)

        # Strategy 1: Search by artists
        try:
            artist1_name = track1["artists"][0]["name"]
            artist2_name = track2["artists"][0]["name"]
            
            # Search for tracks by both artists
            for artist_name in [artist1_name, artist2_name]:
                search_results = search_tracks(sp, f"artist:{artist_name}", limit=5)
                for track in search_results:
                    if track["id"] not in existing_ids and len(suggestions) < 8:
                        suggestions.append({
                            "id": track["id"],
                            "name": track["name"],
                            "artist": track["artists"][0]["name"],
                            "preview_url": track.get("preview_url")
                        })
                        existing_ids.add(track["id"])
        except Exception as e:
            logging.warning(f"Artist search failed: {str(e)}")

        # Strategy 2: Search by genre/style keywords
        if len(suggestions) < 8:
            try:
                # Extract keywords from track names for genre guessing
                track1_words = track1["name"].lower().split()
                track2_words = track2["name"].lower().split()
                
                # Common genre keywords to search for
                genre_keywords = ["pop", "rock", "dance", "electronic", "indie", "hip hop"]
                
                for keyword in genre_keywords[:3]:  # Limit to avoid too many API calls
                    search_results = search_tracks(sp, keyword, limit=3)
                    for track in search_results:
                        if track["id"] not in existing_ids and len(suggestions) < 8:
                            suggestions.append({
                                "id": track["id"],
                                "name": track["name"],
                                "artist": track["artists"][0]["name"],
                                "preview_url": track.get("preview_url")
                            })
                            existing_ids.add(track["id"])
            except Exception as e:
                logging.warning(f"Genre search failed: {str(e)}")

        # Strategy 3: Popular tracks fallback
        if len(suggestions) < 6:
            try:
                popular_searches = ["top hits", "viral songs", "trending now"]
                for search_term in popular_searches[:2]:
                    search_results = search_tracks(sp, search_term, limit=3)
                    for track in search_results:
                        if track["id"] not in existing_ids and len(suggestions) < 8:
                            suggestions.append({
                                "id": track["id"],
                                "name": track["name"],
                                "artist": track["artists"][0]["name"],
                                "preview_url": track.get("preview_url")
                            })
                            existing_ids.add(track["id"])
            except Exception as e:
                logging.warning(f"Popular search failed: {str(e)}")

        # Sort by preview availability
        suggestions.sort(key=lambda x: x.get("preview_url") is not None, reverse=True)
        
        logging.info(f"Basic transition found {len(suggestions)} suggestions using search-based approach")
        return {"suggestions": suggestions[:8]}  # Limit to 8 suggestions
        
    except Exception as e:
        logging.error(f"Basic transition algorithm error: {str(e)}")
        return {"error": f"Basic transition failed: {str(e)}"}, 500
