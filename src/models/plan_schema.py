"""
Modelos Pydantic para validación de datos de planes de internet
"""

from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime
from typing import List, Dict, Optional, Any
import re


class ServicioAdicional(BaseModel):
    """Modelo para servicios adicionales (streaming, seguridad, etc.)"""
    tipo_plan: str = Field(..., description="Nombre exacto del plan del servicio")
    meses: int = Field(0, description="Cantidad de meses del beneficio")
    categoria: str = Field(..., description="Categoría: streaming, seguridad, gaming, etc.")


class PlanInternet(BaseModel):
    """Modelo principal para planes de internet"""
    
    # Fecha y particionamiento
    fecha: datetime = Field(default_factory=datetime.now)
    anio: int = Field(..., description="Año de extracción")
    mes: int = Field(..., description="Mes de extracción")
    dia: int = Field(..., description="Día de extracción")
    
    # Identificación
    empresa: str = Field(..., description="Nombre legal según Superintendencia")
    marca: str = Field(..., description="Marca comercial")
    nombre_plan: str = Field(..., description="Nombre del plan")
    
    # Velocidades
    velocidad_download_mbps: float = Field(..., gt=0)
    velocidad_upload_mbps: Optional[float] = Field(None, description="Velocidad de subida")
    
    # Precios
    precio_plan: float = Field(..., gt=0, description="Precio base sin IVA")
    precio_plan_tarjeta: Optional[float] = Field(None)
    precio_plan_debito: Optional[float] = Field(None)
    precio_plan_efectivo: Optional[float] = Field(None)
    precio_plan_descuento: Optional[float] = Field(None)
    
    # Descuentos
    descuento: Optional[float] = Field(None, ge=0, le=1)
    meses_descuento: Optional[int] = Field(None, ge=0)
    
    # Costos y términos
    costo_instalacion: Optional[float] = Field(None)
    comparticion: Optional[str] = Field(None, description="Compartición del servicio")
    meses_contrato: Optional[int] = Field(None)
    facturas_gratis: Optional[int] = Field(None)
    
    # Servicios adicionales
    pys_adicionales: int = Field(0, description="Cantidad de servicios adicionales")
    pys_adicionales_detalle: Dict[str, ServicioAdicional] = Field(default_factory=dict)
    
    # Tecnología
    tecnologia: str = Field(..., description="fibra_optica, cobre, etc.")
    
    # Geo-áreas con beneficios
    sectores: List[str] = Field(default_factory=list)
    parroquia: List[str] = Field(default_factory=list)
    canton: List[str] = Field(default_factory=list)
    provincia: List[str] = Field(default_factory=list)
    
    # Condiciones
    factura_anterior: bool = Field(False)
    terminos_condiciones: Optional[str] = Field(None)
    beneficios_publicitados: Optional[str] = Field(None)
    
    @field_validator('anio', 'mes', 'dia', mode='before')
    @classmethod
    def validate_date_parts(cls, v: int, info) -> int:
        """Validar partes de fecha"""
        if v is None and info.field_name == 'anio':
            return datetime.now().year
        elif v is None and info.field_name == 'mes':
            return datetime.now().month
        elif v is None and info.field_name == 'dia':
            return datetime.now().day
        
        if info.field_name == 'anio' and (v < 2020 or v > 2030):
            raise ValueError(f'Año inválido: {v}')
        if info.field_name == 'mes' and (v < 1 or v > 12):
            raise ValueError(f'Mes inválido: {v}')
        if info.field_name == 'dia' and (v < 1 or v > 31):
            raise ValueError(f'Día inválido: {v}')
        return v
    
    @field_validator('velocidad_download_mbps')
    @classmethod
    def validate_speed(cls, v: float) -> float:
        """Validar velocidad razonable"""
        if v <= 0 or v > 10000:
            raise ValueError(f'Velocidad inválida: {v} Mbps')
        return v
    
    @field_validator('precio_plan')
    @classmethod
    def validate_price(cls, v: float) -> float:
        """Validar precio razonable"""
        if v <= 0 or v > 1000:
            raise ValueError(f'Precio inválido: ${v}')
        return v
    
    @model_validator(mode='after')
    def calculate_discount(self) -> 'PlanInternet':
        """Calcular descuento automáticamente si no está presente"""
        if self.precio_plan_descuento is not None and self.precio_plan > 0:
            if self.descuento is None:
                self.descuento = (self.precio_plan - self.precio_plan_descuento) / self.precio_plan
        return self
    
    @model_validator(mode='after')
    def set_pys_count(self) -> 'PlanInternet':
        """Establecer cantidad de servicios adicionales"""
        self.pys_adicionales = len(self.pys_adicionales_detalle)
        return self
    
    class Config:
        json_schema_extra = {
            "example": {
                "empresa": "NETLIFE S.A.",
                "marca": "Netlife",
                "nombre_plan": "Netlife 500",
                "velocidad_download_mbps": 500.0,
                "precio_plan": 49.99,
                "tecnologia": "fibra_optica"
            }
        }
