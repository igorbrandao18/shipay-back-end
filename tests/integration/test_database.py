import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.user import User
from app.core.config import settings

@pytest.fixture(scope="session")
def db_engine():
    """Cria uma engine de banco de dados para testes."""
    return create_engine(settings.DATABASE_URL)

@pytest.fixture(scope="session")
def db_session_factory(db_engine):
    """Cria uma factory de sessões do banco de dados."""
    return sessionmaker(bind=db_engine)

@pytest.fixture(scope="function")
def db_session(db_session_factory):
    """Cria uma sessão do banco de dados para cada teste."""
    session = db_session_factory()
    yield session
    session.rollback()
    session.close()

def test_create_user(db_session):
    """Testa a criação de um usuário no banco de dados."""
    user = User(
        name="Test User",
        email="test@example.com",
        role_id=1
    )
    db_session.add(user)
    db_session.commit()
    
    assert user.id is not None
    assert user.name == "Test User"
    assert user.email == "test@example.com"
    assert user.role_id == 1

def test_read_user(db_session):
    """Testa a leitura de um usuário do banco de dados."""
    user = User(
        name="Test User",
        email="test@example.com",
        role_id=1
    )
    db_session.add(user)
    db_session.commit()
    
    retrieved_user = db_session.query(User).filter_by(email="test@example.com").first()
    assert retrieved_user is not None
    assert retrieved_user.name == "Test User"

def test_update_user(db_session):
    """Testa a atualização de um usuário no banco de dados."""
    user = User(
        name="Test User",
        email="test@example.com",
        role_id=1
    )
    db_session.add(user)
    db_session.commit()
    
    user.name = "Updated User"
    db_session.commit()
    
    updated_user = db_session.query(User).filter_by(email="test@example.com").first()
    assert updated_user.name == "Updated User"

def test_delete_user(db_session):
    """Testa a exclusão de um usuário do banco de dados."""
    user = User(
        name="Test User",
        email="test@example.com",
        role_id=1
    )
    db_session.add(user)
    db_session.commit()
    
    db_session.delete(user)
    db_session.commit()
    
    deleted_user = db_session.query(User).filter_by(email="test@example.com").first()
    assert deleted_user is None

def test_user_relationships(db_session):
    """Testa os relacionamentos do modelo User."""
    user = User(
        name="Test User",
        email="test@example.com",
        role_id=1
    )
    db_session.add(user)
    db_session.commit()
    
    assert user.role is not None
    assert user.role.id == 1

def test_user_constraints(db_session):
    """Testa as constraints do modelo User."""
    # Teste de email único
    user1 = User(
        name="Test User 1",
        email="test@example.com",
        role_id=1
    )
    db_session.add(user1)
    db_session.commit()
    
    user2 = User(
        name="Test User 2",
        email="test@example.com",
        role_id=1
    )
    db_session.add(user2)
    
    with pytest.raises(Exception):
        db_session.commit()
    
    db_session.rollback()

def test_user_validation(db_session):
    """Testa a validação de dados do modelo User."""
    # Teste de email inválido
    with pytest.raises(ValueError):
        User(
            name="Test User",
            email="invalid_email",
            role_id=1
        )
    
    # Teste de nome vazio
    with pytest.raises(ValueError):
        User(
            name="",
            email="test@example.com",
            role_id=1
        )
    
    # Teste de role_id inválido
    with pytest.raises(ValueError):
        User(
            name="Test User",
            email="test@example.com",
            role_id=0
        ) 