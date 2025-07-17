import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import ast
from flask import Flask, request, jsonify
import pickle
import os

app = Flask(__name__)

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
        for i in ast.literal_eval(ob):
            lis.append(i['name'])
        return lis

    def topcast(ob):
        lis = []
        for i in ast.literal_eval(ob)[:3]:
            lis.append(i['name'])
        return lis

    def director(ob):
        lis = []
        for i in ast.literal_eval(ob):
            if i['job'] == "Director":
                lis.append(i['name'])
        return lis

    movs['genres'] = movs['genres'].apply(convert)
    movs['keywords'] = movs['keywords'].apply(convert)
    movs['cast'] = movs['cast'].apply(topcast)
    movs['crew'] = movs['crew'].apply(director)

    movs['tags'] = movs['genres'] + movs['keywords'] + movs['cast'] + movs['crew']
    movs['tags'] = movs['tags'].apply(lambda x: " ".join(x))
    
    return movs

# Initialize recommendation system
def initialize_recommender(movs):
    tfid = TfidfVectorizer(stop_words="english")
    fitter = tfid.fit_transform(movs["tags"])
    cos = cosine_similarity(fitter, fitter)
    return tfid, cos

# Check if preprocessed data exists
if os.path.exists('preprocessed_data.pkl'):
    with open('preprocessed_data.pkl', 'rb') as f:
        movs = pickle.load(f)
    tfid, cos = initialize_recommender(movs)
else:
    movs = load_and_preprocess_data()
    tfid, cos = initialize_recommender(movs)
    with open('preprocessed_data.pkl', 'wb') as f:
        pickle.dump(movs, f)

# Recommendation function
def get_recommendations(movie, movs, cos):
    try:
        idx = movs[movs["title"] == movie].index[0]
    except IndexError:
        return None
    
    sim_scores = list(enumerate(cos[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    sim_scores = sim_scores[1:11]
    movie_indices = [i[0] for i in sim_scores]
    return movs['title'].iloc[movie_indices].tolist()

# API Endpoints
@app.route('/recommend', methods=['GET'])
def recommend():
    movie_title = request.args.get('title')
    if not movie_title:
        return jsonify({"error": "Please provide a movie title"}), 400
    
    recommendations = get_recommendations(movie_title, movs, cos)
    if recommendations is None:
        return jsonify({"error": "Movie not found in database"}), 404
    
    return jsonify({
        "movie": movie_title,
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)