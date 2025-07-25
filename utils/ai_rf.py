# utils/ai_rf.py

import os
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib

def get_rf_model_path(num_days):
    # Đảm bảo thư mục data/
    if not os.path.exists("data"):
        os.makedirs("data")
    return os.path.join("data", f"rf_xsmb_model_N{num_days}.pkl")

def prepare_rf_data(num_days=14, data_path="xsmb.csv"):
    if not os.path.exists(data_path):
        return None, None, "❌ Không tìm thấy file dữ liệu xsmb.csv!"
    df = pd.read_csv(data_path)
    df = df.sort_values("date", ascending=False).head(num_days)
    # Dummy: đặc trưng là chỉ số ngày (có thể mở rộng thêm đặc trưng khác)
    X = df.index.values.reshape(-1, 1)
    y = df["DB"].astype(str).str[-2:]   # 2 số cuối ĐB
    return X, y, None

def train_rf_model(num_days=14, data_path="xsmb.csv"):
    model_path = get_rf_model_path(num_days)
    X, y, err = prepare_rf_data(num_days, data_path)
    if err: return err
    if X is None or len(X) < 2:
        return f"❌ Không đủ dữ liệu để train với {num_days} ngày."
    rf = RandomForestClassifier(n_estimators=100, random_state=42)
    rf.fit(X, y)
    joblib.dump(rf, model_path)
    return f"✅ Đã train xong Random Forest {num_days} ngày và lưu tại {model_path}!"

def predict_rf_model(num_days=14):
    model_path = get_rf_model_path(num_days)
    if not os.path.exists(model_path):
        return f"❌ Chưa train AI với {num_days} ngày. Hãy train trước."
    # Dự đoán cho ngày tiếp theo (index tiếp theo)
    try:
        rf = joblib.load(model_path)
        df = pd.read_csv("xsmb.csv")
        X_input = [[df.shape[0]]]  # index mới nhất + 1
        y_pred = rf.predict(X_input)[0]
        return f"🤖 Dự đoán Random Forest {num_days} ngày: *{y_pred}* (2 số cuối ĐB)"
    except Exception as e:
        return f"❌ Lỗi khi dự đoán: {e}"
