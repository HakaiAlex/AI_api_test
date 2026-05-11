import os
import json
import requests
import base64
import uuid
import urllib3
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# отключил предупреждение о самоподписных сертификатах
urllib3.disable_warnings()

# Конфигурация
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
SCOPE = os.getenv("SCOPE")
GIGACHAT_MODEL = "GigaChat"


# Работа с данными
def load_data(filepath: str) -> pd.DataFrame:
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Файл не найден: {filepath}")
    
    df = pd.read_csv(filepath, encoding='utf-8')
    print(f"Загружено {len(df)} строк, {len(df.columns)} колонок")
    return df


def generate_data_summary(df: pd.DataFrame, top_n: int = 3) -> str:
    summary = []

    # Статистика дата фрейма
    summary.append(f"Всего записей: {len(df)}")
    summary.append(f"Колонки: {', '.join(df.columns.to_list())}")

    # Числовые колонки: среднее, мин, макс
    numeric_cols = df.select_dtypes(include='number').columns
    for col in numeric_cols[:top_n]: #берем первые n числовие (по дефолту 3)
        summary.append(f"{col}: среднее={df[col].mean():.2f}, мин={df[col].min()}, макс={df[col].max()}")

    # Категориальные: уникальные значения
    obj_cols = df.select_dtypes(include='object').columns
    for col in obj_cols[:top_n]:
        unique_vals = df[col].nunique()
        top_vals = df[col].value_counts().head(2).tolist()
        summary.append(f"{col}: {unique_vals} уникальных, топ-2: {top_vals}")
    
    return "; ".join(summary)

# Gigachat API. Получает access token через OAuth 2.0 (Sber)
def get_gigachat_token() -> str | None:
    url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    auth_string = f"{CLIENT_ID}:{CLIENT_SECRET}"
    encoded_auth = base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "RqUID": str(uuid.uuid4()),
        "Authorization": f"Basic {encoded_auth}"
    }
    payload = {"scope": SCOPE}
    
    try:
        resp = requests.post(url, headers=headers, data=payload, verify=False, timeout=30)
        resp.raise_for_status()
        return resp.json().get("access_token")
    except requests.exceptions.RequestException as e:
        print(f"Ошибка получения токена: {e}")
        return None

# Отправляет промпт и получает ответ
def ask_gigachat(token: str, prompt: str, temperature: float = 0.3) -> str | None:
    url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    payload = {
        "model": GIGACHAT_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,  # 0.3 = более детерминированные ответы
        "stream": False
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, verify=False, timeout=60)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as e:
        print(f"Ошибка запроса к GigaChat: {e}")
        return None
    
# Бизнес-логика (формируем промпт с контекстом данных)
def build_prompt(data_summary: str, task: str = "анализ") -> str:
    prompts = {
        "анализ": (
            f"Ты — опытный аналитик данных. Вот краткая статистика по набору данных: {data_summary}. "
            "Дай 3 практических рекомендации для бизнеса на основе этих данных. "
            "Отвечай кратко, по пунктам, на русском языке."
        ),
        "гипотезы": (
            f"Данные: {data_summary}. "
            "Предложи 3 гипотезы, которые можно проверить с помощью дополнительного анализа. "
            "Отвечай кратко, на русском."
        ),
        "отчет": (
            f"Статистика: {data_summary}. "
            "Сформируй краткий текстовый отчёт для руководителя (3-4 предложения). "
            "Акцент на выводах, а не на цифрах."
        )
    }
    return prompts.get(task, prompts["анализ"])


def main():
    # Загрузка данных
    print("Загружаю данные...")
    df = load_data(r"D:\Sasha\Projects\AI_api\AI_api_test\data\sample.csv")  # путь относительно src/
    
    # Генерация сводки данных
    print("📝 Формирую контекст для ИИ...")
    data_summary = generate_data_summary(df)
    
    # Получение токена
    print("Получаю токен GigaChat...")
    token = get_gigachat_token()
    if not token:
        print("Не удалось получить токен. Проверьте .env и подключение.")
        return
    
    # Формирование и отправка промпта
    prompt = build_prompt(data_summary, task="анализ")  # можно менять: "анализ", "гипотезы", "отчет"
    print("💬 Запрашиваю анализ у GigaChat...")
    
    answer = ask_gigachat(token, prompt)
    
    # Вывод результата
    if answer:
        print("\n" + "═" * 50)
        print("ИНСАЙТЫ ОТ GIGACHAT:")
        print("═" * 50)
        print(answer)
        print("═" * 50 + "\n")
        
        # Опционально: сохранить результат
        with open(r"D:\Sasha\Projects\AI_api\Uploaded_data\ai_report.txt", "w", encoding="utf-8") as f:
            f.write(f"Данные: {data_summary}\n\nОтвет ИИ:\n{answer}")
        print("Отчёт сохранён в data/ai_report.txt")
    else:
        print("Не получен ответ от ИИ.")


if __name__ == "__main__":
    main()
