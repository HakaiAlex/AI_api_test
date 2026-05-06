import os
import requests
import base64
import uuid
import urllib3
from dotenv import load_dotenv

load_dotenv()

#отключил предупреждение о самоподписных сертификатах
urllib3.disable_warnings()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
SCOPE = os.getenv("SCOPE")

def get_token():
    url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    auth_string = f"{CLIENT_ID}:{CLIENT_SECRET}"
    encoded_auth = base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')
    payload = {"scope": SCOPE}
    headers ={
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "RqUID": str(uuid.uuid4()),
        "Authorization": f"Basic {encoded_auth}"
    }

    resp = requests.post(url, headers=headers, data=payload, verify=False)
    if resp.status_code == 200:
        return resp.json().get("access_token")
    else:
        print(f"Ошибка авторизации ({resp.status_code}): {resp.text}")
        return None


def ask_gigachat(token, prompt):
    url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Bearer {token}"
    }
    payload = {
        "model": "GigaChat",
        "messages": [{"role": "user", "content": prompt}],
        "stream": False
    }
    resp = requests.post(url, headers=headers, json=payload, verify=False)
    if resp.status_code == 200:
        return resp.json()["choices"][0]["message"]["content"]
    else:
        return print(f"Ошибка чата ({resp.status_code}): {resp.text}")
    

if __name__ == "__main__":
    print("Получаю токен доступа...")
    token = get_token() #Пример тестовый, а так надо токен кэшировать в память/файл, ловить 401 и запрашивать новый файл. Более подробно, если нужно будет, я в инете гляну

    #Для отлавливания ошибок, использовать logging, а не print
    if token:
        print("✅ Токен получен успешно!")
        print("💬 Отправляю запрос в GigaChat...")
        answer = ask_gigachat(token, "Кратко (в 3 пунктах) опиши, как ИИ может ускорить работу аналитика данных.")
        print("\n🤖 Ответ GigaChat:")
        print(answer)
    else:
        print("❌ Запуск прерван. Проверьте .env файл.")

