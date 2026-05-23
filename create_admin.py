
from backend.database import SessionLocal, init_db
from backend.models import User
from backend.security import get_password_hash

def create_admin():
    init_db()
    db = SessionLocal()
    
   
    existing = db.query(User).filter(User.username == "admin").first()
    if existing:
        print("⚠️ Admin déjà existant!")
        db.close()
        return
    
    admin = User(
        username="admin",
        email="admin@video-r1.com",
        hashed_password=get_password_hash("Admin@12345"),
        is_admin=True,
        is_active=True
    )
    
    db.add(admin)
    db.commit()
    db.close()
    print("✅ Admin créé: admin / Admin@12345")

if __name__ == "__main__":
    create_admin()