import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib

# Đọc dữ liệu lịch sử
df = pd.read_csv('xsmb.csv')
df = df.dropna()
df['ĐB'] = df['ĐB'].astype(str).str[-2:]
df['ĐB'] = df['ĐB'].astype(int)

# Tạo tập huấn luyện: 7 ngày liên tiếp -> ĐB ngày tiếp theo
X, y = [], []
for i in range(len(df) - 7):
    features = df['ĐB'][i:i+7].tolist()
    label = df['ĐB'][i+7]
    X.append(features)
    y.append(label)

# Huấn luyện mô hình
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X, y)

# Lưu mô hình với tên mới
joblib.dump(model, 'model_rf_loto.pkl')
print("
