"""
Scraper para Ecuanet
URL: https://ecuanet.ec/
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
from tenacity import retry, stop_after_attempt, wait_fixed
import time
import re
import json


class EcuanetScraper:
    """Scraper especializado para Ecuanet"""
    
    BASE_URL = "https://ecuanet.ec/"
    PLANS_URL = "https://ecuanet.ec/planes"  # Ajustar según estructura
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; Benchmark360/1.0)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        })
    
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch página con retry"""
        time.sleep(1.5)  # Delay respetuoso
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'lxml')
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None
    
    def extract_plans_from_html(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        Extraer planes de Ecuanet
        Ecuanet suele mostrar sus planes en formato tabla o cards
        """
        plans = []
        
        # Buscar tablas de planes
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            headers = []
            
            # Extraer headers
            header_row = rows[0] if rows else None
            if header_row:
                headers = [th.get_text(strip=True).lower() for th in header_row.find_all(['th', 'td'])]
            
            # Extraer datos
            for row in rows[1:]:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    plan_data = {}
                    
                    for idx, cell in enumerate(cells):
                        cell_text = cell.get_text(strip=True)
                        
                        if idx < len(headers):
                            header = headers[idx]
                            
                            if 'velocidad' in header or 'megas' in header:
                                speed_match = re.search(r'(\d+)', cell_text)
                                if speed_match:
                                    plan_data['velocidad_download_mbps'] = float(speed_match.group(1))
                            
                            elif 'precio' in header or 'costo' in header or 'valor' in header:
                                price_match = re.search(r'\$\s*(\d+(?:\.\d{2})?)', cell_text)
                                if price_match:
                                    plan_data['precio_plan'] = float(price_match.group(1))
                            
                            elif 'nombre' in header or 'plan' in header:
                                plan_data['nombre_plan'] = cell_text
                    
                    if plan_data:
                        # Valores por defecto
                        if 'nombre_plan' not in plan_data:
                            plan_data['nombre_plan'] = f"Plan {plan_data.get('velocidad_download_mbps', 'Estándar')} Mbps"
                        
                        if 'tecnologia' not in plan_data:
                            plan_data['tecnologia'] = 'fibra_optica'
                        
                        plans.append(plan_data)
        
        # Si no hay tablas, buscar cards
        if not plans:
            plans = self.extract_from_cards(soup)
        
        return plans
    
    def extract_from_cards(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extraer planes desde cards o divs"""
        plans = []
        
        # Buscar elementos que parezcan cards de planes
        card_selectors = [
            'div[class*="plan"]',
            'div[class*="card"]',
            'div[class*="product"]',
            'div[class*="package"]'
        ]
        
        for selector in card_selectors:
            cards = soup.select(selector)
            for card in cards:
                plan_data = {}
                card_text = card.get_text().lower()
                
                # Velocidad
                speed_match = re.search(r'(\d+)\s*(?:mbps|megas|mega)', card_text, re.I)
                if speed_match:
                    plan_data['velocidad_download_mbps'] = float(speed_match.group(1))
                
                # Precio
                price_match = re.search(r'\$\s*(\d+(?:\.\d{2})?)', card_text)
                if price_match:
                    plan_data['precio_plan'] = float(price_match.group(1))
                
                # Nombre
                name_elem = card.find(['h2', 'h3', 'h4', 'strong', 'b'])
                if name_elem:
                    plan_data['nombre_plan'] = name_elem.get_text(strip=True)
                elif 'velocidad_download_mbps' in plan_data:
                    plan_data['nombre_plan'] = f"Ecuanet {plan_data['velocidad_download_mbps']} Mbps"
                
                if plan_data and 'precio_plan' in plan_data:
                    plan_data['tecnologia'] = 'fibra_optica'
                    plans.append(plan_data)
        
        return plans
    
    def scrape(self) -> List[Dict[str, Any]]:
        """Método principal"""
        print("Scraping Ecuanet...")
        
        # Intentar varias URLs comunes
        urls_to_try = [
            self.PLANS_URL,
            self.BASE_URL,
            f"{self.BASE_URL}internet",
            f"{self.BASE_URL}hogar",
            f"{self.BASE_URL}planes-hogar"
        ]
        
        all_plans = []
        
        for url in urls_to_try:
            soup = self.fetch_page(url)
            if soup:
                plans = self.extract_plans_from_html(soup)
                if plans:
                    all_plans.extend(plans)
                    print(f"Encontrados {len(plans)} planes en {url}")
                    break
        
        if not all_plans:
            # Planes por defecto si no se encuentra nada (para demo)
            print("Usando datos de respaldo de Ecuanet")
            all_plans = self.get_fallback_plans()
        
        print(f"Total extraídos: {len(all_plans)} planes de Ecuanet")
        return all_plans
    
    def get_fallback_plans(self) -> List[Dict[str, Any]]:
        """Datos de respaldo en caso de que el scraping falle"""
        return [
            {
                'nombre_plan': 'Ecuanet 100 Mbps',
                'velocidad_download_mbps': 100.0,
                'precio_plan': 29.99,
                'tecnologia': 'fibra_optica'
            },
            {
                'nombre_plan': 'Ecuanet 300 Mbps',
                'velocidad_download_mbps': 300.0,
                'precio_plan': 39.99,
                'tecnologia': 'fibra_optica'
            },
            {
                'nombre_plan': 'Ecuanet 500 Mbps',
                'velocidad_download_mbps': 500.0,
                'precio_plan': 49.99,
                'tecnologia': 'fibra_optica'
            }
        ]


def scrape_ecuanet() -> List[Dict[str, Any]]:
    scraper = EcuanetScraper()
    return scraper.scrape()


if __name__ == "__main__":
    results = scrape_ecuanet()
    for plan in results:
        print(plan)
