import shutil
import os
from datetime import date, datetime
from pathlib import Path
from config import Config

class BackupManager:
    @staticmethod
    def perform_manual_backup(destination_path):
        """
        Copies the database to the specified destination path.
        """
        config_data = Config.load_config()
        db_path = config_data.get("db_path", str(Config.DATA_DIR / "attensync.db"))
        
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"Database file not found at {db_path}")
            
        try:
            # Create parent dirs if needed
            Path(destination_path).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(db_path, destination_path)
            return True, f"Backup successful to {destination_path}"
        except Exception as e:
            return False, str(e)

    @staticmethod
    def check_and_run_auto_backup():
        """
        Checks if auto-backup is enabled and due, then runs it.
        Returns: (bool: ran?, str: message)
        """
        config_data = Config.load_config()
        backup_cfg = config_data.get("backup", {})
        
        if not backup_cfg.get("enabled", False):
            return False, "Auto-backup disabled"
            
        last_backup_str = backup_cfg.get("last_backup_date")
        today = date.today()
        should_run = False
        
        if not last_backup_str:
            should_run = True
        else:
            last_backup = datetime.strptime(last_backup_str, "%Y-%m-%d").date()
            freq = backup_cfg.get("frequency", "daily")
            
            if freq == "daily" and last_backup < today:
                should_run = True
            elif freq == "weekly" and (today - last_backup).days >= 7:
                should_run = True
                
        if should_run:
            backup_dir = backup_cfg.get("location", str(Config.BACKUP_DIR))
            # Create timestamped filename
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"attensync_backup_{timestamp}.db"
            dest_path = os.path.join(backup_dir, filename)
            
            success, msg = BackupManager.perform_manual_backup(dest_path)
            
            if success:
                # Update last backup date
                backup_cfg["last_backup_date"] = today.strftime("%Y-%m-%d")
                config_data["backup"] = backup_cfg
                Config.save_config(config_data)
                return True, f"Auto-backup completed: {filename}"
            else:
                return False, f"Auto-backup failed: {msg}"
                
        return False, "Backup not due yet"
