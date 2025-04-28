from pydantic import BaseModel, Field, validator, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
import secrets
import string
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
    MANAGER = "manager"

class EventStatus(str, Enum):
    PENDING = "pending"
    SCHEDULED = "scheduled"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class Address(BaseModel):
    cep: str = Field(..., description="CEP do endereço")
    logradouro: str = Field(..., description="Nome da rua/avenida")
    complemento: Optional[str] = Field(None, description="Complemento do endereço")
    bairro: str = Field(..., description="Bairro")
    cidade: str = Field(..., description="Cidade")
    uf: str = Field(..., description="Unidade Federativa")
    
    @validator('cep')
    def validate_cep(cls, v):
        # Remove caracteres não numéricos
        cep = ''.join(filter(str.isdigit, v))
        if len(cep) != 8:
            raise ValueError('CEP deve conter 8 dígitos')
        return cep

class CompanyInfo(BaseModel):
    cnpj: str = Field(..., description="CNPJ da empresa")
    razao_social: str = Field(..., description="Razão social da empresa")
    nome_fantasia: Optional[str] = Field(None, description="Nome fantasia da empresa")
    endereco: Address = Field(..., description="Endereço da empresa")

class CustomerValidationRequest(BaseModel):
    cnpj: str = Field(..., description="CNPJ do cliente")
    cep: str = Field(..., description="CEP do endereço do cliente")
    
    @validator('cnpj')
    def validate_cnpj(cls, v):
        # Remove caracteres não numéricos
        cnpj = ''.join(filter(str.isdigit, v))
        if len(cnpj) != 14:
            raise ValueError('CNPJ deve conter 14 dígitos')
        return cnpj

class CustomerValidationResponse(BaseModel):
    is_valid: bool = Field(..., description="Indica se o endereço é válido")
    company_info: CompanyInfo = Field(..., description="Informações da empresa")
    address_match: bool = Field(..., description="Indica se o endereço corresponde")
    details: Optional[str] = Field(None, description="Detalhes da validação")

class RocketLaunchBase(BaseModel):
    launch_id: str = Field(..., description="ID único do lançamento")
    name: str = Field(..., description="Nome do lançamento")
    status: str = Field(..., description="Status do lançamento")
    launch_date: datetime = Field(..., description="Data do lançamento")
    rocket_name: str = Field(..., description="Nome do foguete")
    rocket_type: str = Field(..., description="Tipo do foguete")
    launch_site: str = Field(..., description="Local de lançamento")
    mission_name: Optional[str] = Field(None, description="Nome da missão")
    mission_details: Optional[Dict[str, Any]] = Field(None, description="Detalhes da missão")
    payload_mass: Optional[float] = Field(None, description="Massa da carga útil")
    orbit: Optional[str] = Field(None, description="Órbita planejada")
    user_id: int = Field(..., description="ID do usuário que registrou o lançamento")

class RocketLaunch(RocketLaunchBase):
    id: int = Field(..., description="ID do lançamento no banco de dados")
    created_at: datetime = Field(..., description="Data de criação do registro")
    updated_at: datetime = Field(..., description="Data da última atualização")

    class Config:
        orm_mode = True

class RocketLaunchCreate(RocketLaunchBase):
    pass

class RocketLaunchResponse(RocketLaunchBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class LaunchReport(BaseModel):
    customer_id: str = Field(..., description="ID do cliente")
    period_start: datetime = Field(..., description="Início do período do relatório")
    period_end: datetime = Field(..., description="Fim do período do relatório")
    total_launches: int = Field(..., description="Total de lançamentos no período")
    successful_launches: int = Field(..., description="Lançamentos bem-sucedidos")
    failed_launches: int = Field(..., description="Lançamentos que falharam")
    average_pre_flight_time: float = Field(..., description="Tempo médio de verificação pré-lançamento")
    launches: List[RocketLaunchBase] = Field(default_factory=list, description="Lista de lançamentos detalhados")

class LaunchReportRequest(BaseModel):
    customer_id: str = Field(..., description="ID do cliente")
    period_start: datetime = Field(..., description="Início do período do relatório")
    period_end: datetime = Field(..., description="Fim do período do relatório")

class LaunchStatistics(BaseModel):
    total_launches: int
    successful_launches: int
    failed_launches: int
    success_rate: float
    rocket_types: Dict[str, int]

class UserBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="User's full name")
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=8, max_length=100, description="User's password")
    role_id: int = Field(..., ge=1, le=3, description="User's role ID (1=admin, 2=user, 3=manager)")

class UserCreate(UserBase):
    @validator('email')
    def validate_email(cls, v):
        if not v:
            raise ValueError('Email is required')
        return v.lower()

    @validator('password')
    def validate_password(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')
        return v

class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, description="User's full name")
    email: Optional[EmailStr] = Field(None, description="User's email address")
    password: Optional[str] = Field(None, description="User's password")
    role_id: Optional[int] = Field(None, description="User's role ID")

class UserResponse(BaseModel):
    id: int = Field(..., description="User's unique identifier")
    name: str = Field(..., description="User's full name")
    email: EmailStr = Field(..., description="User's email address")
    role_id: int = Field(..., description="User's role ID")
    created_at: datetime = Field(..., description="User creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="User last update timestamp")

    class Config:
        orm_mode = True

class RenderEvent(BaseModel):
    event_id: str = Field(..., description="ID único do evento")
    event_type: str = Field(..., description="Tipo do evento")
    content: Dict[str, Any] = Field(..., description="Conteúdo do evento")
    scheduled_time: datetime = Field(..., description="Data e hora agendada para execução")
    status: EventStatus = Field(default=EventStatus.SCHEDULED, description="Status do evento")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadados adicionais do evento")
    created_at: datetime = Field(default_factory=datetime.now, description="Data de criação do evento")
    updated_at: datetime = Field(default_factory=datetime.now, description="Data da última atualização")

    class Config:
        from_attributes = True

class ScheduleEventRequest(BaseModel):
    event_type: str = Field(..., description="Tipo do evento")
    content: Dict[str, Any] = Field(..., description="Conteúdo do evento a ser agendado")
    scheduled_time: datetime = Field(..., description="Data e hora para agendamento")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadados adicionais do evento")
    
    @validator('scheduled_time')
    def validate_scheduled_time(cls, v):
        if v <= datetime.now():
            raise ValueError("A data agendada deve ser futura")
        return v

class ScheduleEventResponse(BaseModel):
    event_id: str = Field(..., description="ID do evento agendado")
    status: EventStatus = Field(..., description="Status do agendamento")
    scheduled_time: datetime = Field(..., description="Data e hora agendada")

class ValidationRequest(BaseModel):
    cnpj: str = Field(..., description="CNPJ to validate")
    cep: str = Field(..., description="CEP to validate")

    @validator('cnpj')
    def validate_cnpj(cls, v):
        # Remove non-numeric characters
        v = ''.join(filter(str.isdigit, v))
        if len(v) != 14:
            raise ValueError('CNPJ must have 14 digits')
        return v

    @validator('cep')
    def validate_cep(cls, v):
        # Remove non-numeric characters
        v = ''.join(filter(str.isdigit, v))
        if len(v) != 8:
            raise ValueError('CEP must have 8 digits')
        return v

class ValidationResponse(BaseModel):
    id: int
    cnpj: str
    cep: str
    cnpj_valid: bool
    cep_valid: bool
    cnpj_data: Optional[dict] = None
    cep_data: Optional[dict] = None
    created_at: datetime

    class Config:
        orm_mode = True

class EventBase(BaseModel):
    name: str
    description: Optional[str] = None
    schedule: str
    status: EventStatus = EventStatus.PENDING

class EventCreate(EventBase):
    pass

class EventUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    schedule: Optional[str] = None
    status: Optional[EventStatus] = None

class EventResponse(EventBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class RocketLaunch(BaseModel):
    mission_name: str
    launch_date: datetime
    rocket_name: str
    success: bool
    details: Optional[str] = None