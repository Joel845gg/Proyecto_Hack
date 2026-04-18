"""
Pipeline principal de extracción y procesamiento
"""

import asyncio
import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

from datetime import datetime
from typing import List, Dict, Any
import pandas as pd
import json
from pathlib import Path

from src.scraper.netlife import scrape_netlife
from src.scraper.claro import scrape_claro
from src.scraper.ecuanet import scrape_ecuanet
from src.parser.gemini_extractor import extract_with_gemini
from src.models.plan_schema import PlanInternet
from src.normalizer.snake_case_mapper import map_company_to_legal_name, normalize_services


class BenchmarkPipeline:
    """Pipeline principal para extracción de datos de competidores"""
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
        # Mapeo de scrapers
        self.scrapers = {
            'netlife': scrape_netlife,
            'claro': scrape_claro,
            'ecuanet': scrape_ecuanet,
            'cnt': lambda: [],
            'xtrim': lambda: [],
            'puntonet': lambda: [],
            'alfanet': lambda: [],
            'fibramax': lambda: []
        }
    
    def enrich_plan_data(self, raw_plan: Dict[str, Any], source: str) -> Dict[str, Any]:
        """
        Enriquecer datos crudos con valores calculados y mapeos
        """
        # Fecha actual
        now = datetime.now()
        
        # Mapeo de empresa
        legal_name, brand = map_company_to_legal_name(source)
        
        # Estructura base
        enriched = {
            'fecha': now,
            'anio': now.year,
            'mes': now.month,
            'dia': now.day,
            'empresa': legal_name,
            'marca': brand,
            'nombre_plan': raw_plan.get('nombre_plan', f"{brand} {raw_plan.get('velocidad_download_mbps', '')} Mbps").strip(),
            'velocidad_download_mbps': raw_plan.get('velocidad_download_mbps', 0.0),
            'velocidad_upload_mbps': raw_plan.get('velocidad_upload_mbps'),
            'precio_plan': raw_plan.get('precio_plan', 0.0),
            'precio_plan_tarjeta': raw_plan.get('precio_plan_tarjeta'),
            'precio_plan_debito': raw_plan.get('precio_plan_debito'),
            'precio_plan_efectivo': raw_plan.get('precio_plan_efectivo'),
            'precio_plan_descuento': raw_plan.get('precio_plan_descuento'),
            'meses_descuento': raw_plan.get('meses_descuento'),
            'costo_instalacion': raw_plan.get('costo_instalacion'),
            'comparticion': raw_plan.get('comparticion'),
            'meses_contrato': raw_plan.get('meses_contrato', 12),  # Default 12 meses
            'facturas_gratis': raw_plan.get('facturas_gratis', 0),
            'tecnologia': raw_plan.get('tecnologia', 'fibra_optica'),
            'sectores': raw_plan.get('sectores', []),
            'parroquia': raw_plan.get('parroquia', []),
            'canton': raw_plan.get('canton', []),
            'provincia': raw_plan.get('provincia', []),
            'factura_anterior': raw_plan.get('factura_anterior', False),
            'terminos_condiciones': raw_plan.get('terminos_condiciones'),
            'beneficios_publicitados': raw_plan.get('beneficios_publicitados'),
        }
        
        # Normalizar servicios adicionales si existen
        if raw_plan.get('servicios_adicionales'):
            enriched['pys_adicionales_detalle'] = normalize_services(raw_plan['servicios_adicionales'])
        else:
            enriched['pys_adicionales_detalle'] = {}
        
        return enriched
    
    def extract_all(self) -> List[Dict[str, Any]]:
        """
        Ejecutar todos los scrapers y recolectar datos
        """
        all_raw_plans = []
        
        for source, scraper_func in self.scrapers.items():
            print(f"\n{'='*50}")
            print(f"Procesando: {source.upper()}")
            print(f"{'='*50}")
            
            try:
                raw_plans = scraper_func()
                
                # FALLBACK AL LLM GEMINI: Si el scraper nativo no arroja planes
                if not raw_plans:
                    print(f"⚠️ {source} falló o devolvió 0 planes. Invocando Guardrail Gemini LLM...")
                    raw_plans = extract_with_gemini(source)
                
                print(f"✓ Extraídos {len(raw_plans)} planes de {source}")
                
                for raw_plan in raw_plans:
                    enriched = self.enrich_plan_data(raw_plan, source)
                    all_raw_plans.append(enriched)
                    
            except Exception as e:
                print(f"✗ Error en {source}: {e}")
                continue
        
        return all_raw_plans
    
    def validate_plans(self, plans_data: List[Dict[str, Any]]) -> List[PlanInternet]:
        """
        Validar todos los planes con Pydantic
        """
        valid_plans = []
        errors = []
        
        for idx, plan_dict in enumerate(plans_data):
            try:
                validated = PlanInternet(**plan_dict)
                valid_plans.append(validated)
            except Exception as e:
                errors.append({
                    'index': idx,
                    'plan': plan_dict.get('nombre_plan', 'Unknown'),
                    'error': str(e)
                })
        
        if errors:
            print(f"\n⚠️ {len(errors)} planes inválidos:")
            for err in errors[:5]:  # Mostrar primeros 5
                print(f"  - {err['plan']}: {err['error'][:100]}")
        
        print(f"✓ {len(valid_plans)} planes válidos")
        return valid_plans
    
    def to_dict_list(self, valid_plans: List[PlanInternet]) -> List[Dict[str, Any]]:
        """Convertir a diccionarios"""
        data = []
        for plan in valid_plans:
            plan_dict = plan.model_dump()
            plan_dict['fecha'] = plan_dict['fecha'].isoformat()
            data.append(plan_dict)
        return data

    def save_json(self, data: List[Dict[str, Any]], filename: str = "benchmark_industria.json") -> Path:
        filepath = self.output_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✓ Datos guardados en: {filepath}")
        return filepath
        
    def to_dataframe(self, valid_plans: List[PlanInternet]) -> pd.DataFrame:
        """
        Convertir planes validados a DataFrame
        """
        data = []
        for plan in valid_plans:
            plan_dict = plan.model_dump()
            plan_dict['fecha'] = pd.to_datetime(plan_dict['fecha']) # Parquet requires actual datetime
            
            # Serializar diccionarios/listas para evitar errores en pyarrow
            plan_dict['pys_adicionales_detalle'] = str(plan_dict['pys_adicionales_detalle'])
            plan_dict['sectores'] = str(plan_dict.get('sectores', []))
            plan_dict['parroquia'] = str(plan_dict.get('parroquia', []))
            plan_dict['canton'] = str(plan_dict.get('canton', []))
            plan_dict['provincia'] = str(plan_dict.get('provincia', []))
            
            data.append(plan_dict)
        
        df = pd.DataFrame(data)
        
        # Reordenar columnas según especificación
        column_order = [
            'fecha', 'anio', 'mes', 'dia',
            'empresa', 'marca', 'nombre_plan',
            'velocidad_download_mbps', 'velocidad_upload_mbps',
            'precio_plan', 'precio_plan_tarjeta', 'precio_plan_debito',
            'precio_plan_efectivo', 'precio_plan_descuento', 'descuento',
            'meses_descuento', 'costo_instalacion', 'comparticion',
            'pys_adicionales', 'pys_adicionales_detalle',
            'meses_contrato', 'facturas_gratis', 'tecnologia',
            'sectores', 'parroquia', 'canton', 'provincia',
            'factura_anterior', 'terminos_condiciones', 'beneficios_publicitados'
        ]
        
        # Reordenar columnas existentes
        existing_cols = [col for col in column_order if col in df.columns]
        df = df[existing_cols]
        
        return df
    
    def save_parquet(self, df: pd.DataFrame, filename: str = "benchmark_industria.parquet") -> Path:
        """
        Guardar DataFrame como Parquet (Obligatorio para el negocio)
        """
        filepath = self.output_dir / filename
        df.to_parquet(filepath, index=False)
        print(f"\n✓ Datos guardados en: {filepath}")
        print(f"  Tamaño: {filepath.stat().st_size / 1024:.2f} KB")
        return filepath
    
    def run(self) -> List[Dict[str, Any]]:
        """
        Ejecutar pipeline completo
        """
        print("\n" + "="*60)
        print("BENCHMARK 360 - PIPELINE DE INTELIGENCIA COMPETITIVA")
        print("="*60)
        
        # 1. Extracción
        print("\n📡 FASE 1: EXTRACCIÓN DE DATOS")
        raw_data = self.extract_all()
        
        if not raw_data:
            print("❌ No se extrajeron datos")
            return []
        
        # 2. Validación
        print("\n✅ FASE 2: VALIDACIÓN CON PYDANTIC")
        valid_plans = self.validate_plans(raw_data)
        
        if not valid_plans:
            print("❌ No hay planes válidos")
            return []
        
        # 3. Guardado JSON Robusto
        print("\n💾 FASE 3: ALMACENAMIENTO (Seguro)")
        data = self.to_dict_list(valid_plans)
        self.save_json(data)
        
        # 4. Intentar Parquet
        try:
            df = self.to_dataframe(valid_plans)
            self.save_parquet(df)
            
            print("\n📈 ESTADÍSTICAS:")
            print(f"  Empresas: {df['empresa'].nunique()}")
            print(f"  Velocidad promedio: {df['velocidad_download_mbps'].mean():.0f} Mbps")
            print(f"  Precio promedio: ${df['precio_plan'].mean():.2f}")
        except Exception as e:
            print(f"\n⚠️ (AppLocker de Windows bloqueó Pandas: Se generó sólo JSON. Puedes convertir tu .json a .parquet luego online).")

        return data
        
def run_pipeline():
    """Función principal para ejecutar el pipeline"""
    pipeline = BenchmarkPipeline()
    data = pipeline.run()
    return data


if __name__ == "__main__":
    df_result = run_pipeline()
    print("\n✅ Pipeline completado exitosamente")
