# Configuração do Ambiente

Este documento descreve como configurar as variáveis de ambiente necessárias para executar a aplicação.

## Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:

```env
# Database
POSTGRES_SERVER=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=shipay

# Security
SECRET_KEY=your-secret-key-here

# External APIs
CNPJ_API_URL=https://api.cnpja.com/office
CEP_API_URL=https://viacep.com.br/ws
```

### Descrição das Variáveis

- **POSTGRES_SERVER**: Endereço do servidor PostgreSQL
- **POSTGRES_USER**: Usuário do banco de dados
- **POSTGRES_PASSWORD**: Senha do banco de dados
- **POSTGRES_DB**: Nome do banco de dados
- **SECRET_KEY**: Chave secreta para geração de tokens JWT
- **CNPJ_API_URL**: URL da API de consulta de CNPJ
- **CEP_API_URL**: URL da API de consulta de CEP

## Configuração do Banco de Dados

1. Instale o PostgreSQL se ainda não estiver instalado
2. Crie um banco de dados chamado `shipay`
3. Configure as credenciais de acesso no arquivo `.env`

## Geração da Chave Secreta

Para gerar uma chave secreta segura, você pode usar o seguinte comando Python:

```python
import secrets
print(secrets.token_urlsafe(32))
```

Copie a saída e use como valor da variável `SECRET_KEY`.

## Executando a Aplicação

Após configurar as variáveis de ambiente, você pode executar a aplicação com:

```bash
uvicorn app.main:app --reload
```

A aplicação estará disponível em `http://localhost:8000`. 