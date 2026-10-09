import requests

ip_esp32 = "10.74.22.240"  # Troque pelo IP real do ESP32
url = f"http://{ip_esp32}/api/dados"

try:
    resposta = requests.get(url, timeout=5)

    print("Status HTTP:", resposta.status_code)
    print("Dados do sensor:", resposta.json())

except requests.exceptions.RequestException as erro:
    print("Erro ao conectar:", erro)