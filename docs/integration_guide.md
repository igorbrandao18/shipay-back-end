# Guia de Integração da API

## 1. Autenticação

A API utiliza autenticação baseada em JWT (JSON Web Token). Para acessar os endpoints protegidos, você precisa:

1. Obter um token de acesso através do endpoint de autenticação
2. Incluir o token no header `Authorization` de todas as requisições subsequentes

### Exemplo de Autenticação

```python
import requests

# Obter token
auth_url = "http://localhost:8000/api/v1/auth/token"
auth_data = {
    "username": "seu_usuario",
    "password": "sua_senha"
}

auth_response = requests.post(auth_url, json=auth_data)
token = auth_response.json()["access_token"]

# Usar token em requisições subsequentes
headers = {
    "Authorization": f"Bearer {token}"
}

response = requests.get("http://localhost:8000/api/v1/users/1", headers=headers)
```

## 2. Endpoints Disponíveis

### 2.1 Usuários

#### Criar Usuário
- **Método**: POST
- **URL**: `/api/v1/users`
- **Corpo**:
  ```json
  {
    "name": "string",
    "email": "string",
    "role_id": "integer"
  }
  ```

#### Buscar Usuário
- **Método**: GET
- **URL**: `/api/v1/users/{user_id}`

### 2.2 Validação

#### Validar CNPJ
- **Método**: POST
- **URL**: `/api/v1/validate/cnpj`
- **Corpo**:
  ```json
  {
    "cnpj": "string"
  }
  ```

#### Validar CEP
- **Método**: POST
- **URL**: `/api/v1/validate/cep`
- **Corpo**:
  ```json
  {
    "cep": "string"
  }
  ```

### 2.3 Relatórios

#### Consultar Lançamentos
- **Método**: GET
- **URL**: `/api/v1/reports/launches`
- **Parâmetros**:
  - `start_date`: string (ISO 8601)
  - `end_date`: string (ISO 8601)

#### Estatísticas
- **Método**: GET
- **URL**: `/api/v1/reports/statistics`

### 2.4 Agendador

#### Agendar Evento
- **Método**: POST
- **URL**: `/api/v1/scheduler/schedule`
- **Corpo**:
  ```json
  {
    "event_type": "string",
    "scheduled_time": "string (ISO 8601)",
    "metadata": {
      "video_id": "string",
      "resolution": "string"
    }
  }
  ```

#### Status do Evento
- **Método**: GET
- **URL**: `/api/v1/scheduler/status/{event_id}`

## 3. Tratamento de Erros

A API retorna códigos de status HTTP apropriados e mensagens de erro detalhadas em formato JSON.

### Códigos de Status Comuns

- `200 OK`: Requisição bem-sucedida
- `201 Created`: Recurso criado com sucesso
- `400 Bad Request`: Erro de validação ou dados inválidos
- `401 Unauthorized`: Autenticação necessária ou inválida
- `403 Forbidden`: Acesso negado
- `404 Not Found`: Recurso não encontrado
- `500 Internal Server Error`: Erro interno do servidor

### Formato de Resposta de Erro

```json
{
  "detail": "Mensagem de erro detalhada",
  "code": "CÓDIGO_DO_ERRO",
  "status": "HTTP_STATUS_CODE"
}
```

## 4. Boas Práticas

1. **Tratamento de Erros**
   - Sempre implemente tratamento de erros adequado
   - Verifique os códigos de status HTTP
   - Utilize as mensagens de erro fornecidas

2. **Autenticação**
   - Armazene tokens de forma segura
   - Implemente renovação automática de token
   - Não exponha credenciais em código

3. **Requisições**
   - Implemente retry com backoff exponencial
   - Utilize timeouts apropriados
   - Valide dados antes de enviar

4. **Performance**
   - Implemente cache quando apropriado
   - Utilize paginação para grandes conjuntos de dados
   - Minimize o número de requisições

## 5. Exemplo de Cliente Python

```python
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

class ShipayAPI:
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.token = None
        self.token_expiry = None

    def _get_token(self) -> str:
        if self.token and self.token_expiry and datetime.now() < self.token_expiry:
            return self.token

        auth_url = f"{self.base_url}/api/v1/auth/token"
        auth_data = {
            "username": self.username,
            "password": self.password
        }

        response = requests.post(auth_url, json=auth_data)
        response.raise_for_status()
        
        data = response.json()
        self.token = data["access_token"]
        self.token_expiry = datetime.now() + timedelta(seconds=data["expires_in"])
        
        return self.token

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        token = self._get_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        url = f"{self.base_url}{endpoint}"
        response = requests.request(method, url, headers=headers, **kwargs)
        response.raise_for_status()
        
        return response.json()

    def create_user(self, name: str, email: str, role_id: int) -> Dict[str, Any]:
        data = {
            "name": name,
            "email": email,
            "role_id": role_id
        }
        return self._make_request("POST", "/api/v1/users", json=data)

    def get_user(self, user_id: int) -> Dict[str, Any]:
        return self._make_request("GET", f"/api/v1/users/{user_id}")

    def validate_cnpj(self, cnpj: str) -> Dict[str, Any]:
        data = {"cnpj": cnpj}
        return self._make_request("POST", "/api/v1/validate/cnpj", json=data)

    def validate_cep(self, cep: str) -> Dict[str, Any]:
        data = {"cep": cep}
        return self._make_request("POST", "/api/v1/validate/cep", json=data)

    def get_launches(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        params = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }
        return self._make_request("GET", "/api/v1/reports/launches", params=params)

    def schedule_event(self, event_type: str, scheduled_time: datetime, metadata: Dict[str, Any]) -> Dict[str, Any]:
        data = {
            "event_type": event_type,
            "scheduled_time": scheduled_time.isoformat(),
            "metadata": metadata
        }
        return self._make_request("POST", "/api/v1/scheduler/schedule", json=data)

    def get_event_status(self, event_id: str) -> Dict[str, Any]:
        return self._make_request("GET", f"/api/v1/scheduler/status/{event_id}")
```

## 6. Limites e Quotas

- **Rate Limiting**: 100 requisições por minuto por IP
- **Tamanho Máximo de Payload**: 1MB
- **Timeout de Requisição**: 30 segundos
- **Tamanho Máximo de Resposta**: 10MB

## 7. Suporte

Para suporte técnico ou dúvidas sobre a integração:

- Email: suporte@shipay.com
- Documentação: https://docs.shipay.com
- Status da API: https://status.shipay.com 