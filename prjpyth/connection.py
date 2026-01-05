"""
Connexion PostgreSQL ultra-simplifiée sans pool
"""
import psycopg2
import psycopg2.extras
import logging

# Désactiver les logs pour éviter les erreurs
logging.basicConfig(level=logging.CRITICAL)
logger = logging.getLogger(__name__)

class SimpleConnection:
    """Connexion simple sans pool"""
    
    @staticmethod
    def get_connection():
        """Retourne une connexion simple"""
        try:
            # Configuration minimaliste
            conn = psycopg2.connect(
                dbname="exam_platform",
                user="postgres",
                password="gr123",
                host="localhost",
                port="5432",
                connect_timeout=5  # Timeout court
            )
            return conn
        except psycopg2.OperationalError as e:
            print(f"⚠️  Erreur connexion PostgreSQL: {e}")
            print("\n💡 Solutions:")
            print("1. Vérifiez que PostgreSQL est lancé")
            print("2. Créez la base: CREATE DATABASE exam_platform;")
            print("3. Essayez sans mot de passe: password=''")
            return None
        except Exception as e:
            print(f"❌ Erreur inconnue: {e}")
            return None

def execute_query(query: str, params=None, fetch=True):
    """
    Version ultra-simplifiée d'execute_query
    """
    conn = None
    try:
        conn = SimpleConnection.get_connection()
        if not conn:
            return [] if fetch else 0
        
        # Utiliser RealDictCursor pour avoir des dictionnaires
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute(query, params or ())
        
        if fetch and cursor.description:
            results = cursor.fetchall()
            conn.commit()
            return results
        else:
            conn.commit()
            return cursor.rowcount
            
    except Exception as e:
        print(f"⚠️  Erreur query: {str(e)[:100]}...")
        if conn:
            conn.rollback()
        return [] if fetch else 0
    finally:
        if conn:
            conn.close()

def load_dataframe(query: str, params=None):
    """
    Version simplifiée - retourne liste de dicts
    """
    try:
        results = execute_query(query, params, fetch=True)
        return {"data": results}
    except Exception as e:
        print(f"⚠️  Erreur load_dataframe: {e}")
        return {"data": []}

# Test au démarrage
if __name__ == "__main__":
    print("🔍 Test de connexion PostgreSQL...")
    
    # Test 1: Connexion simple
    conn = SimpleConnection.get_connection()
    if conn:
        print("✅ PostgreSQL connecté")
        conn.close()
    else:
        print("❌ Échec connexion")
        print("\n🚨 VÉRIFIEZ CES POINTS:")
        print("1. PostgreSQL est-il installé?")
        print("2. Le service est-il lancé? (services.msc)")
        print("3. Avez-vous créé la base?")
        print("\n📝 Pour créer la base:")
        print("   psql -U postgres")
        print("   CREATE DATABASE exam_platform;")
       