#This file is just the notebook made into a python file 
import pandas as pd 
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import ast 

def read_csv_basic(file_name):
    try:
        return pd.read_csv(file_name)
    except FileNotFoundError:
        print(f"Error: Could not find '{file_name}' in the current directory.")
        print("Please make sure:")
        print(f"1. The file '{file_name}' exists")
        print("2. You're running the script from the correct directory")
        exit(1)

# Read files
creds = read_csv_basic("tmdb_5000_credits.csv")
movs = read_csv_basic("tmdb_5000_movies.csv")
#Use absolute file paths while tagging to csv or else gives a file not found error 
movs=movs.merge(creds,on="title")
movs= movs[['movie_id','title','overview','genres','keywords','cast','crew','runtime']]

# FUNCTIONS FOR CONVERTING DATAFRAME TO LIST OF DICTIONARIES  
def convert(ob):
    lis=[]
    for i in ast.literal_eval(ob):
        lis.append(i['name'])
    return lis

def topcast(ob):
    lis=[]
    for i in ast.literal_eval(ob)[:3]:
        lis.append(i['name'])
    return lis

def director(ob):
    lis=[]
    for i in ast.literal_eval(ob):
        if(i['job']=="Director"):
            lis.append(i['name'])
    return lis

movs['genres']=movs['genres'].apply(convert)
movs['keywords']=movs['keywords'].apply(convert)
movs['cast']=movs['cast'].apply(topcast)
movs['crew']=movs['crew'].apply(director)

movs['tags']=movs['genres']+movs['keywords']+movs['cast']+movs['crew']
movs['tags']=movs['tags'].apply(lambda x: " ".join(x))

# To build the recommender system we use TFID Vectoriser and cosine similarity
# TFID Vectoriser detects the occurence of the word in dataset and this is represented as a score 
# Cosine similarity matches the dots to build the recommender system using content-based filtering

tfid=TfidfVectorizer(stop_words="english")
#This avoids count of all commonly used words in English 
fitter=tfid.fit_transform(movs["tags"])

cos=cosine_similarity(fitter,fitter)

def getrecommend(movie,sim=cos):
    res=list(enumerate(cos[movs[movs["title"]==movie].index[0]]))
    res=sorted(res,key=lambda x: x[1], reverse=True)
    res=res[1:11]
    listindi=[]
    for i in res:
        listindi.append(i[0])
    return movs['title'].iloc[listindi]

print(getrecommend('Avatar'))
