from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from datetime import datetime
import logging
import json
import time
from typing import List

class InstagramBot:
    def wait_for_element(self, by, value, timeout=10, visible=True):
        """Espera por un elemento y lo retorna cuando está disponible"""
        try:
            if visible:
                element = WebDriverWait(self.driver, timeout).until(
                    EC.visibility_of_element_located((by, value))
                )
            else:
                element = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((by, value))
                )
            return element
        except TimeoutException:
            logging.warning(f"Timeout esperando elemento: {value}")
            return None
        except Exception as e:
            logging.error(f"Error esperando elemento {value}: {str(e)}")
            return None

    def verify_instagram_session(self) -> bool:
        """Verifica que estamos en Instagram y la sesión está activa"""
        try:
            logging.info("Verificando sesión de Instagram...")
            
            # Ir a Instagram
            self.driver.get('https://www.instagram.com/')
            time.sleep(3)
            
            # Verificar URL
            if 'instagram.com' not in self.driver.current_url:
                logging.error(f"URL incorrecta: {self.driver.current_url}")
                return False
                
            # Verificar elementos de usuario logueado
            logged_in_elements = [
                (By.CSS_SELECTOR, 'svg[aria-label="Inicio"]'),
                (By.CSS_SELECTOR, 'svg[aria-label="Nueva publicación"]'),
                (By.XPATH, f"//a[contains(@href, '/{self.config['USERNAME']}/')]"),
                (By.XPATH, "//span[contains(text(), 'Crear')]")
            ]
            
            for by, selector in logged_in_elements:
                try:
                    element = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((by, selector))
                    )
                    if element.is_displayed():
                        logging.info(f"Elemento de sesión encontrado: {selector}")
                        return True
                except:
                    continue
                    
            # Si llegamos aquí, no encontramos elementos de sesión
            logging.warning("No se encontraron elementos de sesión activa")
            
            # Verificar si hay elementos de login
            login_elements = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Iniciar')]")
            if login_elements:
                logging.error("Se encontró pantalla de login")
                return False
                
            return False
            
        except Exception as e:
            logging.error(f"Error verificando sesión: {str(e)}")
            return False
        
    def setup_driver(self) -> None:
        """Configura el driver con tiempos de espera más cortos"""
        options = webdriver.ChromeOptions()
        options.add_argument('--disable-notifications')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920,1080')
        
        service = Service(self.config['CHROME_DRIVER_PATH'])
        self.driver = webdriver.Chrome(service=service, options=options)
        # Reducir el tiempo de espera global
        self.driver.implicitly_wait(10)
        self.wait = WebDriverWait(self.driver, 10)  # Reducir a 10 segundos

    def verify_page_loaded(self) -> bool:
        """Verifica si la página se cargó correctamente"""
        try:
            # Esperar a que desaparezca el spinner de carga
            WebDriverWait(self.driver, 10).until_not(
                EC.presence_of_element_located((By.XPATH, '//div[@role="progressbar"]'))
            )
            
            # Verificar que estamos en Instagram
            assert "instagram.com" in self.driver.current_url
            
            # Verificar que la página no muestra error
            error_messages = self.driver.find_elements(By.XPATH, '//h2[contains(text(), "Error")]')
            if error_messages:
                logging.error(f"Página muestra error: {error_messages[0].text}")
                return False
                
            return True
        except Exception as e:
            logging.error(f"Error verificando la página: {str(e)}")
            return False

    def load_cookies(self) -> bool:
        """Carga las cookies y verifica la sesión"""
        try:
            logging.info("Iniciando carga de cookies...")
            
            # Primero ir a Instagram
            self.driver.get('https://www.instagram.com/')
            time.sleep(3)
            
            # Cargar cookies
            with open(self.config['COOKIE_FILE_PATH'], 'r') as file:
                cookies = json.load(file)
                for cookie in cookies:
                    try:
                        # Asegurar que el dominio es correcto
                        if 'domain' in cookie and not cookie['domain'].endswith('instagram.com'):
                            cookie['domain'] = '.instagram.com'
                        # Asegurar sameSite
                        if 'sameSite' not in cookie or cookie['sameSite'] not in ['Strict', 'Lax', 'None']:
                            cookie['sameSite'] = 'Lax'
                        self.driver.add_cookie(cookie)
                    except Exception as e:
                        logging.warning(f"Error añadiendo cookie: {str(e)}")
                        
            # Recargar la página
            self.driver.refresh()
            time.sleep(3)
            
            return True
            
        except Exception as e:
            logging.error(f"Error cargando cookies: {str(e)}")
            return False
            
    def check_login_status(self) -> bool:
        """Verifica el estado de login con timeouts más cortos"""
        try:
            logging.info("Verificando estado de login...")
            
            # Ir a Instagram home
            self.driver.get('https://www.instagram.com/')
            time.sleep(3)
            
            # Verificar elementos que indican sesión activa
            login_indicators = [
                (By.XPATH, "//span[contains(text(), 'Crear')]"),
                (By.XPATH, "//div[@role='menuitem']"),
                (By.CSS_SELECTOR, "svg[aria-label='Inicio']"),
                (By.XPATH, f"//a[contains(@href, '/{self.config['USERNAME']}/')]")
            ]
            
            for by, selector in login_indicators:
                try:
                    # Usar un timeout más corto para cada verificación
                    element = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((by, selector))
                    )
                    if element.is_displayed():
                        logging.info(f"Sesión detectada usando selector: {selector}")
                        return True
                except:
                    continue
            
            # Verificar si hay botón de login (indica que no hay sesión)
            try:
                login_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Iniciar')]")
                if login_button.is_displayed():
                    logging.warning("Se detectó botón de login - No hay sesión activa")
                    return False
            except:
                pass
                
            return False
            
        except Exception as e:
            logging.error(f"Error verificando login: {str(e)}")
            return False

    def handle_login(self) -> bool:
        """Maneja el proceso completo de login"""
        try:
            # Cargar cookies
            if not self.load_cookies():
                logging.error("Error cargando cookies")
                return False
                
            # Verificar login
            if not self.check_login_status():
                logging.error("No se detectó sesión activa después de cargar cookies")
                return False
                
            return True
            
        except Exception as e:
            logging.error(f"Error en proceso de login: {str(e)}")
            return False
        
    def extract_post_code(self, url: str) -> str:
        """Extrae el código de la publicación de una URL de Instagram"""
        try:
            # Eliminar posibles parámetros de la URL
            clean_url = url.split('?')[0]
            # Eliminar trailing slash si existe
            clean_url = clean_url.rstrip('/')
            # Obtener el código de la publicación
            parts = clean_url.split('/')
            # El código suele estar después de '/p/' en la URL
            if 'p' in parts:
                p_index = parts.index('p')
                if p_index + 1 < len(parts):
                    return parts[p_index + 1]
        except Exception as e:
            logging.error(f"Error extrayendo código de post: {str(e)}")
        return None
        
    def verify_post_before_likes(self) -> bool:
        """Verifica que la publicación está lista para obtener likes"""
        try:
            logging.info(f"Verificando publicación en URL actual: {self.driver.current_url}")
            
            # Verificar que la publicación está cargada
            article = self.wait_for_element(By.TAG_NAME, 'article', timeout=10)
            if not article:
                logging.error("No se encontró el artículo de la publicación")
                return False

            # Verificar elementos clave de la publicación
            key_elements = {
                'imagen': (By.TAG_NAME, 'img'),
                'acciones': (By.XPATH, '//section[contains(@class, "_ae5q")]'),
                'likes': (By.XPATH, '//button[contains(@class, "_abl-")]//span[contains(text(), "Me gusta")]')
            }

            elements_found = []
            for name, (by, selector) in key_elements.items():
                element = self.wait_for_element(by, selector, timeout=5)
                if element and element.is_displayed():
                    elements_found.append(name)
                    logging.info(f"Elemento encontrado: {name}")

            # Tomar screenshot para verificación
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = f'post_verification_{timestamp}.png'
            self.driver.save_screenshot(screenshot_path)
            logging.info(f"Screenshot guardado en: {screenshot_path}")

            # Verificar si encontramos suficientes elementos
            if len(elements_found) >= 2:
                logging.info("Publicación verificada correctamente")
                return True
            else:
                logging.error(f"Faltan elementos clave. Encontrados: {elements_found}")
                return False

        except Exception as e:
            logging.error(f"Error verificando publicación: {str(e)}")
            import traceback
            logging.error(f"Stack trace:\n{traceback.format_exc()}")
            return False

    def get_liked_users(self) -> List[str]:
        """Obtiene la lista de usuarios que dieron like a una publicación"""
        try:
            logging.info("Iniciando obtención de usuarios que dieron like...")
            
            # Lista de selectores para el botón/link de likes
            like_button_selectors = [
                # Selectores para el botón de likes
                ('xpath', "//a[contains(@href, '/liked_by/')]"),
                ('xpath', "//a[contains(@href, 'liked_by')]"),
                ('xpath', "//div[@class='_aacl _aaco _aacw _aad0 _aad7']"),
                ('xpath', "//*[contains(text(), 'Me gusta')]/ancestor::button"),
                ('xpath', "//span[contains(text(), 'Me gusta')]/parent::button"),
                ('xpath', "//span[contains(text(), 'likes')]/parent::button"),
                ('css selector', 'a[href*="liked_by"]'),
                ('xpath', "//section//div[contains(text(), 'Me gusta')]"),
                ('xpath', "//section//span[contains(text(), 'Me gusta')]")
            ]

            # Intentar cada selector
            like_element = None
            used_selector = None
            
            for selector_type, selector in like_button_selectors:
                try:
                    logging.info(f"Probando selector: {selector_type} -> {selector}")
                    
                    elements = self.driver.find_elements(
                        getattr(By, selector_type.upper()),
                        selector
                    )
                    
                    for element in elements:
                        try:
                            # Verificar si el elemento es visible
                            if element.is_displayed():
                                # Obtener el texto del elemento para debugging
                                element_text = element.text
                                logging.info(f"Elemento encontrado con texto: {element_text}")
                                
                                # Guardar una captura antes de hacer clic
                                self.driver.save_screenshot('before_click.png')
                                
                                # Intentar diferentes métodos de clic
                                try:
                                    # Método 1: Clic directo
                                    element.click()
                                except:
                                    try:
                                        # Método 2: Clic con JavaScript
                                        self.driver.execute_script("arguments[0].click();", element)
                                    except:
                                        try:
                                            # Método 3: Clic con Action Chains
                                            ActionChains(self.driver).move_to_element(element).click().perform()
                                        except:
                                            continue
                                
                                # Esperar a que aparezca el diálogo
                                time.sleep(3)
                                
                                # Verificar si el diálogo se abrió
                                dialog = self.wait_for_element(
                                    By.XPATH,
                                    '//div[@role="dialog"]',
                                    timeout=5
                                )
                                
                                if dialog:
                                    like_element = element
                                    used_selector = selector
                                    break
                                
                        except Exception as e:
                            logging.warning(f"Error al interactuar con elemento: {str(e)}")
                            continue
                            
                    if like_element:
                        break
                        
                except Exception as e:
                    logging.warning(f"Selector {selector} falló: {str(e)}")
                    continue

            if not like_element:
                logging.error("No se pudo encontrar el botón de likes")
                # Guardar el HTML para debugging
                with open('page_source.html', 'w', encoding='utf-8') as f:
                    f.write(self.driver.page_source)
                raise Exception("No se pudo encontrar el botón de likes")

            logging.info(f"Botón de likes encontrado usando selector: {used_selector}")

            # Esperar a que el diálogo esté presente y cargar usuarios
            dialog = self.wait.until(
                EC.presence_of_element_located((By.XPATH, '//div[@role="dialog"]'))
            )

            # Hacer scroll en el diálogo para cargar todos los usuarios
            last_height = 0
            scroll_attempts = 0
            max_scrolls = 10

            while scroll_attempts < max_scrolls:
                # Obtener altura actual
                current_height = self.driver.execute_script(
                    "return arguments[0].scrollHeight", 
                    dialog
                )

                if current_height == last_height:
                    break

                # Hacer scroll
                self.driver.execute_script(
                    "arguments[0].scrollTop = arguments[0].scrollHeight", 
                    dialog
                )

                # Esperar a que carguen más usuarios
                time.sleep(2)

                last_height = current_height
                scroll_attempts += 1

            # Obtener los usuarios
            user_elements = dialog.find_elements(
                By.XPATH,
                './/a[@role="link" and @href]'
            )
            
            # Extraer nombres de usuario
            users = []
            for element in user_elements:
                try:
                    href = element.get_attribute('href')
                    if href and '//' in href:
                        username = href.split('/')[-2]
                        if username and username not in users:
                            users.append(username)
                except:
                    continue

            logging.info(f"Se encontraron {len(users)} usuarios únicos")

            # Guardar los usuarios en un archivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            with open(f'users_list_{timestamp}.txt', 'w', encoding='utf-8') as f:
                f.write('\n'.join(users))

            return users

        except Exception as e:
            logging.error(f"Error obteniendo usuarios: {str(e)}")
            # Guardar screenshot del error
            self.driver.save_screenshot(f'error_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')
            raise

    def check_login_status(self) -> bool:
        """Verifica si estamos logueados en Instagram usando múltiples métodos"""
        try:
            logging.info("Verificando estado de login...")
            
            # Primero, navegar a Instagram
            self.driver.get('https://www.instagram.com/')
            time.sleep(5)  # Dar tiempo a que cargue
            
            # Lista de selectores para verificar login
            login_indicators = [
                ('xpath', '//span[contains(text(), "Crear")]'),  # Botón "Crear"
                ('xpath', '//span[contains(text(), "Mensajes")]'),  # Botón Mensajes
                ('xpath', '//a[contains(@href, "/direct/inbox/")]'),  # Link a mensajes
                ('xpath', f'//a[contains(@href, "/{self.config["USERNAME"]}/")]'),  # Link al perfil
                ('xpath', '//div[@role="menuitem"]'),  # Cualquier elemento del menú
                ('css selector', 'svg[aria-label="Inicio"]'),  # Ícono de inicio
                ('css selector', 'svg[aria-label="Nueva publicación"]')  # Ícono de nueva publicación
            ]
            
            for selector_type, selector in login_indicators:
                try:
                    logging.info(f"Probando selector de login: {selector}")
                    if selector_type == 'xpath':
                        element = self.wait.until(
                            EC.presence_of_element_located((By.XPATH, selector))
                        )
                    else:
                        element = self.wait.until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                    if element:
                        logging.info(f"Sesión detectada usando selector: {selector}")
                        return True
                except Exception as e:
                    logging.debug(f"Selector {selector} no encontrado: {str(e)}")
                    continue
            
            # Si llegamos aquí, intentemos verificar las cookies
            cookies = self.driver.get_cookies()
            session_cookies = [c for c in cookies if 'sessionid' in c['name']]
            
            if session_cookies:
                logging.info("Sesión detectada mediante cookies")
                return True
                
            # Último intento: verificar si hay botón de login
            login_buttons = self.driver.find_elements(By.XPATH, 
                '//button[contains(text(), "Iniciar sesión")]'
            )
            
            if login_buttons:
                logging.warning("Se detectó botón de login - No hay sesión activa")
                return False
                
            logging.warning("No se pudo determinar el estado de login")
            return False
            
        except Exception as e:
            logging.error(f"Error verificando estado de login: {str(e)}")
            return False

    def interact_with_users(self, users: List[str]) -> None:
        """Interactúa con una lista de usuarios"""
        successful_interactions = 0
        failed_interactions = 0

        for user in users:
            try:
                if self.interact_with_user(user):
                    successful_interactions += 1
                else:
                    failed_interactions += 1
            except RateLimitError:
                logging.warning("Límite de acciones alcanzado, pausando ejecución")
                break
            except Exception as e:
                logging.error(f"Error inesperado con {user}: {str(e)}")
                failed_interactions += 1

        logging.info(f"Interacciones exitosas: {successful_interactions}")
        logging.info(f"Interacciones fallidas: {failed_interactions}")

    def close(self) -> None:
        """Cierra el navegador y limpia los recursos"""
        if self.driver:
            self.driver.quit()

def main():
    bot = None
    try:
        bot = InstagramBot(CONFIG)
        
        # Verificar sesión
        if not bot.verify_instagram_session():
            logging.error("No se pudo verificar la sesión de Instagram")
            # Intentar cargar cookies nuevamente
            if not bot.load_cookies():
                logging.error("No se pudieron cargar las cookies")
                return
            # Verificar nuevamente
            if not bot.verify_instagram_session():
                logging.error("No se pudo establecer la sesión")
                return
        
        logging.info("Sesión verificada correctamente")
        
        # Navegar a la publicación
        bot.driver.get(CONFIG['POST_URL'])
        time.sleep(5)
        
        # Verificar que estamos en la publicación correcta
        if not bot.verify_post_before_likes():
            logging.error("No se pudo verificar la publicación")
            return
            
        # Obtener usuarios
        users = bot.get_liked_users()
        if users:
            logging.info(f"Se encontraron {len(users)} usuarios")
            bot.interact_with_users(users)
        else:
            logging.error("No se encontraron usuarios")
            
    except Exception as e:
        logging.error(f"Error en la ejecución principal: {str(e)}")
    finally:
        if bot:
            bot.close()

if __name__ == "__main__":
    main()