"""Setup script for Discord Mesai Bot."""

import asyncio
import os
import shutil
from database import Database
from config import Config

async def setup_bot():
    """Setup the bot for first run."""
    print("🔧 Discord Mesai Bot Kurulum Başlatılıyor...")
    
    # Create directories
    os.makedirs("data", exist_ok=True)
    os.makedirs("backups", exist_ok=True)
    print("✅ Dizinler oluşturuldu")
    
    # Setup database
    db = Database()
    await db.init_db()
    print("✅ Veritabanı başlatıldı")
    
    # Create .env file if it doesn't exist
    if not os.path.exists(".env"):
        shutil.copy(".env.example", ".env")
        print("✅ .env dosyası oluşturuldu (.env.example'dan kopyalandı)")
        print("⚠️  Lütfen .env dosyasını bot token'ınız ve diğer ayarlarınızla düzenleyin!")
    else:
        print("✅ .env dosyası mevcut")
    
    print("\n🎉 Kurulum tamamlandı!")
    print("\nSonraki adımlar:")
    print("1. .env dosyasını Discord bot token'ınızla düzenleyin")
    print("2. Bot'u çalıştırmak için: python bot.py")
    print("\n📝 Komutlar:")
    print("• /mesai-baslat - Mesai başlat")
    print("• /mesai-bitir - Mesai bitir")
    print("• /mesai-durum - Mevcut durum")
    print("• /mesai-gecmisi - Mesai geçmişi")
    print("• /hedef-belirle - Hedef belirle")
    print("• /siralama - Leaderboard")
    print("• /istatistik - Kişisel istatistikler")
    print("• /admin-panel - Admin paneli (Sadece adminler)")

if __name__ == "__main__":
    asyncio.run(setup_bot())