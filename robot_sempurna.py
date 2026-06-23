import time
import MetaTrader5 as mt5
import pandas as pd
from bot_live_sumbu import cek_sinyal_live

# =====================================================================
# 1. KONEKSI KAKU KE TERMINAL METATRADER 5
# =====================================================================
if not mt5.initialize():
    print("❌ Gagal koneksi ke MT5. Pastikan aplikasi MT5 di VPS sudah dibuka!")
    quit()

SYMBOL = "XAUUSD"
LOT_SIZE = 0.1  # Ukuran lot aman buat uji coba akun demo
print(f"✅ Berhasil Terhubung ke MT5! Memantau Pair: {SYMBOL}")
print("-" * 50)

# =====================================================================
# 2. LOOPING UTAMA: CEK MARKET SETIAP DETIK PERGANTIAN CANDLE
# =====================================================================
menit_terakhir = -1

while True:
    try:
        # Tarik info waktu server MT5
        waktu_sekarang = mt5.symbol_info_tick(SYMBOL).time
        menit_sekarang = time.localtime(waktu_sekarang).tm_min
        
        # Jalankan logika HANYA jika menit baru saja berganti (Candle M1 baru Close)
        if menit_sekarang != menit_terakhir:
            print(f"\n⏰ Menit baru terdeteksi: {time.strftime('%H:%M:%S', time.localtime(waktu_sekarang))}")
            
            # 📥 TARIK DATA CANDLE TERAKHIR DARI MT5
            rates = mt5.copy_rates_from_pos(SYMBOL, mt5.TIMEFRAME_M1, 0, 2)
            df_live = pd.DataFrame(rates)
            
            # Target kita adalah candle index 0 (yang baru saja close murni)
            candle_close = df_live.iloc[[0]].copy()
            
            # --- CALCULATE FITUR MATEMATIS (WAJIB UTUH 82 KOLOM) ---
            # Catatan: Ini contoh kalkulasi basis, pastikan 82 indikator lu masuk semua di sini
            candle_close['pct_wick_atas'] = (candle_close['high'] - candle_close[['open', 'close']].max(axis=1)) / (candle_close['high'] - candle_close['low'])
            candle_close['pct_body'] = (candle_close['open'] - candle_close['close']).abs() / (candle_close['high'] - candle_close['low'])
            
            # 🧠 OPER KE OTAK AI XGBOOST UNTUK DINILAI
            keputusan_ai = cek_sinyal_live(candle_close)
            
            # 🚀 EKSEKUSI JALUR ORDER JIKA AI BERKATA "ENTRY_SELL"
            if keputusan_ai == "ENTRY_SELL":
                harga_entry = mt5.symbol_info_tick(SYMBOL).bid
                
                # MM Kaku dari data Colab lu: SL 30 poin ($0.30), TP 150 poin ($1.50)
                sl_live = harga_entry + 0.30
                tp_live = harga_entry - 1.50
                
                request = {
                    "action": mt5.TRADE_ACTION_DEAL,
                    "symbol": SYMBOL,
                    "volume": LOT_SIZE,
                    "type": mt5.ORDER_TYPE_SELL,
                    "price": harga_entry,
                    "sl": sl_live,
                    "tp": tp_live,
                    "deviation": 10,
                    "magic": 202606,
                    "comment": "XGBoost Pucuk Sumbu",
                    "type_time": mt5.ORDER_TIME_GTC,
                    "type_filling": mt5.ORDER_FILLING_IOC,
                }
                
                # Kirim ke pasar!
                hasil_order = mt5.order_send(request)
                if hasil_order.retcode == mt5.TRADE_RETCODE_DONE:
                    print(f"💰 [CUAN ENTRY SUCCESS] Sell di {harga_entry} | SL: {sl_live} | TP: {tp_live}")
                else:
                    print(f"❌ Order ditolak broker: {hasil_order.comment}")
            
            # Kunci menit agar tidak spamming order
            menit_terakhir = menit_sekarang
            
        time.sleep(1)
        
    except KeyboardInterrupt:
        print("\n🛑 Robot dimatikan!")
        mt5.shutdown()
        break
    except Exception as e:
        print(f"⚠️ Ada error sistem: {e}")
        time.sleep(2)
