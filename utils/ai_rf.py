import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import os
import joblib

MODEL_PATH = "rf_xsmb_model.pkl"

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
    joblib.dump(clf, MODEL_PATH)
    return clf

def load_model():
    if os.path.exists(MODEL_PATH):
        return joblib.load(MODEL_PATH)
    return None

def predict_next(df, N=7, top_k=5, retrain=False):
    if retrain or not os.path.exists(MODEL_PATH):
        clf = train_model(df, N)
    else:
        clf = load_model()
        if clf is None:
            clf = train_model(df, N)
    if clf is None:
        return None, "Không đủ dữ liệu để huấn luyện AI."
    if len(df) < N:
        return None, "Không đủ dữ liệu để dự đoán."
    df = df.sort_values('date')
    lastN = [int(df.iloc[-j]['DB'][-2:]) for j in range(N, 0, -1)]
    probas = clf.predict_proba([lastN])[0]
    top_idxs = np.argsort(probas)[-top_k:][::-1]
    dudoan = [f"{idx:02d}" for idx in top_idxs]
    msg = (
        "🤖 *AI (Random Forest) dự đoán dàn số khả năng cao nhất kỳ tới:*\n"
        + ", ".join(dudoan)
        + "\n\n(Lưu ý: Dự đoán mang tính giải trí, không đảm bảo trúng thưởng!)"
    )
    return dudoan, msg
