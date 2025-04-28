from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.user import User
from app.models.schemas import UserCreate, UserResponse, UserRole
from app.core.security import get_password_hash, verify_password
from app.core.metrics import metrics
from datetime import datetime
from prometheus_client import Counter, Histogram

# Métricas Prometheus
USER_CREATED = Counter('users_created_total', 'Total de usuários criados')
USER_ERRORS = Counter('user_errors_total', 'Total de erros em operações de usuário')
USER_LATENCY = Histogram('user_operations_latency_seconds', 'Latência das operações de usuário')

class UserService:
    def __init__(self, db: Session):
        self.db = db

    def create_user(self, user: UserCreate) -> User:
        db_user = User(
            name=user.name,
            email=user.email,
            password=get_password_hash(user.password),
            role_id=user.role_id,
            created_at=datetime.utcnow()
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        metrics.inc_user_created()
        return db_user

    def get_user(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_user_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    def list_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        return self.db.query(User).offset(skip).limit(limit).all()

    def update_user(self, user_id: int, user: UserCreate) -> Optional[User]:
        db_user = self.get_user(user_id)
        if not db_user:
            return None

        update_data = user.dict(exclude_unset=True)
        if "password" in update_data:
            update_data["password"] = get_password_hash(update_data["password"])
        
        for field, value in update_data.items():
            setattr(db_user, field, value)
        
        db_user.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(db_user)
        metrics.inc_user_updated()
        return db_user

    def delete_user(self, user_id: int) -> bool:
        db_user = self.get_user(user_id)
        if not db_user:
            return False

        self.db.delete(db_user)
        self.db.commit()
        metrics.inc_user_deleted()
        return True

    def verify_password(self, user: User, password: str) -> bool:
        return verify_password(password, user.password)

    @USER_LATENCY.time()
    def get_user_by_id(self, user_id: int) -> User:
        """Busca um usuário pelo ID"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(
                    status_code=404,
                    detail="Usuário não encontrado"
                )
            return user
        except HTTPException:
            raise
        except Exception as e:
            USER_ERRORS.inc()
            metrics.inc_api_error("user", type(e).__name__)
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao buscar usuário: {str(e)}"
            )

    @USER_LATENCY.time()
    def update_user_by_id(self, user_id: int, user_data: UserCreate) -> User:
        """Atualiza um usuário"""
        try:
            user = self.get_user_by_id(user_id)
            
            # Verifica se o novo email já existe
            if user_data.email != user.email:
                existing_user = self.db.query(User).filter(User.email == user_data.email).first()
                if existing_user:
                    raise HTTPException(
                        status_code=400,
                        detail="Email já registrado"
                    )

            # Atualiza os dados
            user.name = user_data.name
            user.email = user_data.email
            if user_data.password:
                user.password = get_password_hash(user_data.password)
            user.role_id = user_data.role_id

            self.db.commit()
            self.db.refresh(user)
            metrics.inc_user_updated()
            return user

        except HTTPException:
            raise
        except Exception as e:
            USER_ERRORS.inc()
            metrics.inc_api_error("user", type(e).__name__)
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao atualizar usuário: {str(e)}"
            )

    @USER_LATENCY.time()
    def delete_user_by_id(self, user_id: int) -> None:
        """Remove um usuário"""
        try:
            user = self.get_user_by_id(user_id)
            self.db.delete(user)
            self.db.commit()
            metrics.inc_user_deleted()
        except HTTPException:
            raise
        except Exception as e:
            USER_ERRORS.inc()
            metrics.inc_api_error("user", type(e).__name__)
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao remover usuário: {str(e)}"
            ) 