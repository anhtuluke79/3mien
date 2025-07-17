import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib
import os

def train_rf_lo_mb(csv_path, model_path, n_days=7):
    """
    Train mô hình RandomForest cho dự đoán lô miền Bắc (lấy n_days ngày trước).
    """
    if not os.path.exists(csv_path):
        return False
    df = pd.read_csv(csv_path)
    dbs = df['ĐB'].astype(str).str[-2:].astype(int)
    X, y = [], []
    for i in range(len(dbs) - n_days):
        X.append(dbs[i:i+n_days].tolist())
        y.append(dbs[i+n_days])  # Lấy số sau chuỗi n_days
    if len(X) == 0 or len(y) == 0:
        return False
    model = RandomForestClassifier(n_estimators=120, random_state=42)
    model.fit(X, y)
    joblib.dump(model, model_path)
    return True

def predict_rf_lo_mb(csv_path, model_path, n_days=7):
    """
    Dự đoán lô MB bằng mô hình RandomForest đã train từ file.
    """
    if not (os.path.exists(csv_path) and os.path.exists(model_path)):
        return "Chưa train hoặc chưa có dữ liệu."
    df = pd.read_csv(csv_path)
    dbs = df['ĐB'].astype(str).str[-2:].astype(int)
    if len(dbs) < n_days:
        return "Không đủ dữ liệu!"
    model = joblib.load(model_path)
    features = dbs[:n_days].tolist()
    pred = model.predict([features])[0]
    return str(pred).zfill(2)
