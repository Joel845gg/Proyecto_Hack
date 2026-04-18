"""
Normalización de nombres de servicios a snake_case
"""

import re
from typing import Dict, List, Any


# Mapeo de categorías por keyword
CATEGORIA_MAP = {
    # Streaming
    'disney': 'streaming',
    'netflix': 'streaming',
    'hbo': 'streaming',
    'max': 'streaming',
    'prime': 'streaming',
    'amazon': 'streaming',
    'paramount': 'streaming',
    'star': 'streaming',
    'apple tv': 'streaming',
    'youtube': 'streaming',
    'spotify': 'streaming',
    'deezer': 'streaming',
    
    # Seguridad
    'kaspersky': 'seguridad',
    'norton': 'seguridad',
    'mcafee': 'seguridad',
    'avast': 'seguridad',
    'bitdefender': 'seguridad',
    'antivirus': 'seguridad',
    
    # Gaming
    'xbox': 'gaming',
    'playstation': 'gaming',
    'nintendo': 'gaming',
    'game pass': 'gaming',
    'geforce': 'gaming',
    'twitch': 'gaming',
    
    # Productividad
    'office': 'productividad',
    'google workspace': 'productividad',
    'dropbox': 'productividad',
    'onedrive': 'productividad',
    
    # Telefonía
    'telefono': 'telefonia',
    'llamadas': 'telefonia',
    'voip': 'telefonia',
}


def normalize_service_name(name: str) -> str:
    """
    Convierte un nombre de servicio a snake_case
    
    Ejemplos:
    "Disney Plus" -> "disney_plus"
    "Netflix" -> "netflix"
    "HBO Max" -> "hbo_max"
    """
    if not name:
        return ""
    
    # Limpiar y normalizar
    name = name.lower().strip()
    
    # Reemplazar caracteres especiales
    name = re.sub(r'[áä]', 'a', name)
    name = re.sub(r'[éë]', 'e', name)
    name = re.sub(r'[íï]', 'i', name)
    name = re.sub(r'[óö]', 'o', name)
    name = re.sub(r'[úü]', 'u', name)
    
    # Reemplazar & y + por 'and'
    name = re.sub(r'[&+]', ' and ', name)
    
    # Reemplazar caracteres no alfanuméricos por espacio
    name = re.sub(r'[^\w\s]', ' ', name)
    
    # Reemplazar espacios múltiples por underscore
    name = re.sub(r'\s+', '_', name)
    
    # Eliminar underscores al inicio/final
    name = name.strip('_')
    
    return name


def get_categoria_for_service(service_name: str) -> str:
    """Determinar categoría basada en el nombre del servicio"""
    service_lower = service_name.lower()
    
    for keyword, categoria in CATEGORIA_MAP.items():
        if keyword in service_lower:
            return categoria
    
    return 'otros'


def normalize_services(services_raw: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Normalizar lista de servicios a formato estándar snake_case
    
    Input:
    [
        {"nombre": "Disney Plus", "tipo_plan": "premium", "meses": 12},
        {"nombre": "Kaspersky", "tipo_plan": "total security", "meses": 24}
    ]
    
    Output:
    {
        "disney_plus": {"tipo_plan": "premium", "meses": 12, "categoria": "streaming"},
        "kaspersky": {"tipo_plan": "total_security", "meses": 24, "categoria": "seguridad"}
    }
    """
    normalized = {}
    
    for service in services_raw:
        if not isinstance(service, dict):
            continue
        
        raw_name = service.get('nombre', service.get('name', ''))
        if not raw_name:
            continue
        
        # Normalizar nombre
        normalized_name = normalize_service_name(raw_name)
        
        # Obtener tipo de plan
        tipo_plan = service.get('tipo_plan', service.get('plan_type', 'estandar'))
        tipo_plan = normalize_service_name(tipo_plan) if tipo_plan else 'estandar'
        
        # Obtener meses
        meses = service.get('meses', service.get('months', 0))
        try:
            meses = int(meses)
        except (ValueError, TypeError):
            meses = 0
        
        # Determinar categoría
        categoria = get_categoria_for_service(normalized_name)
        
        normalized[normalized_name] = {
            'tipo_plan': tipo_plan,
            'meses': meses,
            'categoria': categoria
        }
    
    return normalized


def map_company_to_legal_name(company_marca: str) -> tuple[str, str]:
    """
    Mapear nombre de marca a nombre legal según Superintendencia
    
    Returns: (empresa_legal, marca)
    """
    mapping = {
        'netlife': ('NETLIFE S.A.', 'Netlife'),
        'claro': ('CLARO S.A.', 'Claro'),
        'ecuanet': ('ECUANET S.A.', 'Ecuanet'),
        'cnt': ('CORPORACIÓN NACIONAL DE TELECOMUNICACIONES CNT EP', 'CNT'),
        'xtrim': ('XTRIM S.A.', 'Xtrim'),
        'puntonet': ('PUNTO NET S.A.', 'Puntonet'),
        'celerity': ('PUNTO NET S.A.', 'Celerity'),
        'alfanet': ('ALFANET S.A.', 'Alfanet'),
        'fibramax': ('FIBRAMAX S.A.', 'Fibramax'),
        'megadatos': ('MEGADATOS S.A.', 'Megadatos'),
    }
    
    company_lower = company_marca.lower()
    for key, (legal, brand) in mapping.items():
        if key in company_lower:
            return legal, brand
    
    # Default: capitalizar y asumir mismo nombre
    return company_marca.upper() + ' S.A.', company_marca.capitalize()


# Ejemplo de uso
if __name__ == "__main__":
    test_services = [
        {"nombre": "Disney Plus", "tipo_plan": "Premium", "meses": 12},
        {"nombre": "Netflix", "tipo_plan": "Standard", "meses": "6"},
        {"nombre": "Kaspersky Antivirus", "tipo_plan": "Total Security", "meses": 24},
    ]
    
    result = normalize_services(test_services)
    print("Servicios normalizados:")
    for name, details in result.items():
        print(f"  {name}: {details}")
    
    print("\nMapeo de empresas:")
    for test in ['netlife', 'claro', 'ecuanet']:
        legal, brand = map_company_to_legal_name(test)
        print(f"  {test} -> {legal} / {brand}")
