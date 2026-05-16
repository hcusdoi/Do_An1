import joblib
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

class MovieRecommender:
    def __init__(self):
        print("Dang khoi dong mo hinh...")
        cf = joblib.load('cf_custom_model.pkl')
        self.P = cf['P']; self.Q = cf['Q']
        self.b_u = cf['b_u']; self.b_i = cf['b_i']; self.mu = cf['mu']
        self.user2idx = cf['user2idx']
        self.movie2idx = cf['movie2idx']
        self.idx2movie = cf['idx2movie']
        self.cbf_matrix = joblib.load('cbf_tfidf_matrix.pkl')
        self.db = joblib.load('movie_database.pkl')
        self.db_idx = pd.Series(self.db.index, index=self.db['movieId']).drop_duplicates()
        print("Mo hinh san sang!")

    def _predict(self, u_idx, i_idx):
        return self.mu + self.b_u[u_idx] + self.b_i[i_idx] + np.dot(self.P[u_idx], self.Q[i_idx])

    def get_cf_recommendations(self, user_id, top_n=10):
        if user_id not in self.user2idx:
            return pd.DataFrame()
        u = self.user2idx[user_id]
        
        preds = self.mu + self.b_u[u] + self.b_i + np.dot(self.Q, self.P[u])
        top_idx = np.argsort(preds)[::-1][:top_n]
        top_ids = [self.idx2movie[i] for i in top_idx]
        
        res = self.db[self.db['movieId'].isin(top_ids)].copy()
        res['Score'] = [round(preds[i], 2) for i in top_idx]
        return res.set_index('movieId').loc[top_ids].reset_index()

    def get_cbf_recommendations(self, movie_id, top_n=10):
        if movie_id not in self.db_idx:
            return pd.DataFrame()
        idx = self.db_idx[movie_id]
        sim = cosine_similarity(self.cbf_matrix[idx], self.cbf_matrix).flatten()
        top = sim.argsort()[-(top_n+1):][::-1][1:]
        res = self.db.iloc[top].copy()
        res['Similarity'] = [round(sim[i]*100, 1) for i in top]
        return res

    def get_hybrid_recommendations(self, user_id=None, movie_id=None, top_n=10, cf_weight=0.7):
        cbf_weight = 1.0 - cf_weight
        
        if user_id is None or user_id not in self.user2idx:
            if movie_id is not None:
                return self.get_cbf_recommendations(movie_id, top_n)
            return pd.DataFrame()
            
        u = self.user2idx[user_id]
        
        # Điểm CF
        cf_scores = self.mu + self.b_u[u] + self.b_i + np.dot(self.Q, self.P[u])
        cf_min, cf_max = cf_scores.min(), cf_scores.max()
        cf_norm = (cf_scores - cf_min) / (cf_max - cf_min + 1e-8)
        
        # Điểm CBF
        cbf_scores = np.zeros(len(self.db))
        if movie_id and movie_id in self.db_idx:
            idx = self.db_idx[movie_id]
            cbf_scores = cosine_similarity(self.cbf_matrix[idx], self.cbf_matrix).flatten()
            
        min_len = min(len(cf_norm), len(cbf_scores))
        hybrid = cf_weight * cf_norm[:min_len] + cbf_weight * cbf_scores[:min_len]
        
        top_idx = np.argsort(hybrid)[::-1][:top_n]
        res = self.db.iloc[top_idx].copy()
        res['CF_Score'] = [round(cf_norm[i], 3) for i in top_idx]
        res['CBF_Score'] = [round(cbf_scores[i], 3) for i in top_idx]
        res['Hybrid_Score'] = [round(hybrid[i], 3) for i in top_idx]
        return res
