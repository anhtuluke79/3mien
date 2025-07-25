import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import joblib
import os

MODEL_DIR = "data"
os.makedirs(MODEL_DIR, exist_ok=True)

# ==== Nhập số ngày đặc trưng N ====
try:
    N = int(input("Nhập số ngày liên tiếp để train AI (7, 14, 21, 28, 30...): ").strip())
    assert N > 0
except Exception:
    N = 7
    print("Không hợp lệ, dùng mặc định N=7.")

print(f"Dùng N={N} ngày liên tiếp để train đặc trưng.")

# ==== Đọc và chuẩn hóa dữ liệu ====
df = pd.read_csv("data.xsmb.csv")
df = df.sort_values("date")
df['DB'] = df['DB'].astype(str).str.zfill(5)

# ==== Tạo features và labels ====
features = []
labels = []
for i in range(N, len(df)):
    prev = [int(df.iloc[i-j]['DB'][-2:]) for j in range(N, 0, -1)]
    features.append(prev)
    labels.append(int(df.iloc[i]['DB'][-2:]))

X = np.array(features)
y = np.array(labels)

print(f"Tổng số mẫu train: {len(X)}")

if len(X) < 30:
    print("❌ Không đủ mẫu để train. Cần ít nhất 30 dòng dữ liệu!")
    exit(1)

# ==== Train/Test Split ====
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, shuffle=False
)

# ==== Train model Random Forest ====
clf = RandomForestClassifier(n_estimators=200, random_state=42)
clf.fit(X_train, y_train)

# ==== Đánh giá model ====
score = clf.score(X_test, y_test)
print(f"Accuracy trên tập test: {score:.3f}")

# ==== Lưu model ra file ====
model_name = os.path.join(MODEL_DIR, f"rf_xsmb_model_N{N}.pkl")
joblib.dump(clf, model_name)
print(f"Đã lưu model ra file {model_name}")

# ==== Dự đoán cho kỳ tiếp theo (demo) ====
if len(df) >= N:
    lastN = [int(df.iloc[-j]['DB'][-2:]) for j in range(N, 0, -1)]
    probas = clf.predict_proba([lastN])[0]
    top_idxs = np.argsort(probas)[-5:][::-1]
    dudoan = [f"{idx:02d}" for idx in top_idxs]
    print("Dàn số AI Random Forest dự đoán kỳ tới:", ", ".join(dudoan))
else:
    print("Không đủ dữ liệu để dự đoán kỳ tới!")
