"""
Create platform admin user (superuser)
Usage: docker compose exec backend python create_admin.py
"""
import asyncio
import sys
from sqlalchemy import text

async def create_admin():
    """Create or update platform admin user using raw SQL to avoid model import issues"""
    from sqlalchemy.ext.asyncio import create_async_engine
    import os

    # Database URL from env
    database_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://sdlc_user:changeme_postgres_password@localhost:5432/sdlc_orchestrator")

    # Hash password using bcrypt
    import bcrypt
    password_hash = bcrypt.hashpw("Admin@123456".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # Create engine
    engine = create_async_engine(database_url, echo=False)

    async with engine.begin() as conn:
        # Check if user exists
        result = await conn.execute(
            text("SELECT id, email, role, is_superuser FROM users WHERE email = :email"),
            {"email": "taidt@mtsolution.com.vn"}
        )
        user = result.fetchone()

        if user:
            # Update existing user
            await conn.execute(
                text("""
                    UPDATE users
                    SET password_hash = :password_hash,
                        is_superuser = true,
                        is_active = true,
                        role = 'cto',
                        updated_at = NOW()
                    WHERE email = :email
                """),
                {"password_hash": password_hash, "email": "taidt@mtsolution.com.vn"}
            )
            print(f"✅ Updated existing user: taidt@mtsolution.com.vn")
        else:
            # Create new user
            await conn.execute(
                text("""
                    INSERT INTO users (
                        id, email, full_name, password_hash, role,
                        is_active, is_superuser, created_at, updated_at
                    ) VALUES (
                        gen_random_uuid(), :email, :full_name, :password_hash, :role,
                        true, true, NOW(), NOW()
                    )
                """),
                {
                    "email": "taidt@mtsolution.com.vn",
                    "full_name": "Tai Dang (Platform Admin)",
                    "password_hash": password_hash,
                    "role": "cto"
                }
            )
            print(f"✅ Created new user: taidt@mtsolution.com.vn")

    await engine.dispose()

    print("\n" + "="*60)
    print("✅ PLATFORM ADMIN USER READY!")
    print("="*60)
    print(f"   📧 Email:    taidt@mtsolution.com.vn")
    print(f"   🔑 Password: Admin@123456")
    print(f"   👑 Role:     CTO (Platform Admin)")
    print(f"   🛡️  Superuser: YES")
    print("="*60)
    print("\nYou can now login at: http://localhost:8310")
    print()

if __name__ == "__main__":
    try:
        asyncio.run(create_admin())
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
