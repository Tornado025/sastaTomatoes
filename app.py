import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import ast
from flask import Flask, request, jsonify, send_from_directory, render_template
import pickle
import os
from flask_cors import CORS
from difflib import get_close_matches
from fuzzywuzzy import fuzz, process

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)  # Enable CORS for all routes

def read_csv_basic(file_name):
    try:
        return pd.read_csv(file_name)
    except FileNotFoundError:
        print(f"Error: Could not find '{file_name}' in the current directory.")
        print("Please make sure:")
        print(f"1. The file '{file_name}' exists")
        print("2. You're running the script from the correct directory")
        exit(1)

# Load and preprocess data
def load_and_preprocess_data():
    creds = read_csv_basic(r"D:\CODING\Microsoft VS Code\VISUAL STUDIO CODE\Python\ML\Unsupervised Learning\Recommender System\tmdb_5000_credits.csv")
    movs = read_csv_basic(r"D:\CODING\Microsoft VS Code\VISUAL STUDIO CODE\Python\ML\Unsupervised Learning\Recommender System\tmdb_5000_movies.csv")
    movs = movs.merge(creds, on="title")
    movs = movs[['movie_id', 'title', 'overview', 'genres', 'keywords', 'cast', 'crew', 'runtime']]

    def convert(ob):
        lis = []
        if pd.isna(ob):
            return lis
        for i in ast.literal_eval(ob):
            lis.append(i['name'])
        return lis

    def topcast(ob):
        lis = []
        if pd.isna(ob):
            return lis
        for i in ast.literal_eval(ob)[:3]:
            lis.append(i['name'])
        return lis

    def director(ob):
        lis = []
        if pd.isna(ob):
            return lis
        for i in ast.literal_eval(ob):
            if i['job'] == "Director":
                lis.append(i['name'])
        return lis

    movs['genres'] = movs['genres'].apply(convert)
    movs['keywords'] = movs['keywords'].apply(convert)
    movs['cast'] = movs['cast'].apply(topcast)
    movs['crew'] = movs['crew'].apply(director)

    # Store original cast and crew data for display
    movs['cast_display'] = movs['cast'].apply(lambda x: x if x else [])
    movs['director_display'] = movs['crew'].apply(lambda x: x if x else [])

    movs['tags'] = movs['genres'] + movs['keywords'] + movs['cast'] + movs['crew']
    movs['tags'] = movs['tags'].apply(lambda x: " ".join(x))
    
    return movs

# Initialize recommendation system
def initialize_recommender(movs):
    tfid = TfidfVectorizer(stop_words="english")
    fitter = tfid.fit_transform(movs["tags"])
    cos = cosine_similarity(fitter, fitter)
    return tfid, cos

# Fuzzy matching function
def find_best_movie_match(movie_title, movie_list, threshold=70):
    """Find the best matching movie title using fuzzy matching"""
    match = process.extractOne(movie_title, movie_list, scorer=fuzz.ratio)
    if match and match[1] >= threshold:
        return match[0]
    return None

# Check if preprocessed data exists and force reload to get new columns
force_reload = True  # Set to True to force data reload with new columns

if os.path.exists('preprocessed_data.pkl') and not force_reload:
    try:
        with open('preprocessed_data.pkl', 'rb') as f:
            movs = pickle.load(f)
        # Check if the loaded data has the required columns
        if 'cast_display' not in movs.columns or 'director_display' not in movs.columns:
            print("Old data structure detected. Reprocessing data...")
            raise KeyError("Missing new columns")
        tfid, cos = initialize_recommender(movs)
    except (KeyError, FileNotFoundError):
        movs = load_and_preprocess_data()
        tfid, cos = initialize_recommender(movs)
        with open('preprocessed_data.pkl', 'wb') as f:
            pickle.dump(movs, f)
else:
    print("Loading and preprocessing data...")
    movs = load_and_preprocess_data()
    tfid, cos = initialize_recommender(movs)
    with open('preprocessed_data.pkl', 'wb') as f:
        pickle.dump(movs, f)

# Enhanced recommendation function with detailed movie info
def get_recommendations_with_details(movie, movs, cos):
    # First try exact match
    movie_matches = movs[movs["title"].str.lower() == movie.lower()]
    
    if movie_matches.empty:
        # Try fuzzy matching
        movie_titles = movs['title'].tolist()
        best_match = find_best_movie_match(movie, movie_titles)
        
        if best_match:
            movie_matches = movs[movs["title"] == best_match]
            matched_title = best_match
        else:
            return None, None
    else:
        matched_title = movie_matches.iloc[0]['title']
    
    try:
        idx = movie_matches.index[0]
    except IndexError:
        return None, None
    
    # Get movie details - handle both old and new data structures
    movie_details = {
        'title': movs.iloc[idx]['title'],
        'overview': movs.iloc[idx]['overview'] if pd.notna(movs.iloc[idx]['overview']) else "No overview available",
        'runtime': int(movs.iloc[idx]['runtime']) if pd.notna(movs.iloc[idx]['runtime']) else "Unknown",
        'cast': movs.iloc[idx].get('cast_display', movs.iloc[idx].get('cast', [])),
        'director': movs.iloc[idx].get('director_display', movs.iloc[idx].get('crew', [])),
        'genres': movs.iloc[idx]['genres'] if 'genres' in movs.columns else []
    }
    
    # Get recommendations
    sim_scores = list(enumerate(cos[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    sim_scores = sim_scores[1:11]
    movie_indices = [i[0] for i in sim_scores]
    
    # Get detailed recommendations
    recommendations = []
    for i in movie_indices:
        rec_movie = {
            'title': movs.iloc[i]['title'],
            'overview': movs.iloc[i]['overview'] if pd.notna(movs.iloc[i]['overview']) else "No overview available",
            'runtime': int(movs.iloc[i]['runtime']) if pd.notna(movs.iloc[i]['runtime']) else "Unknown",
            'cast': movs.iloc[i].get('cast_display', movs.iloc[i].get('cast', [])),
            'director': movs.iloc[i].get('director_display', movs.iloc[i].get('crew', [])),
            'genres': movs.iloc[i]['genres'] if 'genres' in movs.columns else []
        }
        recommendations.append(rec_movie)
    
    return movie_details, recommendations

@app.route('/')
def home():
    return render_template('inde.html')

# Add this to serve static files (like prpr.js)
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)

# Enhanced API endpoint for recommendations
@app.route('/recommend', methods=['GET'])
def recommend():
    movie_title = request.args.get('title')
    if not movie_title:
        return jsonify({"error": "Please provide a movie title"}), 400
    
    movie_details, recommendations = get_recommendations_with_details(movie_title, movs, cos)
    if movie_details is None:
        # Suggest similar movies if no match found
        movie_titles = movs['title'].tolist()
        suggestions = get_close_matches(movie_title, movie_titles, n=5, cutoff=0.3)
        return jsonify({
            "error": "Movie not found in database",
            "suggestions": suggestions
        }), 404
    
    return jsonify({
        "searched_movie": movie_details,
        "recommendations": recommendations
    })

@app.route('/movies', methods=['GET'])
def list_movies():
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    
    movies = movs['title'].iloc[start_idx:end_idx].tolist()
    return jsonify({
        "page": page,
        "per_page": per_page,
        "movies": movies,
        "total_movies": len(movs)
    })

# Add search endpoint for autocomplete
@app.route('/search', methods=['GET'])
def search_movies():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({"matches": []})
    
    # Find movies that contain the query (case insensitive)
    matches = movs[movs['title'].str.contains(query, case=False, na=False)]['title'].head(10).tolist()
    
    # If no exact matches, try fuzzy matching
    if not matches:
        movie_titles = movs['title'].tolist()
        fuzzy_matches = process.extract(query, movie_titles, limit=5, scorer=fuzz.partial_ratio)
        matches = [match[0] for match in fuzzy_matches if match[1] > 50]
    
    return jsonify({"matches": matches})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)