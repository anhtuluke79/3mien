# utils/ai_rf/train_all.py
from rf_db import train_rf_db
from rf_lo import train_rf_lo27

if __name__ == "__main__":
    print("====== TRAIN TỔNG HỢP AI RF ======")
    print(">> Train Đặc Biệt ...")
    ok_db = train_rf_db("xsmb.csv", "model_rf_xsmb.pkl", 7)
    print(">> Train Lô 27 số ...")
    ok_lo = train_rf_lo27("xsmb.csv", "model_rf_lo27.pkl", 7)
    print("\n----- Kết quả -----")
    if ok_db:
        print("✅ Model Đặc Biệt: OK")
    else:
        print("❌ Model Đặc Biệt: Lỗi hoặc thiếu dữ liệu")
    if ok_lo:
        print("✅ Model Lô 27 số: OK")
    else:
        print("❌ Model Lô 27 số: Lỗi hoặc thiếu dữ liệu")
    if ok_db and ok_lo:
        print("\n🎉 Đã train xong cả 2 model AI RF!")
    else:
        print("\n⚠️ Có lỗi khi train, kiểm tra lại file xsmb.csv.")
