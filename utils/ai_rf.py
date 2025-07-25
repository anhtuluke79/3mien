import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import os
import joblib

MODEL_DIR = os.path.join(os.path.dirname(__file__), "../data")  # Thư mục chứa .pkl

def get_model_path(N=7):
    os.makedirs(MODEL_DIR, exist_ok=True)
    return os.path.join(MODEL_DIR, f"rf_xsmb_model_N{N}.pkl")

def preprocess_data(df, N=7):
    df = df.sort_values('date')
    df['DB'] = df['DB'].astype(str).str.zfill(5)
    features = []
    labels = []
    for i in range(N, len(df)):
        prev_daus = [int(df.iloc[i-j]['DB'][-2:]) for j in range(N, 0, -1)]
        features.append(prev_daus)
        labels.append(int(df.iloc[i]['DB'][-2:]))
    return np.array(features), np.array(labels)

def train_model(df, N=7):
    X, y = preprocess_data(df, N)
    if len(X) < 30:
        return None
    clf = RandomForestClassifier(n_estimators=200, random_state=42)
    clf.fit(X, y)
    model_path = get_model_path(N)
    joblib.dump(clf, model_path)
    return clf

def load_model(N=7):
    model_path = get_model_path(N)
    if os.path.exists(model_path):
        return joblib.load(model_path)
    return None

def predict_next(df, N=7, top_k=5, retrain=False):
    model_path = get_model_path(N)
    if retrain or not os.path.exists(model_path):
        clf = train_model(df, N)
    else:
        clf = load_model(N)
        if clf is None:
            clf = train_model(df, N)
    if clf is None:
        return None, f"Không đủ dữ liệu để huấn luyện AI với N={N}."
    if len(df) < N:
        return None, f"Không đủ dữ liệu để dự đoán (N={N})."
    df = df.sort_values('date')
    lastN = [int(df.iloc[-j]['DB'][-2:]) for j in range(N, 0, -1)]
    probas = clf.predict_proba([lastN])[0]
    top_idxs = np.argsort(probas)[-top_k:][::-1]
    dudoan = [f"{idx:02d}" for idx in top_idxs]
    msg = (
        f"🤖 *AI (Random Forest, N={N}) dự đoán dàn số khả năng cao nhất kỳ tới:*\n"
        + ", ".join(dudoan)
        + "\n\n(Lưu ý: Dự đoán mang tính giải trí, không đảm bảo trúng thưởng!)"
    )
    return dudoan, msg
