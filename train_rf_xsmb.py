import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib

# Đọc dữ liệu, yêu cầu file xsmb.csv đã có các trường: date, DB, G1
df = pd.read_csv("xsmb.csv")

# Lấy đặc trưng đơn giản: dùng 3 ngày gần nhất trước để dự đoán DB ngày sau (2 số cuối)
X, y = [], []
for i in range(3, len(df)):
    features = []
    for j in range(i-3, i):
        features += [int(str(df.iloc[j]['DB'])[-2:]), int(str(df.iloc[j]['G1'])[-2:])]
    X.append(features)
    y.append(int(str(df.iloc[i]['DB'])[-2:]))

# Train model
model = RandomForestClassifier(n_estimators=200, random_state=42)
model.fit(X, y)

# Save model
joblib.dump(model, "rf_model_xsmb.pkl")
print("Đã train xong và lưu rf_model_xsmb.pkl!")
