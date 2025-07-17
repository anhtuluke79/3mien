import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib
import os

def train_rf_db(csv_path="xsmb.csv", model_path="model_rf_xsmb.pkl", n_feature=7):
    """
    Train model Random Forest cho dự đoán giải Đặc Biệt miền Bắc.
    """
    if not os.path.exists(csv_path):
        print("❌ Chưa có file dữ liệu xsmb.csv!")
        return False
    df = pd.read_csv(csv_path)
    dbs = df['ĐB'].astype(str).str[-2:].astype(int)
    X, y = [], []
    for i in range(len(dbs) - n_feature):
        X.append(dbs[i:i+n_feature].tolist())
        y.append(dbs[i+n_feature])
    if not X or not y:
        print("❌ Không đủ dữ liệu để train!")
        return False
    model = RandomForestClassifier(n_estimators=120, random_state=42)
    model.fit(X, y)
    joblib.dump(model, model_path)
    print(f"✅ Train xong model RF ĐB, lưu tại: {model_path}")
    return True

def predict_rf_xsmb(csv_path="xsmb.csv", model_path="model_rf_xsmb.pkl", n_feature=7):
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

# Test
if __name__ == "__main__":
    train_rf_db()
