# ESP32 DHT11 HTTP API

Projeto de monitoramento de temperatura e umidade utilizando ESP32, sensor DHT11, display OLED e uma API HTTP. Os dados coletados pelo sensor são disponibilizados pelo ESP32 e consumidos por uma aplicação Python com Flask, que apresenta as informações em um painel web.

## Funcionalidades

* Leitura de temperatura e umidade pelo DHT11.
* Exibição das informações em um display OLED.
* Disponibilização dos dados por meio de uma API HTTP.
* Painel web desenvolvido com Python e Flask.
* Atualização automática das informações.
* Gráficos com histórico recente das medições.
* Exibição dos valores mínimos e máximos registrados durante a sessão.
* Conversão da temperatura entre Celsius, Fahrenheit e Kelvin.
* Identificação de falhas de comunicação com o ESP32.

## Tecnologias utilizadas

* ESP32
* Sensor DHT11
* Display OLED I²C
* Arduino IDE e C++
* Python
* Flask
* Requests
* HTML, CSS e JavaScript

## Estrutura do projeto

```text
esp32-dht22-api-http/
├── app.py
├── teste.py
├── requirements.txt
└── README.md
```

* `app.py`: aplicação Flask responsável pelo painel web e pela comunicação com o ESP32.
* `teste.py`: script Python para testar a API HTTP.
* `requirements.txt`: dependências necessárias para executar a aplicação.

## Requisitos

* ESP32 com o firmware do projeto carregado.
* Sensor DHT11 conectado ao ESP32.
* Display OLED conectado ao ESP32.
* Computador com Python instalado.
* ESP32 e computador conectados à mesma rede Wi-Fi, com comunicação entre os dispositivos permitida.

## Instalação

Clone o repositório:

```bash
git clone https://github.com/SEU_USUARIO/esp32-dht22-api-http.git
```

Entre na pasta do projeto:

```bash
cd esp32-dht22-api-http
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

## Configuração

O ESP32 deve estar executando um firmware que disponibilize o endpoint:

```text
/api/dados
```

A API retorna os dados em formato JSON:

```json
{
  "temperatura": 26.0,
  "umidade": 55.0
}
```

Os valores acima são apenas exemplos.

No arquivo `app.py`, configure o endereço IP do ESP32 na variável `ESP32_IP`. O projeto também permite informar o endereço pela linha de comando ou pela variável de ambiente `ESP32_IP`.

## Executando o painel

Execute o comando:

```bash
python app.py
```

Por padrão, o painel estará disponível em:

```text
http://localhost:5000
```

Para informar o IP do ESP32 diretamente pelo terminal:

```bash
python app.py 192.168.1.105
```

Substitua `192.168.1.105` pelo endereço IP real da sua placa.

## Testando a API

Para testar a comunicação diretamente com o ESP32, configure o endereço IP no arquivo `teste.py` e execute:

```bash
python teste.py
```

O script realiza uma requisição HTTP GET e apresenta o código de status e os dados recebidos.

Também é possível acessar o endpoint diretamente pelo navegador:

```text
http://IP_DO_ESP32/api/dados
```

## Como funciona

1. O DHT11 coleta os dados de temperatura e umidade.
2. O ESP32 disponibiliza as leituras por meio de uma API HTTP.
3. A aplicação Python realiza requisições ao endpoint do ESP32.
4. O Flask disponibiliza os dados para o painel web.
5. A interface apresenta as medições e atualiza os gráficos automaticamente.

## Objetivo

Demonstrar a integração entre sistemas embarcados, sensores, comunicação HTTP e desenvolvimento web, utilizando Python para consumir dados de um dispositivo IoT em tempo real.

## Licença

Este projeto pode ser utilizado para fins educacionais e de estudo. Adicione uma licença específica ao repositório caso queira definir formalmente as condições de uso e distribuição.
