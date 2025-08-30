import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY') or 'your-secret-key-here'
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Airtel Router Configuration
    ROUTER_URL = os.getenv('ROUTER_URL', 'https://192.168.1.1')
    ROUTER_USERNAME = os.getenv('ROUTER_USERNAME', 'admin')
    ROUTER_PASSWORD = os.getenv('ROUTER_PASSWORD', 'admin123')
    
    # Selenium Configuration
    SELENIUM_HEADLESS = os.getenv('SELENIUM_HEADLESS', 'False').lower() == 'true'
    CHROME_DRIVER_PATH = os.getenv('CHROME_DRIVER_PATH', r'C:\WebDrivers\chromedriver.exe')
    
    # Application Settings
    DEVICE_MONITOR_INTERVAL = int(os.getenv('DEVICE_MONITOR_INTERVAL', '60'))
