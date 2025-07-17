import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib
import os

def train_rf_db(csv_path="xsmb.csv", model_path="model_rf_xsmb.pkl", n_feature=7):
    if not os.path.exists(csv_path):
        print("Chưa có file dữ liệu xsmb.csv!")
        return False
    df = pd.read_csv(csv_path)
    dbs = df['ĐB'].astype(str).str[-2:].astype(int)
    X, y = [], []
    for i in range(len(dbs) - n_feature):
        X.append(dbs[i:i+n_feature].tolist())
        y.append(dbs[i+n_feature])
    if not X or not y:
        print("Không đủ dữ liệu để train ĐB.")
        return False
    model = RandomForestClassifier(n_estimators=120, random_state=42)
    model.fit(X, y)
    joblib.dump(model, model_path)
    print(f"✅ Train xong model ĐB ({model_path})")
    return True

def train_rf_lo(csv_path="xsmb.csv", model_path="model_rf_lo_mb.pkl", n_feature=7):
    if not os.path.exists(csv_path):
        print("Chưa có file dữ liệu xsmb.csv!")
        return False
    df = pd.read_csv(csv_path)
    dbs = df['ĐB'].astype(str).str[-2:].astype(int)
    X, y = [], []
    for i in range(len(dbs) - n_feature):
        X.append(dbs[i:i+n_feature].tolist())
        y.append(dbs[i+n_feature])  # Có thể custom target nếu bạn muốn dự đoán khác
    if not X or not y:
        print("Không đủ dữ liệu để train Lô.")
        return False
    model = RandomForestClassifier(n_estimators=120, random_state=42)
    model.fit(X, y)
    joblib.dump(model, model_path)
    print(f"✅ Train xong model Lô ({model_path})")
    return True

if __name__ == "__main__":
    print("=== TRAIN ALL AI RF ===")
    ok_db = train_rf_db()
    ok_lo = train_rf_lo()
    if ok_db and ok_lo:
        print("🎉 Đã train xong cả 2 model AI RF.")
    else:
        print("⚠️ Có lỗi khi train model. Kiểm tra lại dữ liệu hoặc log.")
