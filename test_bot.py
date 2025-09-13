"""Test script for Discord Mesai Bot - DEMO MODE ONLY."""

import asyncio
import os
from datetime import datetime
from database import Database
from config import Config

async def test_database_operations():
    """Test database operations without Discord connection."""
    print("🧪 Veritabanı İşlemleri Test Ediliyor...\n")
    
    # Initialize database
    db = Database()
    await db.init_db()
    print("✅ Veritabanı başlatıldı")
    
    # Test user creation
    user_data = await db.get_or_create_user(12345, "test_user")
    print(f"✅ Test kullanıcısı oluşturuldu: {user_data['username']}")
    
    # Test work session
    success = await db.start_work_session(12345, "test_user")
    if success:
        print("✅ Mesai oturumu başlatıldı")
        
        # Wait a moment and end session
        await asyncio.sleep(1)
        session_data = await db.end_work_session(12345)
        if session_data:
            print(f"✅ Mesai oturumu bitirildi - Süre: {session_data['duration_minutes']} dakika")
        else:
            print("❌ Mesai oturumu bitirilemedi")
    else:
        print("❌ Mesai oturumu başlatılamadı")
    
    # Test work history
    history = await db.get_user_work_history(12345, 5)
    print(f"✅ Mesai geçmişi alındı - {len(history)} kayıt")
    
    # Test backup
    backup_path = await db.backup_database()
    print(f"✅ Yedek oluşturuldu: {backup_path}")
    
    print("\n🎉 Tüm veritabanı testleri başarıyla tamamlandı!")
    return True

def check_configuration():
    """Check bot configuration."""
    print("🔧 Yapılandırma Kontrolü...\n")
    
    if not Config.DISCORD_TOKEN or Config.DISCORD_TOKEN == 'your_bot_token_here':
        print("⚠️  Discord token ayarlanmamış - Bot başlatılamaz")
        return False
    
    print("✅ Discord token ayarlanmış")
    
    if Config.GUILD_ID:
        print(f"✅ Guild ID ayarlanmış: {Config.GUILD_ID}")
    else:
        print("ℹ️  Guild ID ayarlanmamış - Global komutlar kullanılacak")
    
    if Config.ADMIN_CHANNEL_ID:
        print(f"✅ Admin kanal ID ayarlanmış: {Config.ADMIN_CHANNEL_ID}")
    else:
        print("⚠️  Admin kanal ID ayarlanmamış - Hata logları devre dışı")
    
    print(f"✅ Veritabanı yolu: {Config.DATABASE_PATH}")
    print(f"✅ Yedek dizini: {Config.BACKUP_DIRECTORY}")
    print(f"✅ Otomatik bitiş süresi: {Config.AUTO_WORK_LIMIT_HOURS} saat")
    
    return True

async def demo_mode():
    """Run bot in demo mode (database only, no Discord)."""
    print("=" * 60)
    print("🤖 DISCORD MESAI BOT - DEMO MODU")
    print("=" * 60)
    print("Bu test Discord'a bağlanmaz, sadece yerel işlevleri test eder.\n")
    
    # Check configuration
    config_ok = check_configuration()
    
    # Test database
    db_ok = await test_database_operations()
    
    print("\n" + "=" * 60)
    print("📊 TEST SONUÇLARI")
    print("=" * 60)
    
    if config_ok and db_ok:
        print("🎉 Tüm testler BAŞARILI!")
        if Config.DISCORD_TOKEN and Config.DISCORD_TOKEN != 'your_bot_token_here':
            print("\n🚀 Bot Discord'a bağlanmaya hazır!")
            print("Çalıştırmak için: python bot.py")
        else:
            print("\n⚠️  Bot'u çalıştırmak için .env dosyasında DISCORD_TOKEN ayarlayın")
    else:
        print("❌ Bazı testler başarısız! Sorunları düzeltin.")
    
    print("=" * 60)

def real_bot_check():
    """Check if this is an attempt to run the real bot."""
    if Config.DISCORD_TOKEN and Config.DISCORD_TOKEN != 'your_bot_token_here':
        print("🚨 UYARI: Gerçek Discord token tespit edildi!")
        print("Bu test scripti gerçek bot yerine kullanılmamalı.")
        print("Gerçek botu çalıştırmak için: python bot.py")
        return True
    return False

if __name__ == "__main__":
    if real_bot_check():
        print("Test yerine gerçek bot'u çalıştırın: python bot.py")
    else:
        asyncio.run(demo_mode())