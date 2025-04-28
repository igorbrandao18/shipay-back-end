# Exemplos de Uso da API

## 1. Gerenciamento de Usuários

### Criar Usuário
```python
import requests

url = "http://localhost:8000/api/v1/users"
data = {
    "name": "João Silva",
    "email": "joao@exemplo.com",
    "role_id": 1
}

response = requests.post(url, json=data)
print(response.json())
```

### Buscar Usuário
```python
import requests

user_id = 1
url = f"http://localhost:8000/api/v1/users/{user_id}"

response = requests.get(url)
print(response.json())
```

## 2. Validação de Dados

### Validar CNPJ
```python
import requests

url = "http://localhost:8000/api/v1/validate/cnpj"
data = {
    "cnpj": "12.345.678/0001-90"
}

response = requests.post(url, json=data)
print(response.json())
```

### Validar CEP
```python
import requests

url = "http://localhost:8000/api/v1/validate/cep"
data = {
    "cep": "12345-678"
}

response = requests.post(url, json=data)
print(response.json())
```

## 3. Relatórios de Lançamentos

### Consultar Lançamentos por Período
```python
import requests
from datetime import datetime, timedelta

url = "http://localhost:8000/api/v1/reports/launches"
params = {
    "start_date": (datetime.now() - timedelta(days=30)).isoformat(),
    "end_date": datetime.now().isoformat()
}

response = requests.get(url, params=params)
print(response.json())
```

### Obter Estatísticas
```python
import requests

url = "http://localhost:8000/api/v1/reports/statistics"

response = requests.get(url)
print(response.json())
```

## 4. Agendamento de Eventos

### Agendar Evento
```python
import requests
from datetime import datetime, timedelta

url = "http://localhost:8000/api/v1/scheduler/schedule"
data = {
    "event_type": "video_render",
    "scheduled_time": (datetime.now() + timedelta(hours=1)).isoformat(),
    "metadata": {
        "video_id": "123",
        "resolution": "1080p"
    }
}

response = requests.post(url, json=data)
print(response.json())
```

### Verificar Status do Evento
```python
import requests

event_id = "abc123"
url = f"http://localhost:8000/api/v1/scheduler/status/{event_id}"

response = requests.get(url)
print(response.json())
```

## 5. Tratamento de Erros

### Exemplo de Tratamento de Erros
```python
import requests
from requests.exceptions import RequestException

try:
    response = requests.post("http://localhost:8000/api/v1/users", json={
        "name": "João Silva",
        "email": "email_invalido",
        "role_id": 1
    })
    response.raise_for_status()
    print(response.json())
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 400:
        print("Erro de validação:", e.response.json())
    elif e.response.status_code == 401:
        print("Não autorizado. Verifique suas credenciais.")
    elif e.response.status_code == 404:
        print("Recurso não encontrado.")
    else:
        print("Erro inesperado:", e.response.json())
except RequestException as e:
    print("Erro de conexão:", str(e)) 