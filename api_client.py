import requests

API_URL = "http://10.8.1.11:9001"
API_KEY = "ac7ab11bb27eec55ddec772b5c8eab42917da842dfb4da80add15288ae58d4bb"

def api_headers():
    return {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }

def get_relays():
    r = requests.get(f"{API_URL}/relays", headers=api_headers(), timeout=10)
    r.raise_for_status()
    return r.json()

def control_relay(relay_id, state):
    r = requests.post(f"{API_URL}/relays/control", headers=api_headers(), json={
        "relay_id": relay_id,
        "state": state
    }, timeout=1)
    r.raise_for_status()
    return r.json()

def get_logs(limit=100):
    r = requests.get(f"{API_URL}/logs?limit={limit}", headers=api_headers())
    r.raise_for_status()
    return r.json()

def get_modem_info():
    r = requests.get(f"{API_URL}/modem/info", headers=api_headers())
    r.raise_for_status()
    return r.json()

def get_modem_signal():
    r = requests.get(f"{API_URL}/modem/signal", headers=api_headers(), timeout=10)
    r.raise_for_status()
    return r.json()

def create_relay(relay_data):
    """
    Создает новое реле через API
    
    Args:
        relay_data (dict): Данные реле, включая:
            - relay_id (int): ID реле
            - name (str): Название реле
            - description (str): Описание реле
            - phone_number (str): Номер телефона
            - password (str): Пароль
            - MO (str): Значение MO
            - TP_RP (str): Значение TP_RP
            - Activity (bool): Активность
            - TimeOn (str): Время включения
            - TimeOff (str): Время выключения
            - Status (str): Статус
    
    Returns:
        dict: Данные созданного реле
    
    Raises:
        requests.exceptions.HTTPError: Если API вернул ошибку
    """
    r = requests.post(f"{API_URL}/relays", headers=api_headers(), json=relay_data, timeout=10)
    r.raise_for_status()
    return r.json() 