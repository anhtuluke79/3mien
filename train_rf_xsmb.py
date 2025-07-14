import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib

def train_rf_model(csv_path="xsmb.csv", model_path="rf_model_xsmb.pkl", n_day=10, n_estimators=200, random_state=123):
    """
    Train model RandomForestClassifier dựa trên dữ liệu xsmb.csv
    - n_day: số ngày gần nhất dùng làm feature (default: 10)
    - csv_path: đường dẫn file dữ liệu
    - model_path: nơi lưu model pkl
    """
    df = pd.read_csv(csv_path)
    df = df.sort_values("date")
    X, y = [], []
    for i in range(n_day, len(df)):
        features = []
        for j in range(i-n_day, i):
            features += [int(str(df.iloc[j]['DB'])[-2:]), int(str(df.iloc[j]['G1'])[-2:])]
        X.append(features)
        y.append(int(str(df.iloc[i]['DB'])[-2:]))
    if not X or not y:
        raise Exception("Không đủ dữ liệu để train (file quá ít dòng)")
    model = RandomForestClassifier(n_estimators=n_estimators, random_state=random_state)
    model.fit(X, y)
    joblib.dump(model, model_path)
    print(f"✅ Đã train và lưu model RF vào {model_path}. Số ngày dùng cho feature: {n_day}, dữ liệu train: {len(X)} dòng.")

if __name__ == "__main__":
    # Khi chạy file này trực tiếp: train trên xsmb.csv mặc định
    train_rf_model()
