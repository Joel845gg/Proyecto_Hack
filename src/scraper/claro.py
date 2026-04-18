"""
Scraper para Claro Ecuador
URL: https://www.claro.com.ec/personas/
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from typing import List, Dict, Any, Optional
import time
import re


class ClaroScraper:
    """Scraper especializado para Claro usando Selenium"""
    
    BASE_URL = "https://www.claro.com.ec/personas/"
    PLANS_SECTION = "internet-hogar"  # Sección específica
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.driver = None
    
    def setup_driver(self):
        """Configurar WebDriver"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(10)
    
    def get_plans_page(self) -> bool:
        """Navegar a la página de planes"""
        try:
            self.driver.get(self.BASE_URL)
            
            # Buscar enlace a planes de internet
            internet_link = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, "Internet"))
            )
            internet_link.click()
            time.sleep(2)
            
            return True
        except Exception as e:
            print(f"Error navegando a planes de Claro: {e}")
            return False
    
    def extract_plans(self) -> List[Dict[str, Any]]:
        """Extraer planes del DOM"""
        plans = []
        
        try:
            # Esperar a que carguen las cards de planes
            plan_cards = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "[class*='plan'], [class*='card'], [class*='product']"))
            )
            
            for card in plan_cards[:10]:  # Limitar para evitar sobrecarga
                plan_data = {}
                card_text = card.text.lower()
                
                # Extraer nombre del plan
                name_elem = card.find_elements(By.CSS_SELECTOR, "h2, h3, h4, [class*='title']")
                if name_elem:
                    plan_data['nombre_plan'] = name_elem[0].text.strip()
                
                # Extraer velocidad (Claro típicamente muestra "300 Megas")
                speed_match = re.search(r'(\d+)\s*(?:megas|mbps|mega)', card_text, re.I)
                if speed_match:
                    plan_data['velocidad_download_mbps'] = float(speed_match.group(1))
                
                # Extraer precio
                price_match = re.search(r'\$\s*(\d+(?:\.\d{2})?)', card_text)
                if price_match:
                    plan_data['precio_plan'] = float(price_match.group(1))
                
                # Detectar promociones
                if 'promo' in card_text or 'descuento' in card_text:
                    discount_match = re.search(r'(\d+)%', card_text)
                    if discount_match:
                        plan_data['descuento'] = float(discount_match.group(1)) / 100
                
                # Tecnología
                if 'fibra' in card_text:
                    plan_data['tecnologia'] = 'fibra_optica'
                elif 'cobre' in card_text:
                    plan_data['tecnologia'] = 'cobre'
                else:
                    plan_data['tecnologia'] = 'fibra_optica'
                
                if plan_data and 'nombre_plan' in plan_data:
                    plans.append(plan_data)
                    
        except Exception as e:
            print(f"Error extrayendo planes de Claro: {e}")
        
        return plans
    
    def scrape(self) -> List[Dict[str, Any]]:
        """Método principal"""
        print("Scraping Claro...")
        
        try:
            self.setup_driver()
            
            if not self.get_plans_page():
                return []
            
            plans = self.extract_plans()
            print(f"Extraídos {len(plans)} planes de Claro")
            
            return plans
            
        finally:
            if self.driver:
                self.driver.quit()
    
    def scrape_with_fallback(self) -> List[Dict[str, Any]]:
        """
        Intentar primero con Selenium, fallback a requests si es necesario
        """
        try:
            return self.scrape()
        except Exception as e:
            print(f"Selenium falló para Claro: {e}")
            # Fallback: scraping básico con requests
            return self.scrape_requests_fallback()
    
    def scrape_requests_fallback(self) -> List[Dict[str, Any]]:
        """Fallback simple con requests si Selenium no funciona"""
        import requests
        from bs4 import BeautifulSoup
        
        plans = []
        try:
            response = requests.get(self.BASE_URL, timeout=30)
            soup = BeautifulSoup(response.content, 'lxml')
            
            # Búsqueda básica de precios y velocidades
            price_pattern = re.compile(r'\$\s*(\d+(?:\.\d{2})?)')
            prices = soup.find_all(string=price_pattern)
            
            for price_text in prices[:5]:
                plan_data = {
                    'nombre_plan': 'Plan Claro Estándar',
                    'precio_plan': float(price_pattern.search(price_text).group(1)),
                    'tecnologia': 'fibra_optica'
                }
                plans.append(plan_data)
            
            print(f"Fallback: extraídos {len(plans)} planes de Claro")
        except Exception as e:
            print(f"Fallback también falló: {e}")
        
        return plans


def scrape_claro() -> List[Dict[str, Any]]:
    scraper = ClaroScraper(headless=True)
    return scraper.scrape_with_fallback()


if __name__ == "__main__":
    results = scrape_claro()
    for plan in results:
        print(plan)
