"""Validation script for Discord Mesai Bot."""

import asyncio
import os
import sys
from database import Database
from config import Config

async def validate_bot():
    """Validate bot components and configuration."""
    print("🔍 Discord Mesai Bot Doğrulama Başlatılıyor...\n")
    
    errors = []
    warnings = []
    
    # Check Python version
    if sys.version_info < (3, 8):
        errors.append("Python 3.8 veya üzeri gerekli")
    else:
        print("✅ Python versiyonu: OK")
    
    # Check required files
    required_files = [
        'bot.py', 'config.py', 'database.py', 'requirements.txt',
        'cogs/work_commands.py', 'cogs/leaderboard.py', 'cogs/admin_panel.py'
    ]
    
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}: Mevcut")
        else:
            errors.append(f"Gerekli dosya bulunamadı: {file}")
    
    # Check directories
    required_dirs = ['cogs', 'data', 'backups']
    for directory in required_dirs:
        if os.path.exists(directory):
            print(f"✅ {directory}/ dizini: Mevcut")
        else:
            warnings.append(f"Dizin bulunamadı: {directory}")
    
    # Check imports
    try:
        import discord
        print("✅ discord.py: Yüklü")
    except ImportError:
        errors.append("discord.py kütüphanesi yüklü değil")
    
    try:
        import aiosqlite
        print("✅ aiosqlite: Yüklü")
    except ImportError:
        errors.append("aiosqlite kütüphanesi yüklü değil")
    
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        print("✅ APScheduler: Yüklü")
    except ImportError:
        errors.append("APScheduler kütüphanesi yüklü değil")
    
    # Test database initialization
    try:
        db = Database()
        await db.init_db()
        print("✅ Veritabanı başlatma: OK")
        
        # Test basic database operations
        await db.get_or_create_user(12345, "test_user")
        print("✅ Veritabanı işlemleri: OK")
        
    except Exception as e:
        errors.append(f"Veritabanı hatası: {e}")
    
    # Check configuration
    if not Config.DISCORD_TOKEN or Config.DISCORD_TOKEN == 'your_bot_token_here':
        warnings.append(".env dosyasında DISCORD_TOKEN ayarlanmamış")
    else:
        print("✅ Discord Token: Ayarlanmış")
    
    if not Config.GUILD_ID:
        warnings.append("GUILD_ID ayarlanmamış (global komutlar kullanılacak)")
    else:
        print("✅ Guild ID: Ayarlanmış")
    
    if not Config.ADMIN_CHANNEL_ID:
        warnings.append("ADMIN_CHANNEL_ID ayarlanmamış (hata logları devre dışı)")
    else:
        print("✅ Admin Channel ID: Ayarlanmış")
    
    # Test cog imports
    try:
        sys.path.append('.')
        from cogs import work_commands, leaderboard, admin_panel
        print("✅ Cog modülleri: Yüklenebilir")
    except Exception as e:
        errors.append(f"Cog yükleme hatası: {e}")
    
    # Summary
    print(f"\n{'='*50}")
    print("📊 DOĞRULAMA SONUCU")
    print(f"{'='*50}")
    
    if not errors and not warnings:
        print("🎉 Tüm kontroller başarılı! Bot çalıştırılmaya hazır.")
    else:
        if errors:
            print(f"\n❌ HATALAR ({len(errors)}):")
            for error in errors:
                print(f"   • {error}")
        
        if warnings:
            print(f"\n⚠️  UYARILAR ({len(warnings)}):")
            for warning in warnings:
                print(f"   • {warning}")
        
        if errors:
            print("\n🚫 Hatalar düzeltilmeden bot çalışmayabilir.")
        else:
            print("\n✅ Sadece uyarılar var, bot çalışabilir.")
    
    print(f"\n{'='*50}")
    print("🚀 BAŞLATMA TALİMATLARI:")
    print("1. .env dosyasını düzenleyin (özellikle DISCORD_TOKEN)")
    print("2. Bot'u başlatın: python bot.py")
    print("3. Discord'da slash komutları kullanın")
    print(f"{'='*50}")

if __name__ == "__main__":
    asyncio.run(validate_bot())