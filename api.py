from fastapi import FastAPI, Query
from typing import Optional
from bll import BLL
import uvicorn
import pandas as pd

app = FastAPI(title="Movie Recommendation API")

@app.get("/")
def home():
    return {"message": "Movie Recommendation API is running!"}

@app.get("/movies")
def search_movies(query: str = Query(None), limit: int = 50):
    with BLL() as db:
        movies = db.get_movies(limit=limit, search=query)
        df = pd.DataFrame(movies)
    if df.empty:
        return []
    if query:
        df = df[df['title'].str.contains(query, case=False, na=False)]
    
    df = df.head(limit)
    if 'genres_clean' in df.columns:
        df['genres_clean'] = df['genres_clean'].apply(lambda x: ', '.join(x) if isinstance(x, list) else str(x))
    
    return df.to_dict(orient="records")

@app.get("/recommend")
def recommend(user_id: Optional[int] = Query(None), movie_id: Optional[int] = Query(None), top_n: int = 10):
    if user_id is None and movie_id is None:
        return {"error": "Cần cung cấp user_id hoặc movie_id"}
        
    with BLL() as db:
        df = db.get_hybrid_recommendations(user_id=user_id, movie_id=movie_id, top_n=top_n)
    
    if df is None or df.empty:
        return []
        
    if 'genres_clean' in df.columns:
        df['genres_clean'] = df['genres_clean'].apply(lambda x: ', '.join(x) if isinstance(x, list) else str(x))
        
    return df.to_dict(orient="records")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
