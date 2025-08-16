# Spotify Transition Songs

A Flask web application for searching Spotify tracks, previewing songs, and generating smooth playlist transitions using smart algorithms.

## Features
- **Search Tracks:** Find tracks on Spotify by name, artist, or keyword.
- **Popular Tracks:** Aggressively fetch popular tracks with preview URLs for instant listening.
- **Track Features:** View audio features (tempo, energy, etc.) for any track.
- **Transition Algorithms:** Generate recommendations for smooth transitions between two songs using basic and smart algorithms.
- **Playlist Preview:** Simulate playlist transitions and preview tracks.
- **Track Settings:** Save and retrieve custom settings for tracks (tempo, energy, notes, etc.).

## Main Files
- `spotify.py`: Main Flask app, API endpoints, and core logic.
- `spotify_client.py`: Spotify API authentication and helper functions.
- `transition_algorithms.py`: Smart and basic transition recommendation algorithms.
- `database.py`: SQLite database for storing track settings.
- `secretgenerator.py`: Utility for generating secrets.
- `requirements.txt`: Python dependencies.

## Templates & Static
- `templates/`: HTML templates for UI (`base.html`, `home.html`, `search.html`, `playlists.html`, `playlist_tracks.html`).
- `static/style.css`: Main stylesheet.

## Setup
1. **Clone the repository**
2. **Install dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```
3. **Set up environment variables:**
   - Create a `.env` file with your Spotify API credentials:
     ```env
     CLIENT_ID=your_spotify_client_id
     CLIENT_SECRET=your_spotify_client_secret
     ```
4. **Run the app:**
   ```powershell
   python spotify.py
   ```
   The app will start on `http://localhost:5001`

## API Endpoints
- `/api/search_tracks?query=...` — Search for tracks
- `/api/popular_tracks` — Get popular tracks with previews
- `/api/track_features/<track_id>` — Get audio features for a track
- `/api/basic_recommendations` — Get basic transition recommendations (POST)
- `/api/smart_recommendations` — Get smart transition recommendations (POST)
- `/api/playlist_preview` — Preview playlist transitions (POST)
- `/api/save_settings` — Save track settings (POST)
- `/api/get_settings/<track_id>` — Get saved settings for a track

## Database
- Uses SQLite (`settings.db`) to store track settings and user data.

## License
MIT

---
**Author:** Nanda8555
