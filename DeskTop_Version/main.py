import sys
import warnings

# Suppress pkg_resources deprecation warning from face_recognition_models
warnings.filterwarnings("ignore", category=UserWarning, message="pkg_resources is deprecated as an API")
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow
from database import db

from ui.setup.first_run_wizard import FirstRunWizard
from config import Config
from utils.backup_manager import BackupManager
from services.sync_service import SyncService

def main():
    # Check First Run
    config = Config.load_config()
    app = QApplication(sys.argv)
    app.setStyle("Fusion") 

    if not config.get('setup_complete'):
        wizard = FirstRunWizard()
        if not wizard.exec():
            sys.exit(0)

    # Initialize Database (might be re-initialized after wizard)
    db.initialize()
    
    # Check Auto Backup
    ran, msg = BackupManager.check_and_run_auto_backup()
    if ran:
        print(msg) # Log to console, or could show toast
    
    # Check Cloud Sync
    config = Config.load_config()
    if config.get("cloud_sync", {}).get("enabled") and config.get("cloud_sync", {}).get("auto_sync"):
        print("Checking Cloud Sync...")
        # Run in try/except to not block UI
        try:
            service = SyncService()
            success, msg = service.sync_data_to_sheets()
            print(f"Cloud Sync: {msg}")
        except Exception as e:
            print(f"Cloud Sync Error: {e}")
    
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
