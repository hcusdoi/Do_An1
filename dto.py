from pydantic import BaseModel
from typing import Optional, List, Any

class UserDTO(BaseModel):
    id: int
    username: str
    email: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    role: str
    is_new_user: int
    created_at: str
    last_login: Optional[str] = None

class UserWithPasswordDTO(UserDTO):
    password_hash: str

class MovieDTO(BaseModel):
    movie_id: int
    title: str
    year: Optional[int] = None
    genres: Optional[str] = None
    avg_rating: float = 0.0
    num_ratings: int = 0
    poster_url: Optional[str] = None
    overview: Optional[str] = None

class RatingDTO(BaseModel):
    id: int
    user_id: int
    movie_id: int
    rating: float
    created_at: str

class AuthResultDTO(BaseModel):
    ok: bool
    user: Optional[UserDTO] = None
    error: Optional[str] = None
