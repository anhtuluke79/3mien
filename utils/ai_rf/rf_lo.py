import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import MultiLabelBinarizer
import joblib
import os

def get_all_los(df):
    # Lấy tất cả các số 2 chữ số từ giải ĐB và các giải khác trong 1 ngày
    # Tùy file xsmb.csv, nếu chỉ có cột ĐB thì dùng ĐB, nếu đầy đủ thì mở rộng
    # Dưới đây chỉ lấy từ ĐB, bạn có thể mở rộng
    los = []
    for i, row in df.iterrows():
        # Lấy từng cặp 2 số cuối cùng của các giải (ở đây chỉ lấy ĐB)
        so_db = str(row['ĐB']).strip()[-2:]
        if len(so_db) == 2:
            los.append(so_db)
    return los

def train_rf_lo27(csv_path="xsmb.csv", model_path="model_rf_lo27.pkl", n_feature=7):
    """
    Train mô hình Random Forest multi-label cho dự đoán lô 27 số.
    Mỗi ngày là 1 vector 2 số cuối của 27 giải, gộp thành multi-label.
    """
    if not os.path.exists(csv_path):
        print("❌ Chưa có file dữ liệu xsmb.csv!")
        return False
    df = pd.read_csv(csv_path)
    all_los = [str(x).zfill(2) for x in range(0, 100)]  # các lô từ 00-99
    X, y = [], []
    for i in range(len(df) - n_feature):
        # Feature: 7 ngày gần nhất mỗi ngày lấy ĐB cuối (nếu cần, bạn lấy thêm các giải khác)
        feature = []
        for j in range(i, i + n_feature):
            so_db = str(df.iloc[j]['ĐB']).strip()[-2:]
            feature.append(int(so_db))
        # Target: các lô về ngày tiếp theo (có thể chỉ ĐB, hoặc bạn mở rộng sang G1-G7)
        los = []
        row_next = df.iloc[i + n_feature]
        # Dưới đây chỉ lấy từ ĐB (nếu muốn đủ 27 lô phải mở rộng file)
        so_db_next = str(row_next['ĐB']).strip()[-2:]
        if len(so_db_next) == 2:
            los.append(so_db_next)
        # Nếu cần thêm từ các giải khác, bạn xử lý thêm ở đây
        y.append(los)
        X.append(feature)
    if not X or not y:
        print("❌ Không đủ dữ liệu để train lô 27.")
        return False
    mlb = MultiLabelBinarizer(classes=[str(x).zfill(2) for x in range(0,100)])
    y_bin = mlb.fit_transform(y)
    model = RandomForestClassifier(n_estimators=150, random_state=42)
    model.fit(X, y_bin)
    joblib.dump((model, mlb), model_path)
    print(f"✅ Train xong model lô 27 số, lưu tại: {model_path}")
    return True

def predict_rf_lo27(csv_path="xsmb.csv", model_path="model_rf_lo27.pkl", n_feature=7, topk=2):
    """
    Dự đoán top K lô có xác suất về cao nhất theo model multi-label Random Forest đã train.
    """
    if not (os.path.exists(csv_path) and os.path.exists(model_path)):
        return "Chưa train hoặc chưa có dữ liệu/model."
    df = pd.read_csv(csv_path)
    if len(df) < n_feature:
        return "Không đủ dữ liệu!"
    model, mlb = joblib.load(model_path)
    X_pred = []
    for i in range(n_feature):
        so_db = str(df.iloc[i]['ĐB']).strip()[-2:]
        X_pred.append(int(so_db))
    X_pred = np.array(X_pred).reshape(1, -1)
    y_proba = model.predict_proba(X_pred)[0]
    # y_proba là list n_class x 2 (với RF multioutput), chỉ lấy xác suất lớp = 1
    # Nên lấy [i][1] cho mỗi i
    scores = [p[1] if isinstance(p, (list, np.ndarray)) else p for p in y_proba]
    top_idx = np.argsort(scores)[::-1][:topk]
    los = mlb.classes_[top_idx]
    probs = [scores[i] for i in top_idx]
    return ", ".join([f"{l} ({round(p*100,1)}%)" for l, p in zip(los, probs)])

# Cho phép chạy độc lập để train
if __name__ == "__main__":
    train_rf_lo27()
