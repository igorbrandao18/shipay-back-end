# Shipay Backend API

API para validação de cadastro de clientes e gerenciamento de lançamentos de foguetes.

## Requisitos

- Python 3.8+
- Redis
- Kafka (opcional, para o serviço de renderização de vídeo)

## Instalação

1. Clone o repositório
2. Crie um ambiente virtual:
```bash
python -m venv .venv
source .venv/bin/activate  # No Windows: .venv\Scripts\activate
```
3. Instale as dependências:
```bash
pip install -r requirements.txt
```

## Executando a API

```bash
uvicorn app.main:app --reload
```

A API estará disponível em `http://localhost:8000`

## Documentação

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Estrutura do Projeto

```
shipay-back-end/
├── app/
│   ├── api/           # Endpoints e rotas
│   ├── core/          # Configurações e utilitários
│   ├── services/      # Lógica de negócio
│   └── models/        # Modelos de dados
├── tests/             # Testes
└── requirements.txt   # Dependências
```

## Funcionalidades

1. Validação de cadastro de clientes
   - Consulta de CNPJ
   - Consulta de CEP
   - Comparação de endereços

2. Gerenciamento de lançamentos de foguetes
   - Relatórios de utilização
   - Monitoramento de lançamentos

3. Renderização de vídeos
   - Agendamento de eventos
   - Processamento assíncrono

## Testes

```bash
pytest
``` 