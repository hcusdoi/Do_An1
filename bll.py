import hashlib
import pandas as pd
# pyrefly: ignore [missing-import]
from dal import DAL
from dto import UserDTO, AuthResultDTO
from typing import Optional, List, Dict, Any
from recommender import MovieRecommender

print("Dang nap mo hinh goi y... (co the mat 10-30 giay)")
try:
    _rec_instance = MovieRecommender()
    print("Mo hinh da san sang!")
except Exception as e:
    print(f"BLL Warning: Khong nap duoc mo hinh - {e}")
    _rec_instance = None

def _hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

class BLL:
    def __init__(self):
        self.dal = DAL()

    def close(self):
        self.dal.close()

    def __enter__(self):
        self.dal.__enter__()
        return self

    def __exit__(self, *_):
        self.dal.__exit__(*_)

    def register(self, username: str, email: str, password: str, display_name: str = None) -> AuthResultDTO:
        display_name = display_name or username
        password_hash = _hash(password)
        
        if self.dal.get_user_by_username(username):
            return AuthResultDTO(ok=False, error="Username đã tồn tại")
        if self.dal.get_user_by_email(email):
            return AuthResultDTO(ok=False, error="Email đã tồn tại")
            
        user_dict = self.dal.create_user(username, email, password_hash, display_name)
        if user_dict:
            return AuthResultDTO(ok=True, user=UserDTO(**user_dict))
        return AuthResultDTO(ok=False, error="Không thể tạo tài khoản")

    def login(self, username: str, password: str) -> Optional[UserDTO]:
        user_dict = self.dal.get_user_by_username(username)
        if user_dict and user_dict['password_hash'] == _hash(password):
            self.dal.update_last_login(user_dict['id'])
            return UserDTO(**user_dict)
        return None

    def get_movies(self, limit: int = 50, offset: int = 0, genre: str = None, search: str = None, sort_by: str = 'num_ratings') -> List[Dict]:
        return self.dal.get_movies(limit, offset, genre, search, sort_by)
        
    def get_popular_movies(self, limit: int = 20, genre: str = None) -> List[Dict]:
        return self.dal.get_popular_movies(limit, genre)
        
    def get_all_genres(self) -> List[str]:
        return self.dal.get_all_genres()
        
    def set_genre_preferences(self, user_id: int, genres: List[str]):
        self.dal.set_genre_preferences(user_id, genres)
        
    def get_cached_recommendations(self, user_id: int, method: str) -> Optional[List[Dict]]:
        return self.dal.get_cached_recommendations(user_id, method)
        
    def get_user_ratings(self, user_id: int) -> List[Dict]:
        return self.dal.get_user_ratings(user_id)
        
    def save_recommendations(self, user_id: int, method: str, results: List[Dict]):
        self.dal.save_recommendations(user_id, method, results)
        
    def get_movie_by_id(self, movie_id: int) -> Optional[Dict]:
        return self.dal.get_movie_by_id(movie_id)
        
    def get_movie_ratings(self, movie_id: int, limit: int = 10) -> List[Dict]:
        return self.dal.get_movie_ratings(movie_id, limit)
        
    def get_user_rating_for_movie(self, user_id: int, movie_id: int) -> Optional[float]:
        return self.dal.get_user_rating_for_movie(user_id, movie_id)
        
    def is_in_watchlist(self, user_id: int, movie_id: int) -> bool:
        return self.dal.is_in_watchlist(user_id, movie_id)
        
    def log_action(self, user_id: int, movie_id: int, action: str):
        self.dal.log_action(user_id, movie_id, action)
        
    def get_watchlist(self, user_id: int) -> List[Dict]:
        return self.dal.get_watchlist(user_id)
        
    def get_genre_preferences(self, user_id: int) -> List[Dict]:
        return self.dal.get_genre_preferences(user_id)
        
    def get_user_history(self, user_id: int, limit: int = 10) -> List[Dict]:
        return self.dal.get_user_history(user_id, limit)
        
    def rate_movie(self, user_id: int, movie_id: int, rating: float) -> bool:
        return self.dal.rate_movie(user_id, movie_id, rating)
        
    def remove_from_watchlist(self, user_id: int, movie_id: int) -> bool:
        return self.dal.remove_from_watchlist(user_id, movie_id)
        
    def add_to_watchlist(self, user_id: int, movie_id: int) -> bool:
        return self.dal.add_to_watchlist(user_id, movie_id)
        
    def search_movies(self, q: str, limit: int = 10) -> List[Dict]:
        return self.dal.search_movies(q, limit)
        
    def get_hybrid_recommendations(self, user_id=None, movie_id=None, top_n=10, cf_weight=0.7) -> Optional[pd.DataFrame]:
        if not _rec_instance:
            return None
        return _rec_instance.get_hybrid_recommendations(user_id=user_id, movie_id=movie_id, top_n=top_n, cf_weight=cf_weight)
        
    def get_conn(self):
        # Fallback if someone accesses conn directly
        return self.dal.conn
