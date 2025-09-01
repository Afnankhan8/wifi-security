import os
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
        
        
    def take_screenshot(self, name="screenshot.png"):
        """Save screenshot into ./screenshots folder for debugging"""
        try:
            os.makedirs("screenshots", exist_ok=True)
            path = os.path.join("screenshots", name if name.endswith(".png") else f"{name}.png")
            self.driver.save_screenshot(path)
            print(f"[RouterManager] Saved screenshot {path}")
            return path
        except Exception as e:
            print(f"[RouterManager] Failed to take screenshot: {e}")
            return None
        
        
        
        
        
    
        
        
        
        
        
        
        
    def get_all_profiles_devices(self):
        """
        Fetch device counts for all family profiles at once.
        Works for both table-based and div-based layouts.
        Returns a dictionary: {profile_name: device_count}
        """
        devices_dict = {}

        try:
            if not self.ensure_login():
                print("[DEBUG] Not logged in!")
                return devices_dict

            # Go to Family Profiles page
            self.driver.get(f"{self.base_url}#/security/family-profiles")
            time.sleep(3)  # Allow JS to render

            # Use JS to fetch names and device counts reliably
            script = """
            var devices = {};
            var rows = document.querySelectorAll(
                "pv-table table tbody tr, pv-list.profile-avatar-list .list"
            );
            rows.forEach(function(row){
                try {
                    var nameElem = row.querySelector("td:first-child, div.text div:first-child");
                    var countElem = row.querySelector("td:nth-child(2) span, div.device-count");
                    if(nameElem){
                        var name = nameElem.innerText.trim();
                        var count = 0;
                        if(countElem){
                            count = parseInt(countElem.innerText.trim()) || 0;
                        }
                        devices[name] = count;
                    }
                } catch(e){}
            });
            return devices;
            """
            devices_dict = self.driver.execute_script(script)
            print(f"[DEBUG] Devices dict: {devices_dict}")

        except Exception as e:
            print(f"[RouterManager] Error fetching profile devices: {e}")

        return devices_dict



        
    
    
    


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

                # Normalize text (remove newlines & extra spaces)
                ui_name = " ".join(name_elem.text.split()).strip()
                target_name = profile_name.strip()

                # Match either exact or startswith
                if ui_name == target_name or ui_name.startswith(target_name):
                    # Scroll into view
                    driver.execute_script("arguments[0].scrollIntoView(true);", profile)
                    # Click the profile
                    name_elem.click()
                    print(f"[RouterManager] Clicked profile '{ui_name}'")

                    # Wait until Assigned Devices section loads
                    try:
                        wait.until(EC.presence_of_element_located(
                            (By.XPATH, "//div[contains(text(),'Assigned Devices') or contains(text(),'Devices')]")
                        ))
                        # Save screenshot
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

    
    
    
    
    
    
    def get_devices_for_profile(self, profile_name):
        """
        Fetch assigned devices inside a given family profile.
        Returns a list of dicts: [{name, mac_address, ip}]
        """
        devices = []
        if not self.open_profile_details(profile_name):
            return devices

        driver = self.driver
        time.sleep(2)

        try:
            rows = driver.find_elements(By.CSS_SELECTOR, "tbody tr, .device-row, .client-row")
            for row in rows:
                try:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) >= 3:
                        devices.append({
                            "name": cells[0].text.strip(),
                            "mac_address": cells[1].text.strip(),
                            "ip": cells[2].text.strip()
                        })
                except:
                    continue
        except Exception as e:
            print(f"[RouterManager] Error fetching devices for profile {profile_name}: {e}")

        return devices




    def toggle_internet_in_profile(self, profile_name, enable=True):
        """
        Enable or disable Internet for a given profile using the profile details page.
        Works for the <pv-toggle> element in the profile details page.
        """
        print(f"[RouterManager] Setting internet {'ON' if enable else 'OFF'} for profile '{profile_name}'")

        # Step 1: Open profile details
        if not self.open_profile_details(profile_name):
            print(f"[RouterManager] Could not open profile details for {profile_name}")
            return False

        driver = self.driver
        wait = WebDriverWait(driver, 10)

        try:
            # Wait for the toggle switch inside <pv-toggle>
            toggle = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "pv-toggle input[type='checkbox']"))
            )

            # Scroll into view
            driver.execute_script("arguments[0].scrollIntoView(true);", toggle)

            # Check current status
            current_status = toggle.is_selected()
            if (enable and not current_status) or (not enable and current_status):
                # Use JS click for reliability
                driver.execute_script("arguments[0].click();", toggle)
                print(f"[RouterManager] Internet {'enabled' if enable else 'disabled'} successfully.")
            else:
                print(f"[RouterManager] Internet already {'enabled' if enable else 'disabled'}.")

            return True

        except TimeoutException:
            print("[RouterManager] Toggle not found in profile details page.")
            return False




    
    def fetch_profiles(self):
        return self.get_family_profiles()

# ------------------- TEST BLOCK -------------------
# ------------------- TEST BLOCK -------------------
if __name__ == "__main__":
    router = RouterManager()
    
    print("=== Testing router connection ===")
    if router.ensure_login():
        print("✓ Login successful\n")
        
        # --- Device Summary ---
        print("=== Getting device summary ===")
        try:
            summary = router.get_device_summary()
            print(f"Device Summary: {summary}\n")
        except Exception as e:
            print(f"❌ Failed to get device summary: {e}\n")

        # --- Connected Devices ---
        print("=== Getting connected devices ===")
        try:
            devices = router.get_connected_devices()
            if devices:
                for d in devices:
                    print(f" - {d.get('name','Unknown')} | MAC: {d.get('mac_address','N/A')} | IP: {d.get('ipv4','N/A')}")
            else:
                print("No devices found.\n")
        except Exception as e:
            print(f"❌ Failed to get connected devices: {e}\n")

        # --- Family Profiles ---
        print("\n=== Getting family profiles ===")
        try:
            profiles = router.get_family_profiles()
            if not profiles:
                print("No family profiles found.\n")
            else:
                for p in profiles:
                    # Fetch assigned devices for each profile
                    try:
                        devices_for_profile = router.get_devices_for_profile(p['name'])
                        p['assigned_devices'] = devices_for_profile

                        print(f"\nProfile: {p['name']} | Status: {p['status']} | Device Count: {len(devices_for_profile)}")
                        if devices_for_profile:
                            for d in devices_for_profile:
                                print(f"   - {d.get('name', 'Unknown')} ({d.get('mac_address', 'No MAC')})")
                        else:
                            print("   (No devices assigned)")
                    except Exception as e:
                        print(f"❌ Failed to fetch devices for profile {p['name']}: {e}")
        except Exception as e:
            print(f"❌ Failed to get family profiles: {e}\n")

        # --- Internet Toggle Test ---
        profile_name = "Home"  # Replace with your actual profile name
        print(f"\n=== Opening profile details for '{profile_name}' ===")
        if router.open_profile_details(profile_name):
            print(f"✅ Successfully navigated to profile details for '{profile_name}'\n")
            
            # Enable Internet
            print(f"=== Enabling internet for '{profile_name}' ===")
            try:
                success = router.toggle_internet_in_profile(profile_name, enable=True)
                print(f"Internet access for profile '{profile_name}' set to Enabled: {success}\n")
            except Exception as e:
                print(f"❌ Failed to enable internet for {profile_name}: {e}")

            # Disable Internet
            print(f"=== Disabling internet for '{profile_name}' ===")
            try:
                success = router.toggle_internet_in_profile(profile_name, enable=False)
                print(f"Internet access for profile '{profile_name}' set to Disabled: {success}\n")
            except Exception as e:
                print(f"❌ Failed to disable internet for {profile_name}: {e}")
        else:
            print(f"❌ Failed to open profile details for '{profile_name}'\n")
        
        print("=== Debugging completed ===")
        print("Check the saved screenshots and HTML files for verification.")

    else:
        print("✗ Failed to login to router")
    
    router.quit()
    print("=== WebDriver closed ===")
