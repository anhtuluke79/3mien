import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib
import os

def train_rf_db(csv_path="xsmb.csv", model_path="model_rf_xsmb.pkl", n_feature=7):
    """
    Train model Random Forest cho dự đoán giải Đặc Biệt miền Bắc.
    - csv_path: file dữ liệu XSMB đã crawl (cần cột 'ĐB')
    - model_path: tên file model lưu lại
    - n_feature: số ngày dùng làm feature
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

if __name__ == "__main__":
    train_rf_db()
