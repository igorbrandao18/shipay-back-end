# Padrões de Design para Normalização de Serviços

## 1. Repository Pattern

### Descrição
O padrão Repository abstrai a camada de acesso a dados, fornecendo uma interface limpa para operações de banco de dados.

### Implementação
```python
from abc import ABC, abstractmethod
from typing import List, Optional

class Repository(ABC):
    @abstractmethod
    def get(self, id: int) -> Optional[Any]:
        pass
    
    @abstractmethod
    def list(self) -> List[Any]:
        pass
    
    @abstractmethod
    def create(self, entity: Any) -> Any:
        pass
    
    @abstractmethod
    def update(self, id: int, entity: Any) -> Any:
        pass
    
    @abstractmethod
    def delete(self, id: int) -> bool:
        pass

class UserRepository(Repository):
    def __init__(self, db: SQLAlchemy):
        self.db = db
        
    def get(self, id: int) -> Optional[User]:
        return self.db.session.query(User).get(id)
```

### Benefícios
- Separação clara de responsabilidades
- Facilita testes unitários
- Permite trocar implementação de banco de dados
- Centraliza lógica de acesso a dados

## 2. Service Layer Pattern

### Descrição
O padrão Service Layer encapsula a lógica de negócios, coordenando operações entre diferentes repositórios.

### Implementação
```python
class UserService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
        
    def create_user(self, user_data: dict) -> User:
        # Validações de negócio
        if not self._validate_email(user_data['email']):
            raise ValueError("Email inválido")
            
        # Criação do usuário
        user = User(**user_data)
        return self.user_repository.create(user)
        
    def _validate_email(self, email: str) -> bool:
        # Lógica de validação
        pass
```

### Benefícios
- Separa lógica de negócios de acesso a dados
- Facilita reuso de código
- Melhora testabilidade
- Centraliza regras de negócio

## 3. Factory Pattern

### Descrição
O padrão Factory centraliza a criação de objetos complexos, encapsulando a lógica de instanciação.

### Implementação
```python
class DatabaseFactory:
    @staticmethod
    def create_database(config: dict) -> Database:
        db_type = config.get('type', 'postgresql')
        
        if db_type == 'postgresql':
            return PostgreSQLDatabase(config)
        elif db_type == 'mysql':
            return MySQLDatabase(config)
        else:
            raise ValueError(f"Tipo de banco não suportado: {db_type}")

class Database(ABC):
    @abstractmethod
    def connect(self):
        pass
    
    @abstractmethod
    def disconnect(self):
        pass
```

### Benefícios
- Encapsula lógica de criação
- Facilita extensão
- Reduz acoplamento
- Centraliza configuração

## 4. Strategy Pattern

### Descrição
O padrão Strategy permite definir uma família de algoritmos, encapsulando cada um e tornando-os intercambiáveis.

### Implementação
```python
class ExportStrategy(ABC):
    @abstractmethod
    def export(self, data: List[Any], file_path: str):
        pass

class ExcelExportStrategy(ExportStrategy):
    def export(self, data: List[Any], file_path: str):
        # Implementação para Excel
        pass

class CSVExportStrategy(ExportStrategy):
    def export(self, data: List[Any], file_path: str):
        # Implementação para CSV
        pass

class Exporter:
    def __init__(self, strategy: ExportStrategy):
        self.strategy = strategy
        
    def export(self, data: List[Any], file_path: str):
        self.strategy.export(data, file_path)
```

### Benefícios
- Flexibilidade para trocar algoritmos
- Facilita adição de novos formatos
- Separa responsabilidades
- Melhora testabilidade

## 5. Observer Pattern

### Descrição
O padrão Observer define uma dependência um-para-muitos entre objetos, onde quando um objeto muda de estado, todos os seus dependentes são notificados.

### Implementação
```python
class Event:
    def __init__(self, name: str, data: dict):
        self.name = name
        self.data = data

class EventObserver(ABC):
    @abstractmethod
    def update(self, event: Event):
        pass

class EventManager:
    def __init__(self):
        self._observers = []
        
    def attach(self, observer: EventObserver):
        self._observers.append(observer)
        
    def notify(self, event: Event):
        for observer in self._observers:
            observer.update(event)

class UserCreatedObserver(EventObserver):
    def update(self, event: Event):
        if event.name == 'user_created':
            # Lógica para notificar sistemas externos
            pass
```

### Benefícios
- Baixo acoplamento entre objetos
- Suporte a múltiplos observadores
- Facilita extensão
- Melhora manutenibilidade

## 6. Decorator Pattern

### Descrição
O padrão Decorator permite adicionar responsabilidades a objetos dinamicamente, sem alterar sua estrutura.

### Implementação
```python
def retry(max_attempts: int = 3):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise
                    time.sleep(2 ** attempt)
            return None
        return wrapper
    return decorator

class UserService:
    @retry(max_attempts=3)
    def create_user(self, user_data: dict) -> User:
        # Lógica de criação
        pass
```

### Benefícios
- Adiciona funcionalidades sem herança
- Mantém código limpo
- Facilita composição
- Melhora reusabilidade

## 7. Dependency Injection

### Descrição
O padrão Dependency Injection permite injetar dependências em um objeto, em vez de criá-las internamente.

### Implementação
```python
class Container:
    def __init__(self):
        self._services = {}
        
    def register(self, name: str, service: Any):
        self._services[name] = service
        
    def get(self, name: str) -> Any:
        return self._services.get(name)

class UserController:
    def __init__(self, container: Container):
        self.user_service = container.get('user_service')
        
    def create_user(self, user_data: dict):
        return self.user_service.create_user(user_data)
```

### Benefícios
- Reduz acoplamento
- Facilita testes
- Melhora manutenibilidade
- Permite configuração flexível

## Benefícios Gerais da Implementação

1. **Manutenibilidade**
   - Código mais organizado
   - Responsabilidades bem definidas
   - Facilidade de manutenção

2. **Testabilidade**
   - Facilidade para criar testes
   - Isolamento de componentes
   - Mocking simplificado

3. **Extensibilidade**
   - Fácil adição de novas funcionalidades
   - Baixo acoplamento
   - Interface bem definida

4. **Performance**
   - Otimização de recursos
   - Caching facilitado
   - Consultas eficientes

5. **Segurança**
   - Controle de acesso centralizado
   - Validações consistentes
   - Logging estruturado

## Próximos Passos

1. Implementar padrões gradualmente
2. Refatorar código existente
3. Adicionar testes unitários
4. Documentar decisões de design
5. Treinar equipe nos padrões 