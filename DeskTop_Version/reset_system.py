import os
import shutil
from pathlib import Path
from config import Config

def reset_system():
    print("WARNING: This will delete the entire database and reset configuration.")
    confirm = input("Are you sure? (y/n): ")
    if confirm.lower() != 'y':
        print("Aborted.")
        return

    # 1. Resolve DB Path from current config
    current_config = Config.load_config()
    db_path = Path(current_config.get('db_path', Config.DEFAULT_CONFIG['db_path']))
    
    if db_path.exists():
        try:
            os.remove(db_path)
            print(f"[OK] Database deleted: {db_path}")
        except Exception as e:
            print(f"[ERR] Could not delete database: {e}")
    
    # 2. Reset Config
    config_file = Path(Config.CONFIG_FILE)
    if config_file.exists():
        try:
            os.remove(config_file)
            print(f"[OK] Config deleted: {config_file}")
        except Exception as e:
            print(f"[ERR] Could not delete config: {e}")
    
    # 3. Clear __pycache__
    root_dir = Path(__file__).parent
    for p in root_dir.rglob('__pycache__'):
        try:
            shutil.rmtree(p)
            print(f"[OK] Cleared cache: {p}")
        except Exception as e:
            print(f"[ERR] Could not clear cache {p}: {e}")

    print("\nSystem Reset Complete. Run 'python main.py' to re-initialize.")

if __name__ == "__main__":
    reset_system()
