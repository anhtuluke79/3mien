import os
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib

def get_rf_model_path(num_days):
    if not os.path.exists("data"):
        os.makedirs("data")
    return os.path.join("data", f"rf_xsmb_model_N{num_days}.pkl")

def prepare_rf_X_y(df, num_days=14):
    """
    Trả về X, y với X là ma trận có shape (n_samples, num_days),
    mỗi hàng là chuỗi N số cuối ĐB liền trước, y là số ĐB tiếp theo.
    """
    # Chỉ lấy phần cần thiết, đảo ngược cho đúng thứ tự thời gian
    db_list = df["DB"].astype(str).str[-2:].tolist()
    X, y = [], []
    for i in range(len(db_list) - num_days):
        feat = [int(x) for x in db_list[i:i+num_days]]
        X.append(feat)
        y.append(db_list[i+num_days])
    if not X or not y:
        return None, None
    return pd.DataFrame(X), pd.Series(y)

def train_rf_model(num_days=14, data_path="xsmb.csv"):
    model_path = get_rf_model_path(num_days)
    if not os.path.exists(data_path):
        return "❌ Không tìm thấy file dữ liệu xsmb.csv!"
    df = pd.read_csv(data_path)
    db_col = df["DB"].astype(str).str[-2:]
    if len(db_col) < num_days + 2:
        return f"❌ Không đủ dữ liệu để train với {num_days} ngày."
    # Đảm bảo mới nhất lên đầu
    db_col = db_col[::-1]
    df = df[::-1].reset_index(drop=True)
    df["DB"] = db_col
    X, y = prepare_rf_X_y(df, num_days)
    if X is None or y is None or len(X) < 3:
        return f"❌ Không đủ dữ liệu mẫu để train với {num_days} ngày."
    rf = RandomForestClassifier(n_estimators=100, random_state=42)
    rf.fit(X, y)
    joblib.dump(rf, model_path)
    return f"✅ Đã train xong Random Forest {num_days} ngày và lưu tại {model_path}!"

def predict_rf_model(num_days=14):
    model_path = get_rf_model_path(num_days)
    if not os.path.exists(model_path):
        return f"❌ Chưa train AI với {num_days} ngày. Hãy train trước."
    try:
        rf = joblib.load(model_path)
        df = pd.read_csv("xsmb.csv")
        db_col = df["DB"].astype(str).str[-2:]
        if len(db_col) < num_days:
            return f"❌ Không đủ dữ liệu để dự đoán với {num_days} ngày!"
        # Lấy N số mới nhất (theo thứ tự từ cũ -> mới)
        last_feat = [int(x) for x in db_col[::-1].head(num_days).tolist()][::-1]
        X_input = [last_feat]
        y_pred = rf.predict(X_input)[0]
        proba = rf.predict_proba(X_input)[0]
        top3 = sorted(zip(rf.classes_, proba), key=lambda x: x[1], reverse=True)[:3]
        top3_txt = ", ".join([f"{c} ({p:.1%})" for c, p in top3])
        return (f"🤖 *AI Random Forest {num_days} ngày*\n"
                f"- Dự đoán 2 số cuối ĐB kế tiếp: *{y_pred}*\n"
                f"- Top 3 dự đoán: {top3_txt}")
    except Exception as e:
        return f"❌ Lỗi khi dự đoán: {e}"
