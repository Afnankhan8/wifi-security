import time
import threading
import atexit
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, NoSuchElementException



class RouterManager:
    _instance = None
    _lock = threading.Lock()
    
    def quit(self):
        if self.driver:
            try:
                self.driver.quit()
                print("[RouterManager] WebDriver closed successfully.")
            except WebDriverException as e:
                print(f"[RouterManager] Error quitting WebDriver: {e}")
            self.driver = None
            self.is_logged_in = False
    
    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(RouterManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self, username="admin", password="Afnan@123"):
        if self._initialized:
            return
            
        self.driver = None
        self.base_url = 'https://192.168.1.1/web_whw/'
        self.username = username
        self.password = password
        self.is_logged_in = False
        self.last_activity = time.time()
        self._initialize_driver()
        self._initialized = True
        
        atexit.register(self.quit)
        self.session_thread = threading.Thread(target=self._maintain_session, daemon=True)
        self.session_thread.start()

    def _initialize_driver(self):
        """Initializes the Selenium WebDriver with better stealth options."""
        if self.driver:
            try:
                self.driver.quit()
            except WebDriverException:
                pass
        
        chrome_options = Options()
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--allow-running-insecure-content')
        chrome_options.add_argument('--disable-notifications')
        chrome_options.add_argument('--disable-popup-blocking')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')

        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(30)
            self.driver.set_script_timeout(30)
            self.wait = WebDriverWait(self.driver, 20)
            print("[RouterManager] WebDriver initialized successfully.")
        except Exception as e:
            print(f"[RouterManager] Failed to initialize WebDriver: {e}")
            self.driver = None

    def _is_driver_healthy(self):
        if not self.driver:
            return False
        try:
            self.driver.current_url
            return True
        except WebDriverException:
            return False

    def _maintain_session(self):
        while True:
            time.sleep(60)
            if not self._is_driver_healthy():
                print("[Session Maintainer] Driver unhealthy, reinitializing...")
                self._initialize_driver()
                self.is_logged_in = False
            if self.is_logged_in and time.time() - self.last_activity > 600:
                print("[Session Maintainer] Refreshing session...")
                try:
                    self.driver.refresh()
                    time.sleep(5)
                    if "/#/login" in self.driver.current_url:
                        self.is_logged_in = False
                        print("[Session Maintainer] Session expired, need to login again")
                except:
                    self.is_logged_in = False

    def _update_activity(self):
        self.last_activity = time.time()

    def ensure_login(self):
        if self.is_logged_in:
            try:
                if "/#/login" not in self.driver.current_url:
                    self._update_activity()
                    return True
            except:
                pass
                
        print("[RouterManager] Logging in...")
        if not self._is_driver_healthy():
            self._initialize_driver()
            if not self._is_driver_healthy():
                return False

        try:
            self.driver.get(f'{self.base_url}#/login')
            time.sleep(3)
            self.driver.save_screenshot('login_page.png')
            print("[RouterManager] Saved login page screenshot")

            # Username field
            try:
                username_field = self.wait.until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, "pv-inputbox[formcontrolname='username'] input"))
                )
            except:
                try:
                    username_field = self.wait.until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, "input[formcontrolname='username']"))
                    )
                except:
                    print("[RouterManager] Could not find username field")
                    return False
            
            username_field.clear()
            username_field.send_keys(self.username)
            
            # Password field
            try:
                password_field = self.wait.until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, "pv-inputbox[formcontrolname='password'] input"))
                )
            except:
                try:
                    password_field = self.wait.until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, "input[formcontrolname='password']"))
                    )
                except:
                    print("[RouterManager] Could not find password field")
                    return False
            
            password_field.clear()
            password_field.send_keys(self.password)
            time.sleep(1)

            # Login button
            try:
                login_button = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//button[./span[text()='Sign in']]"))
                )
            except:
                try:
                    login_button = self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Sign in')]"))
                    )
                except:
                    print("[RouterManager] Could not find login button")
                    return False
            
            if login_button.get_attribute('disabled'):
                print("[RouterManager] Login button is disabled")
                return False
                
            login_button.click()
            time.sleep(5)

            try:
                self.wait.until(
                    EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Overview') or contains(text(), 'Dashboard')]"))
                )
                self.is_logged_in = True
                self._update_activity()
                print("[RouterManager] Login successful.")
                self.driver.save_screenshot('dashboard.png')
                print("[RouterManager] Saved dashboard screenshot")
                return True
            except TimeoutException:
                print("[RouterManager] Login failed - timeout waiting for dashboard")
                if "login" in self.driver.current_url.lower():
                    print("[RouterManager] Still on login page after login attempt")
                return False

        except Exception as e:
            print(f"[RouterManager] Login failed: {e}")
            return False

    def get_device_summary(self):
        try:
            if not self.ensure_login():
                return {}

            self.driver.get(f"{self.base_url}#/overview")
            time.sleep(3)
            self.driver.save_screenshot('overview.png')
            with open('overview_page.html', 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)
            print("[RouterManager] Saved overview page source")
            
            summary = {'total_devices': 0, 'online_devices': 0, 'blocked_devices': 0}
            
            script = """
            var summary = {};
            var deviceElements = document.querySelectorAll('[class*="device"], [class*="count"], circle-progress, pv-text');
            deviceElements.forEach(function(elem) {
                var text = elem.textContent || elem.innerText;
                if (text.includes('Connected') || text.includes('connected')) {
                    var numbers = text.match(/\\d+/g);
                    if (numbers) summary.online_devices = parseInt(numbers[0]);
                }
                if (text.includes('Not connected') || text.includes('Blocked')) {
                    var numbers = text.match(/\\d+/g);
                    if (numbers) summary.blocked_devices = parseInt(numbers[0]);
                }
                if (text.includes('Total') || text.includes('Devices')) {
                    var numbers = text.match(/\\d+/g);
                    if (numbers) summary.total_devices = parseInt(numbers[0]);
                }
            });
            return summary;
            """
            
            js_result = self.driver.execute_script(script)
            if js_result:
                summary.update(js_result)

            try:
                elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Device') or contains(text(), 'Connected') or contains(text(), 'Blocked')]")
                for elem in elements:
                    text = elem.text
                    if 'Connected' in text:
                        numbers = [int(s) for s in text.split() if s.isdigit()]
                        if numbers: summary['online_devices'] = numbers[0]
                    elif 'Blocked' in text or 'Not connected' in text:
                        numbers = [int(s) for s in text.split() if s.isdigit()]
                        if numbers: summary['blocked_devices'] = numbers[0]
                    elif 'Total' in text:
                        numbers = [int(s) for s in text.split() if s.isdigit()]
                        if numbers: summary['total_devices'] = numbers[0]
            except:
                pass
            
            self._update_activity()
            print(f"[RouterManager] Device summary: {summary}")
            return summary

        except Exception as e:
            print(f"[RouterManager] Error fetching device summary: {e}")
            return {'total_devices': 0, 'online_devices': 0, 'blocked_devices': 0}

    def get_connected_devices(self):
        try:
            if not self.ensure_login():
                return []

            self.driver.get(f'{self.base_url}#/devices')
            time.sleep(3)
            self.driver.save_screenshot('devices.png')
            with open('devices_page.html', 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)
            print("[RouterManager] Saved devices page source")
            
            devices = []
            try:
                rows = self.driver.find_elements(By.CSS_SELECTOR, "tbody tr, table tr, .device-row, .client-row")
                for row in rows:
                    try:
                        cells = row.find_elements(By.TAG_NAME, "td")
                        if len(cells) >= 3:
                            devices.append({
                                'name': cells[0].text.strip(),
                                'mac_address': cells[1].text.strip(),
                                'ipv4': cells[2].text.strip(),
                                'is_blocked_on_router': False,
                                'signal_strength': "N/A",
                                'connected_to': "N/A"
                            })
                    except:
                        continue
                if devices:
                    print(f"[RouterManager] Found {len(devices)} devices using direct element search")
                    return devices
            except Exception as e:
                print(f"[RouterManager] Error with direct element search: {e}")

            script = """
            var devices = [];
            var rows = document.querySelectorAll("tbody tr, table tr, tr[class*='row']");
            for (var i = 0; i < rows.length; i++) {
                try {
                    var cells = rows[i].querySelectorAll("td");
                    if (cells.length >= 3) {
                        devices.push({
                            name: cells[0].textContent.trim(),
                            mac_address: cells.length > 1 ? cells[1].textContent.trim() : "N/A",
                            ipv4: cells.length > 2 ? cells[2].textContent.trim() : "N/A",
                            is_blocked_on_router: false,
                            signal_strength: "N/A",
                            connected_to: "N/A"
                        });
                    }
                } catch(e) {}
            }
            return devices;
            """
            devices = self.driver.execute_script(script)
            self._update_activity()
            print(f"[RouterManager] Found {len(devices)} devices using JavaScript")
            return devices

        except Exception as e:
            print(f"[RouterManager] Error fetching devices: {e}")
            return []

    def navigate(self, path: str):
        base_url = "https://192.168.1.1"
        url = path if path.startswith("http") else f"{base_url}{path}"
        self.driver.get(url)






   
        
        
        
        
     # ------------------ Family Profiles Methods ------------------

    def get_family_profiles(self):
        """
        Fetch all family profiles with their names and status (Enabled/Disabled).
        """
        try:
            # Go to the Family Profiles page
            if not self.ensure_login():
                return []

            self.driver.get(f"{self.base_url}#/security/family-profiles")
            time.sleep(3)

            # Updated selector for Airtel AirFiber
            elements = self.driver.find_elements(By.CSS_SELECTOR, "pv-list.profile-avatar-list .list")
            print(f"[DEBUG] Found {len(elements)} profile elements")  # Debug output

            profiles = []
            for el in elements:
                raw_name = el.text
                clean_name = " ".join(raw_name.split())
                
                # Detect status
                status = "Unknown"
                if "Enabled" in clean_name:
                    status = "Enabled"
                    clean_name = clean_name.replace("Enabled", "").strip()
                elif "Disabled" in clean_name:
                    status = "Disabled"
                    clean_name = clean_name.replace("Disabled", "").strip()
                
                profiles.append({"name": clean_name, "status": status})
            return profiles

        except Exception as e:
            print(f"[RouterManager] Error fetching profiles: {e}")
            return []
        
        
        
        
        
        
        
        
        
        
# router_manager.py (add these methods to the RouterManager class)

    def enable_disable_profile(self, profile_name, enable=True):
        """Enable or disable internet access for a specific profile"""
        try:
            # Navigate to family profiles page
            self.driver.get(f"{self.base_url}/#/family/profiles")
            time.sleep(3)
            
            # Find the profile by name
            profiles = self.driver.find_elements(By.CSS_SELECTOR, ".profile-item, tr.profile-row")
            for profile in profiles:
                if profile_name in profile.text:
                    # Look for enable/disable toggle
                    try:
                        toggle = profile.find_element(By.CSS_SELECTOR, ".toggle-switch, .enable-toggle")
                        current_state = toggle.get_attribute("class")
                        
                        # Check if we need to change the state
                        if ("active" in current_state and not enable) or ("active" not in current_state and enable):
                            toggle.click()
                            time.sleep(2)  # Wait for changes to apply
                            return True
                        else:
                            return True  # Already in desired state
                    except:
                        # If toggle not found, try finding enable/disable buttons
                        try:
                            if enable:
                                enable_btn = profile.find_element(By.CSS_SELECTOR, ".enable-btn, .btn-success")
                                enable_btn.click()
                            else:
                                disable_btn = profile.find_element(By.CSS_SELECTOR, ".disable-btn, .btn-warning")
                                disable_btn.click()
                            time.sleep(2)
                            return True
                        except:
                            print(f"Could not find toggle/buttons for profile {profile_name}")
                            return False
            return False
        except Exception as e:
            print(f"Error toggling profile state: {e}")
            self.take_screenshot("enable_disable_profile_error")
            return False

    def get_devices_for_profile(self, profile_name):
        """Get list of devices assigned to a specific profile"""
        try:
            # Navigate to the profile details
            self.driver.get(f"{self.base_url}/#/family/profiles")
            time.sleep(3)
            
            # Find and click on the profile
            profiles = self.driver.find_elements(By.CSS_SELECTOR, ".profile-item, tr.profile-row")
            for profile in profiles:
                if profile_name in profile.text:
                    # Try to find a link or button to view details
                    try:
                        details_link = profile.find_element(By.CSS_SELECTOR, "a, .details-btn, .view-btn")
                        details_link.click()
                    except:
                        profile.click()
                    time.sleep(3)
                    break
            
            # Extract devices from the profile details page
            device_elements = self.driver.find_elements(By.CSS_SELECTOR, ".device-item, .assigned-device, tr.device-row")
            devices = []
            for device in device_elements:
                try:
                    name = device.find_element(By.CSS_SELECTOR, ".device-name, .name, td:nth-child(1)").text
                    mac = device.find_element(By.CSS_SELECTOR, ".device-mac, .mac, td:nth-child(2)").text
                    devices.append({"name": name, "mac_address": mac})
                except:
                    continue
                    
            # Navigate back to profiles list
            self.driver.get(f"{self.base_url}/#/family/profiles")
            time.sleep(2)
                    
            return devices
        except Exception as e:
            print(f"Error getting devices for profile: {e}")
            self.take_screenshot("get_devices_error")
            return []
    
    
    


    def open_profile_details(self, profile_name, screenshot_name="profile_details.png"):
        """
        Click a specific family profile by name, open its details page,
        and save a screenshot after the page loads.
        """
        if not self.ensure_login():
            print("[RouterManager] Not logged in")
            return False

        driver = self.driver
        wait = WebDriverWait(driver, 10)

        # Go to Family Profiles page
        driver.get(f"{self.base_url}#/security/family-profiles")
        time.sleep(2)  # slight wait for page rendering

        try:
            # Wait for profiles to appear
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "pv-list.profile-avatar-list .list")))
        except TimeoutException:
            print("[RouterManager] Family profiles page did not load.")
            return False

        # Fetch profile elements
        profiles = driver.find_elements(By.CSS_SELECTOR, "pv-list.profile-avatar-list .list")

        for profile in profiles:
            try:
                # The name element inside the profile card
                name_elem = profile.find_element(By.CSS_SELECTOR, "div.text div:first-child")
                if name_elem.text.strip() == profile_name:
                    # Scroll into view
                    driver.execute_script("arguments[0].scrollIntoView(true);", profile)
                    # Click the profile
                    name_elem.click()
                    print(f"[RouterManager] Clicked profile '{profile_name}'")

                    # Wait until Assigned Devices section loads
                    try:
                        wait.until(EC.presence_of_element_located(
                            (By.XPATH, "//div[contains(text(),'Assigned Devices') or contains(text(),'Devices')]")
                        ))
                        # Save screenshot of the profile details page
                        driver.save_screenshot(screenshot_name)
                        print(f"[RouterManager] Screenshot saved as '{screenshot_name}'")
                    except TimeoutException:
                        print("[RouterManager] Profile details page did not load properly.")

                    return True

            except StaleElementReferenceException:
                continue
            except Exception as e:
                print(f"[RouterManager] Error clicking profile '{profile_name}': {e}")
                continue

        print(f"[RouterManager] Profile '{profile_name}' not found.")
        return False



    def toggle_internet_in_profile(self, profile_name, enable=True):
        """
        Enable or disable internet for a given profile.
        """
        print(f"[RouterManager] Setting internet {'ON' if enable else 'OFF'} for profile '{profile_name}'")

        # Step 1: Open profile details
        if not self.open_profile_details(profile_name):
            print(f"[RouterManager] Could not open profile details for {profile_name}")
            return False

        driver = self.driver
        wait = WebDriverWait(driver, 10)

        try:
            # Wait for the toggle switch
            toggle = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "label.switch input[type='checkbox']"))
            )

            current_status = toggle.is_selected()
            if (enable and not current_status) or (not enable and current_status):
                driver.execute_script("arguments[0].click();", toggle)
                print(f"[RouterManager] Internet {'enabled' if enable else 'disabled'} successfully.")
            else:
                print(f"[RouterManager] Internet already {'enabled' if enable else 'disabled'}.")

            return True

        except TimeoutException:
            print("[RouterManager] Toggle not found in profile details page.")
            return False


    def get_devices_for_profile(self, profile_name, timeout=15):
        """
        Fetch the list of devices assigned to a specific family profile.
        Handles dynamically loaded devices and waits for them to appear in real-time.
        """
        if not self.open_profile_details(profile_name):
            print(f"[RouterManager] Could not open profile '{profile_name}' details.")
            return []

        devices = []
        wait = WebDriverWait(self.driver, timeout)

        try:
            # Wait until at least one device item is present under Assigned Devices
            device_items = wait.until(lambda d: d.find_elements(By.CSS_SELECTOR, "li, .device-item, .list-item"))

            if not device_items:
                print(f"[RouterManager] No devices found for profile '{profile_name}'")
                return []

            # Extract device information
            for d in device_items:
                try:
                    name_elem = d.find_element(By.CSS_SELECTOR, ".device-name, .name, td:nth-child(1)")
                    mac_elem = d.find_element(By.CSS_SELECTOR, ".device-mac, .mac, td:nth-child(2)")
                    name = name_elem.text.strip() if name_elem else d.text.strip()
                    mac = mac_elem.text.strip() if mac_elem else "N/A"
                    if name:
                        devices.append({"name": name, "mac_address": mac})
                except:
                    # Fallback: just take the text if detailed selectors fail
                    name = d.text.strip()
                    if name:
                        devices.append({"name": name, "mac_address": "N/A"})

            print(f"[RouterManager] Found {len(devices)} devices for profile '{profile_name}'")

        except TimeoutException:
            print(f"[RouterManager] No assigned devices loaded for profile '{profile_name}' within {timeout}s")
        except Exception as e:
            print(f"[RouterManager] Error fetching devices for profile '{profile_name}': {e}")

        return devices



    
    def fetch_profiles(self):
        return self.get_family_profiles()

# ------------------- TEST BLOCK -------------------
if __name__ == "__main__":
    router = RouterManager()
    
    print("=== Testing router connection ===")
    if router.ensure_login():
        print("✓ Login successful\n")
        
        # Device summary
        print("=== Getting device summary ===")
        summary = router.get_device_summary()
        print(f"Device Summary: {summary}\n")
        
        # Connected devices
        print("=== Getting connected devices ===")
        devices = router.get_connected_devices()
        print(f"Connected Devices: {devices}\n")
        
        # Family profiles
        print("=== Getting family profiles ===")
        profiles = router.get_family_profiles()
        for p in profiles:
            # Fetch assigned devices for each profile
            devices_for_profile = router.get_devices_for_profile(p['name'])
            p['assigned_devices'] = devices_for_profile
            print(f"Profile: {p['name']} | Status: {p['status']} | Devices: {devices_for_profile}")
        print()
        
        # Pick a profile
        profile_name = "Afnan"  # <-- change if your router uses a different name
        print(f"=== Opening profile details for '{profile_name}' ===")
        if router.open_profile_details(profile_name):
            print(f"✅ Successfully navigated to profile details for '{profile_name}'\n")
            
            # Enable/Disable Internet
            print(f"=== Enabling internet for '{profile_name}' ===")
            success = router.toggle_internet_in_profile(profile_name, enable=True)
            print(f"Internet access for profile '{profile_name}' set to Enabled: {success}\n")
        else:
            print(f"❌ Failed to open profile details for '{profile_name}'\n")
        
        print("=== Debugging completed ===")
        print("Check the saved screenshots and HTML files for verification.")
    else:
        print("✗ Failed to login to router")
    
    router.quit()
    print("=== WebDriver closed ===")
