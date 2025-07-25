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
    # Ví dụ: dự đoán số cuối giải ĐB. X, y sẽ cần chuẩn hóa lại tùy mục đích thực tế
    # Ở đây dự đoán số cuối của DB
    X = df.index.values.reshape(-1, 1)  # chỉ số ngày (dummy), bạn nên đổi thành đặc trưng mạnh hơn
    y = df["DB"].astype(str).str[-2:]   # 2 số cuối đặc biệt
    return X, y, None

def train_rf_model(num_days=14, data_path="xsmb.csv"):
    model_path = get_rf_model_path(num_days)
    X, y, err = prepare_rf_data(num_days, data_path)
    if err: return err
    if len(X) < 2:
        return f"❌ Không đủ dữ liệu để train với {num_days} ngày."
    rf = RandomForestClassifier(n_estimators=100, random_state=42)
    rf.fit(X, y)
    joblib.dump(rf, model_path)
    return f"✅ Đã train xong Random Forest {num_days} ngày và lưu tại {model_path}!"

def predict_rf_model(num_days=14):
    model_path = get_rf_model_path(num_days)
    if not os.path.exists(model_path):
        return f"❌ Chưa train AI với {num_days} ngày. Hãy train trước."
    # Dự đoán cho ngày tiếp theo
    rf = joblib.load(model_path)
    # Giả sử predict tiếp ngày mới nhất (index + 1)
    try:
        df = pd.read_csv("xsmb.csv")
        X_input = [[df.shape[0]]]  # index tiếp theo (dummy feature)
        y_pred = rf.predict(X_input)[0]
        return f"🤖 Dự đoán Random Forest {num_days} ngày: *{y_pred}* (2 số cuối ĐB)"  # Bạn có thể mở rộng trả về cả xác suất vv
    except Exception as e:
        return f"❌ Lỗi khi dự đoán: {e}"
