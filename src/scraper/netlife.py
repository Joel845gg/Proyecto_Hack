"""
Scraper para Netlife - Internet inteligente para un mundo inteligente
URL: https://netlife.ec/
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
from tenacity import retry, stop_after_attempt, wait_fixed
import time
import re


class NetlifeScraper:
    """Scraper especializado para Netlife"""
    
    BASE_URL = "https://netlife.ec/"
    PLANS_URL = "https://netlife.ec/internet-hogar"  # Ajustar según estructura real
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; Benchmark360/1.0; +https://netlife.ec)'
        })
    
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def get_page(self, url: str) -> Optional[BeautifulSoup]:
        """Obtener página con retry y delay"""
        time.sleep(1)  # Delay respetuoso
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'lxml')
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None
    
    def extract_plans_from_html(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        Extraer planes de internet desde el HTML de Netlife
        Este método debe adaptarse a la estructura real de la página
        """
        plans = []
        
        # Buscar contenedores de planes (ejemplo - ajustar selectores)
        # Netlife típicamente muestra planes en cards
        plan_cards = soup.find_all('div', class_=re.compile(r'plan|card|package'))
        
        for card in plan_cards:
            plan_data = {}
            
            # Extraer nombre del plan
            name_elem = card.find(['h2', 'h3', 'h4'], class_=re.compile(r'title|name'))
            if name_elem:
                plan_data['nombre_plan'] = name_elem.get_text(strip=True)
            
            # Extraer velocidad
            speed_elem = card.find(string=re.compile(r'(\d+)\s*(?:Mbps|MB|MEGAS)', re.I))
            if speed_elem:
                speed_match = re.search(r'(\d+)\s*(?:Mbps|MB|MEGAS)', speed_elem, re.I)
                if speed_match:
                    plan_data['velocidad_download_mbps'] = float(speed_match.group(1))
            
            # Extraer precio
            price_elem = card.find(string=re.compile(r'\$\s*(\d+(?:\.\d{2})?)'))
            if price_elem:
                price_match = re.search(r'\$\s*(\d+(?:\.\d{2})?)', price_elem)
                if price_match:
                    plan_data['precio_plan'] = float(price_match.group(1))
            
            # Extraer tecnología (asumir fibra óptica por defecto)
            if 'fibra' in card.get_text().lower():
                plan_data['tecnologia'] = 'fibra_optica'
            else:
                plan_data['tecnologia'] = 'fibra_optica'  # Netlife es principalmente fibra
            
            if plan_data:
                plans.append(plan_data)
        
        return plans
    
    def scrape(self) -> List[Dict[str, Any]]:
        """Método principal para ejecutar scraping"""
        print("Scraping Netlife...")
        
        soup = self.get_page(self.PLANS_URL)
        if not soup:
            print("No se pudo acceder a Netlife")
            return []
        
        plans = self.extract_plans_from_html(soup)
        print(f"Extraídos {len(plans)} planes de Netlife")
        
        return plans


# Función de conveniencia para usar en el pipeline
def scrape_netlife() -> List[Dict[str, Any]]:
    scraper = NetlifeScraper()
    return scraper.scrape()


if __name__ == "__main__":
    # Prueba rápida
    results = scrape_netlife()
    for plan in results:
        print(plan)
