import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib
import os
def predict_rf_lo_mb(csv_path, model_path, n_days=7):
    # Dummy function, bạn thay bằng code thật nếu có
    return "Dự đoán lô MB mẫu"
def train_rf_lo_mb(csv_path, model_path, n_feature=7):
    if not os.path.exists(csv_path):
        return False
    df = pd.read_csv(csv_path)
    dbs = df['ĐB'].astype(str).str[-2:].astype(int)
    X, y = [], []
    for i in range(len(dbs) - n_feature):
        X.append(dbs[i:i+n_feature].tolist())
        y.append(dbs[i+n_feature])  # Lô, có thể thay đổi tùy cách tính
    model = RandomForestClassifier(n_estimators=120, random_state=42)
    model.fit(X, y)
    joblib.dump(model, model_path)
    return True

def predict_rf_lo_mb(csv_path, model_path, n_feature=7):
    if not (os.path.exists(csv_path) and os.path.exists(model_path)):
        return "Chưa train hoặc chưa có dữ liệu."
    df = pd.read_csv(csv_path)
    dbs = df['ĐB'].astype(str).str[-2:].astype(int)
    if len(dbs) < n_feature:
        return "Không đủ dữ liệu!"
    model = joblib.load(model_path)
    features = dbs[:n_feature].tolist()
    pred = model.predict([features])[0]
    return str(pred).zfill(2)
