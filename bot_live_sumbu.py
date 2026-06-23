import os
import numpy as np
import pandas as pd
from xgboost import XGBClassifier

# =====================================================================
# 1. LOAD OTAK AI & DAFTAR FITUR YANG UDAH LU DOWNLOAD
# =====================================================================
print("➔ Mengunggah otak AI XGBoost ke sistem VPS...")

# Membaca urutan fitur wajib dari file txt
with open("daftar_fitur.txt", "r") as f:
    fitur_wajib = [line.strip() for line in f.readlines()]

# Muat model XGBoost json
model_live = XGBClassifier()
model_live.load_model("model_xgboost_sumbu.json")

print(f"✅ Robot Live Siap! Mengunci {len(fitur_wajib)} fitur standar.")
print("-" * 50)

# =====================================================================
# 2. FUNGSI DETEKSI MARKET LIVE (DIPANGGIL SETIAP CANDLE M1 CLOSE)
# =====================================================================
def cek_sinyal_live(df_live_m1):
    """
    df_live_m1: Dataframe berisi 1 baris data candle M1 terakhir 
                yang indikatornya udah dihitung lengkap dari MT5.
    """
    try:
        # Pastikan urutan kolom data live SAMA PERSIS dengan saat latihan kemarin
        X_live = df_live_m1[fitur_wajib]
        
        # AI Mulai Menebak
        prediksi = model_live.predict(X_live)[0]
        probabilitas = model_live.predict_proba(X_live)[0][1] # Persentase keyakinan AI
        
        if prediksi == 1 and probabilitas > 0.85: # Filter tambahan: Hanya entry jika keyakinan AI > 85%
            print(f"🔥 [SINYAL VALID] AI Mendeteksi Pucuk Sumbu Emas! (Akurasi Keyakinan: {probabilitas*100:.2f}%)")
            return "ENTRY_SELL"
        else:
            print(f"💤 [NO ACTION] Candle normal. Keyakinan AI cuma: {probabilitas*100:.2f}%")
            return "WAIT"
            
    except Exception as e:
        print(f"❌ Gagal memproses data live: {e}")
        return "ERROR"

# =====================================================================
# 3. SETTINGAN MM BERDASARKAN STATISTIK COLAB
# =====================================================================
FIXED_TP_POIN = 150   # Ambil profit aman $1.50 (150 poin)
FIXED_SL_POIN = 30    # Batas cut-loss kaku $0.30 (30 poin) di atas High candle

print(f"🛠️ Aturan Main Money Management:")
print(f" ➔ Target Take Profit : {FIXED_TP_POIN} Poin ($1.50)")
print(f" ➔ Resiko Stop Loss   : {FIXED_SL_POIN} Poin ($0.30)")
print("-" * 50)
