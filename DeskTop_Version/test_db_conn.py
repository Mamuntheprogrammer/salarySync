from sqlalchemy import create_engine
import sys

def test_conn(uri):
    print(f"Testing URI: {uri}")
    try:
        # Supabase usually needs sslmode=require
        if "sslmode" not in uri:
            if "?" in uri: uri += "&sslmode=require"
            else: uri += "?sslmode=require"
                
        engine = create_engine(uri, connect_args={'connect_timeout': 10})
        with engine.connect() as conn:
            print("--- SUCCESS! ---")
            print("Successfully connected.")
            return True
    except Exception as e:
        print(f"FAILED: {e}")
        return False

if __name__ == "__main__":
    base_uri = "postgresql+psycopg2://postgres:polOLP1369P@db.zxouswurmenfmcvsnufo.supabase.co"
    db_name = "postgres"
    
    print("Trying Direct Connection (Port 5432)...")
    if not test_conn(f"{base_uri}:5432/{db_name}"):
        print("\nTrying Connection Pooler (Port 6543)...")
        if not test_conn(f"{base_uri}:6543/{db_name}"):
            print("\n--- ALL ATTEMPTS FAILED ---")
            print("Suggestion: Check Supabase IP Whitelisting or Network Restrictions.")
