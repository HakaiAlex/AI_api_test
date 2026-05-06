import pandas as pd
import requests

# 1. Чтение CSV (путь указан относительно корня проекта)
try:
    df = pd.read_csv("D:\Sasha\Projects\AI_api\AI_api_test\data/sample.csv")
    print("✅ Данные загружены. Строк:", len(df))
    print("📊 Средние продажи:", df["sales"].mean())
except Exception as e:
    print(f"❌ Ошибка чтения CSV: {e}")

# 2. Проверка работы requests
try:
    r = requests.get("https://httpbin.org/get", timeout=5)
    print("✅ requests работает. Статус ответа:", r.status_code)
except Exception as e:
    print(f"❌ Ошибка requests: {e}")