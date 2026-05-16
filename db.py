"""
db.py - Database helper cho Movie Recommender Web App
Cung cap cac ham CRUD don gian cho tat ca cac tinh nang web.

Cach dung:
    from db import DB
    db = DB()
    user = db.login('alice', 'alice123')
    db.close()
"""
import sqlite3
import hashlib
import json
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

DB_PATH = os.path.join(os.path.dirname(__file__), 'app.db')


def _hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


class DB:
    def __init__(self, path: str = DB_PATH):
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row          # tra ve dict-like rows
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.execute("PRAGMA journal_mode = WAL")

    def close(self):
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    # ------------------------------------------------------------------
    # AUTH
    # ------------------------------------------------------------------
    def register(self, username: str, email: str, password: str,
                 display_name: str = None) -> Dict:
        """
        Dang ki nguoi dung moi.
        Tra ve {'ok': True, 'user': {...}} hoac {'ok': False, 'error': '...'}
        """
        display_name = display_name or username
        try:
            cur = self.conn.execute("""
                INSERT INTO users (username, email, password_hash, display_name)
                VALUES (?,?,?,?)
            """, (username.strip(), email.strip().lower(),
                  _hash(password), display_name))
            self.conn.commit()
            return {'ok': True, 'user': self.get_user_by_id(cur.lastrowid)}
        except sqlite3.IntegrityError as e:
            err = 'Username da ton tai' if 'username' in str(e).lower() else 'Email da ton tai'
            return {'ok': False, 'error': err}

    def login(self, username: str, password: str) -> Optional[Dict]:
        """
        Dang nhap. Tra ve dict user neu thanh cong, None neu sai.
        """
        row = self.conn.execute("""
            SELECT * FROM users WHERE username = ? COLLATE NOCASE
        """, (username,)).fetchone()

        if row and row['password_hash'] == _hash(password):
            self.conn.execute("""
                UPDATE users SET last_login = datetime('now','localtime') WHERE id = ?
            """, (row['id'],))
            self.conn.commit()
            return dict(row)
        return None

    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        row = self.conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        return dict(row) if row else None

    def update_profile(self, user_id: int, display_name: str = None,
                       avatar_url: str = None) -> bool:
        if display_name:
            self.conn.execute("UPDATE users SET display_name=? WHERE id=?",
                              (display_name, user_id))
        if avatar_url:
            self.conn.execute("UPDATE users SET avatar_url=? WHERE id=?",
                              (avatar_url, user_id))
        self.conn.commit()
        return True

    def change_password(self, user_id: int, old_pw: str, new_pw: str) -> bool:
        row = self.conn.execute("SELECT password_hash FROM users WHERE id=?",
                                (user_id,)).fetchone()
        if row and row['password_hash'] == _hash(old_pw):
            self.conn.execute("UPDATE users SET password_hash=? WHERE id=?",
                              (_hash(new_pw), user_id))
            self.conn.commit()
            return True
        return False

    # ------------------------------------------------------------------
    # MOVIES
    # ------------------------------------------------------------------
    def get_movies(self, limit: int = 50, offset: int = 0,
                   genre: str = None, search: str = None,
                   sort_by: str = 'num_ratings') -> List[Dict]:
        """Lay danh sach phim, co the loc theo the loai / tu khoa."""
        q = "SELECT * FROM movies WHERE 1=1"
        params: List[Any] = []
        if genre:
            q += " AND genres LIKE ?"
            params.append(f'%{genre}%')
        if search:
            q += " AND title LIKE ?"
            params.append(f'%{search}%')
        safe_sort = sort_by if sort_by in ('num_ratings','avg_rating','title','year') else 'num_ratings'
        q += f" ORDER BY {safe_sort} DESC LIMIT ? OFFSET ?"
        params += [limit, offset]
        rows = self.conn.execute(q, params).fetchall()
        return [dict(r) for r in rows]

    def get_movie_by_id(self, movie_id: int) -> Optional[Dict]:
        row = self.conn.execute("SELECT * FROM movies WHERE movie_id=?",
                                (movie_id,)).fetchone()
        return dict(row) if row else None

    def search_movies(self, query: str, limit: int = 20) -> List[Dict]:
        rows = self.conn.execute("""
            SELECT * FROM movies WHERE title LIKE ? ORDER BY num_ratings DESC LIMIT ?
        """, (f'%{query}%', limit)).fetchall()
        return [dict(r) for r in rows]

    def get_popular_movies(self, limit: int = 20, genre: str = None) -> List[Dict]:
        q = "SELECT * FROM movies WHERE num_ratings > 0"
        params: List[Any] = []
        if genre:
            q += " AND genres LIKE ?"
            params.append(f'%{genre}%')
        q += " ORDER BY num_ratings DESC LIMIT ?"
        params.append(limit)
        return [dict(r) for r in self.conn.execute(q, params).fetchall()]

    def get_all_genres(self) -> List[str]:
        """Lay danh sach tat ca the loai."""
        rows = self.conn.execute("SELECT DISTINCT genres FROM movies WHERE genres IS NOT NULL").fetchall()
        genres = set()
        for row in rows:
            for g in row['genres'].split(','):
                g = g.strip()
                if g:
                    genres.add(g)
        return sorted(genres)

    # ------------------------------------------------------------------
    # RATINGS
    # ------------------------------------------------------------------
    def rate_movie(self, user_id: int, movie_id: int, rating: float) -> bool:
        """Them hoac cap nhat rating. Tra ve True neu thanh cong."""
        if not (0.5 <= rating <= 5.0):
            return False
        self.conn.execute("""
            INSERT INTO ratings (user_id, movie_id, rating)
            VALUES (?,?,?)
            ON CONFLICT(user_id, movie_id) DO UPDATE SET rating=excluded.rating,
                created_at=datetime('now','localtime')
        """, (user_id, movie_id, rating))
        # Cap nhat is_new_user = 0 sau khi co rating dau tien
        self.conn.execute("UPDATE users SET is_new_user=0 WHERE id=?", (user_id,))
        # Xoa cache vi ratings thay doi
        self.conn.execute("DELETE FROM recommendations_cache WHERE user_id=?", (user_id,))
        self.conn.commit()
        return True

    def delete_rating(self, user_id: int, movie_id: int) -> bool:
        self.conn.execute("DELETE FROM ratings WHERE user_id=? AND movie_id=?",
                          (user_id, movie_id))
        self.conn.commit()
        return True

    def get_user_ratings(self, user_id: int) -> List[Dict]:
        """Lay tat ca ratings cua mot user, kem thong tin phim."""
        rows = self.conn.execute("""
            SELECT r.*, m.title, m.genres, m.avg_rating, m.poster_url
            FROM ratings r
            JOIN movies m ON m.movie_id = r.movie_id
            WHERE r.user_id = ?
            ORDER BY r.created_at DESC
        """, (user_id,)).fetchall()
        return [dict(r) for r in rows]

    def get_movie_ratings(self, movie_id: int, limit: int = 20) -> List[Dict]:
        rows = self.conn.execute("""
            SELECT r.rating, r.created_at, u.display_name, u.avatar_url
            FROM ratings r
            JOIN users u ON u.id = r.user_id
            WHERE r.movie_id = ?
            ORDER BY r.created_at DESC LIMIT ?
        """, (movie_id, limit)).fetchall()
        return [dict(r) for r in rows]

    def get_user_rating_for_movie(self, user_id: int, movie_id: int) -> Optional[float]:
        row = self.conn.execute("""
            SELECT rating FROM ratings WHERE user_id=? AND movie_id=?
        """, (user_id, movie_id)).fetchone()
        return row['rating'] if row else None

    # ------------------------------------------------------------------
    # HISTORY
    # ------------------------------------------------------------------
    def log_action(self, user_id: int, movie_id: int, action: str = 'view'):
        """Ghi lai hanh dong (view/click/rate/skip)."""
        self.conn.execute("""
            INSERT INTO user_history (user_id, movie_id, action)
            VALUES (?,?,?)
        """, (user_id, movie_id, action))
        self.conn.commit()

    def get_user_history(self, user_id: int, limit: int = 50) -> List[Dict]:
        rows = self.conn.execute("""
            SELECT h.*, m.title, m.genres, m.poster_url
            FROM user_history h
            JOIN movies m ON m.movie_id = h.movie_id
            WHERE h.user_id = ?
            ORDER BY h.created_at DESC LIMIT ?
        """, (user_id, limit)).fetchall()
        return [dict(r) for r in rows]

    def get_recently_viewed_movie_ids(self, user_id: int, limit: int = 20) -> List[int]:
        rows = self.conn.execute("""
            SELECT DISTINCT movie_id FROM user_history
            WHERE user_id=? ORDER BY created_at DESC LIMIT ?
        """, (user_id, limit)).fetchall()
        return [r['movie_id'] for r in rows]

    # ------------------------------------------------------------------
    # WATCHLIST
    # ------------------------------------------------------------------
    def add_to_watchlist(self, user_id: int, movie_id: int) -> bool:
        try:
            self.conn.execute("""
                INSERT INTO watchlist (user_id, movie_id) VALUES (?,?)
            """, (user_id, movie_id))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False  # da co trong watchlist

    def remove_from_watchlist(self, user_id: int, movie_id: int) -> bool:
        self.conn.execute("DELETE FROM watchlist WHERE user_id=? AND movie_id=?",
                          (user_id, movie_id))
        self.conn.commit()
        return True

    def get_watchlist(self, user_id: int) -> List[Dict]:
        rows = self.conn.execute("""
            SELECT w.added_at, m.*
            FROM watchlist w
            JOIN movies m ON m.movie_id = w.movie_id
            WHERE w.user_id = ?
            ORDER BY w.added_at DESC
        """, (user_id,)).fetchall()
        return [dict(r) for r in rows]

    def is_in_watchlist(self, user_id: int, movie_id: int) -> bool:
        row = self.conn.execute("""
            SELECT 1 FROM watchlist WHERE user_id=? AND movie_id=?
        """, (user_id, movie_id)).fetchone()
        return row is not None

    # ------------------------------------------------------------------
    # USER GENRE PREFERENCES (Cold Start)
    # ------------------------------------------------------------------
    def set_genre_preferences(self, user_id: int, genres: List[str]):
        """Set so thich the loai sau khi dang ki (cold start onboarding)."""
        self.conn.execute("DELETE FROM user_genres WHERE user_id=?", (user_id,))
        for i, genre in enumerate(genres):
            weight = 1.5 - i * 0.1  # genre dau tien quan trong nhat
            self.conn.execute("""
                INSERT INTO user_genres (user_id, genre, weight) VALUES (?,?,?)
            """, (user_id, genre, max(0.5, weight)))
        # Xoa cache
        self.conn.execute("DELETE FROM recommendations_cache WHERE user_id=?", (user_id,))
        self.conn.commit()

    def get_genre_preferences(self, user_id: int) -> List[Dict]:
        rows = self.conn.execute("""
            SELECT genre, weight FROM user_genres
            WHERE user_id=? ORDER BY weight DESC
        """, (user_id,)).fetchall()
        return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # RECOMMENDATIONS CACHE
    # ------------------------------------------------------------------
    def save_recommendations(self, user_id: int, method: str,
                              results: List[Dict], ttl_hours: int = 24):
        """Luu ket qua goi y vao cache."""
        expires = (datetime.now() + timedelta(hours=ttl_hours)).strftime('%Y-%m-%d %H:%M:%S')
        self.conn.execute("""
            INSERT INTO recommendations_cache (user_id, method, results, expires_at)
            VALUES (?,?,?,?)
            ON CONFLICT(user_id, method) DO UPDATE SET
                results=excluded.results,
                created_at=datetime('now','localtime'),
                expires_at=excluded.expires_at
        """, (user_id, method, json.dumps(results, ensure_ascii=False), expires))
        self.conn.commit()

    def get_cached_recommendations(self, user_id: int, method: str) -> Optional[List[Dict]]:
        """Lay cache neu con han. Tra ve None neu het han hoac chua co."""
        row = self.conn.execute("""
            SELECT results, expires_at FROM recommendations_cache
            WHERE user_id=? AND method=?
        """, (user_id, method)).fetchone()
        if not row:
            return None
        if row['expires_at'] and datetime.now().strftime('%Y-%m-%d %H:%M:%S') > row['expires_at']:
            return None  # het han
        return json.loads(row['results'])

    def invalidate_cache(self, user_id: int):
        """Xoa cache khi user rating moi."""
        self.conn.execute("DELETE FROM recommendations_cache WHERE user_id=?", (user_id,))
        self.conn.commit()

    # ------------------------------------------------------------------
    # STATS (cho trang admin)
    # ------------------------------------------------------------------
    def get_stats(self) -> Dict:
        stats = {}
        for table, col in [('users','id'),('movies','movie_id'),
                            ('ratings','id'),('watchlist','id')]:
            row = self.conn.execute(f"SELECT COUNT({col}) FROM {table}").fetchone()
            stats[f'total_{table}'] = row[0]
        # Top rated movies
        rows = self.conn.execute("""
            SELECT m.title, m.avg_rating, m.num_ratings
            FROM movies m
            WHERE m.num_ratings > 50
            ORDER BY m.avg_rating DESC LIMIT 5
        """).fetchall()
        stats['top_movies'] = [dict(r) for r in rows]
        # Most active users
        rows = self.conn.execute("""
            SELECT u.username, u.display_name, COUNT(r.id) as rating_count
            FROM users u LEFT JOIN ratings r ON r.user_id = u.id
            GROUP BY u.id ORDER BY rating_count DESC LIMIT 5
        """).fetchall()
        stats['active_users'] = [dict(r) for r in rows]
        return stats

    # ------------------------------------------------------------------
    # UTILITY
    # ------------------------------------------------------------------
    def get_rated_movie_ids(self, user_id: int) -> List[int]:
        """Lay danh sach movieId ma user da danh gia (de loai khoi goi y)."""
        rows = self.conn.execute("""
            SELECT movie_id FROM ratings WHERE user_id=?
        """, (user_id,)).fetchall()
        return [r['movie_id'] for r in rows]

    def get_all_movie_ids(self) -> List[int]:
        rows = self.conn.execute("SELECT movie_id FROM movies").fetchall()
        return [r['movie_id'] for r in rows]

    def user_exists(self, username: str) -> bool:
        row = self.conn.execute(
            "SELECT 1 FROM users WHERE username=? COLLATE NOCASE", (username,)).fetchone()
        return row is not None
