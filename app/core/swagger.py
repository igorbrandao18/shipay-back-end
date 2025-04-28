from fastapi.openapi.utils import get_openapi
from fastapi import FastAPI

def custom_openapi(app: FastAPI):
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Shipay Backend API",
        version="1.0.0",
        description="""
        API para o desafio Shipay Backend.
        
        ## Endpoints
        
        ### Usuários
        - POST /users - Criar novo usuário
        - GET /users/{id} - Buscar usuário por ID
        - PUT /users/{id} - Atualizar usuário
        - DELETE /users/{id} - Remover usuário
        
        ### Validação
        - POST /validate/cnpj - Validar CNPJ
        - POST /validate/cep - Validar CEP
        
        ### Relatórios
        - GET /reports/launches - Relatório de lançamentos
        - GET /reports/statistics - Estatísticas de lançamentos
        
        ### Agendador
        - POST /scheduler/schedule - Agendar evento
        - GET /scheduler/status/{event_id} - Status do evento
        """,
        routes=app.routes,
    )

    # Configuração de segurança
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }

    # Adiciona autenticação em todos os endpoints
    for path in openapi_schema["paths"].values():
        for method in path.values():
            method["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema 