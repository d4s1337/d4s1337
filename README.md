# Discord Mesai Bot 🤖

Gelişmiş Discord mesai takip botu. Kullanıcıların çalışma saatlerini takip eder, hedefler belirler, sıralamalar oluşturur ve otomatik hatırlatmalar gönderir.

## ✨ Özellikler

### 🎯 Temel Özellikler
- **Mesai Takibi**: Mesai başlatma/bitirme sistemi
- **Hedef Belirleme**: Günlük ve haftalık mesai hedefleri
- **Otomatik Hatırlatmalar**: DM ile hedef hatırlatmaları
- **Mesai Geçmişi**: Son 10 mesai kaydını görüntüleme

### 📊 Sıralama Sistemi
- **Interaktif Leaderboard**: Butonlarla geçiş yapılabilir
  - 📅 Haftalık sıralama
  - 📆 Aylık sıralama
  - 🏆 Genel sıralama
- **Kişisel İstatistikler**: Detaylı mesai analizi

### 🛡️ Güvenlik ve Otomatizasyon
- **Otomatik Mesai Bitirme**: 12 saatten uzun mesailer otomatik bitirilir
- **Haftalık Sıfırlama**: Her Pazar 23:59'da otomatik sıfırlama
- **Veritabanı Yedekleme**: Düzenli otomatik yedekler
- **Gelişmiş Hata Loglama**: Admin kanalına hata bildirimleri

### 🔧 Admin Paneli
- **Toplu İşlemler**: Tüm mesaileri kapatma, sıfırlama
- **Sistem Durumu**: Detaylı sistem istatistikleri
- **Günlük Raporlar**: Otomatik mesai raporları
- **Kullanıcı Yönetimi**: Bireysel kullanıcı mesai yönetimi

## 🚀 Kurulum

### 1. Gereksinimler
```bash
pip install -r requirements.txt
```

### 2. Bot Kurulumu
```bash
python setup.py
```

### 3. Yapılandırma
`.env` dosyasını düzenleyin:
```env
DISCORD_TOKEN=your_bot_token_here
GUILD_ID=your_guild_id_here
ADMIN_CHANNEL_ID=your_admin_channel_id_here
```

### 4. Botu Çalıştırma
```bash
python bot.py
```

## 📝 Komutlar

### 👤 Kullanıcı Komutları
- `/mesai-baslat` - Mesai başlat
- `/mesai-bitir` - Mesai bitir
- `/mesai-durum` - Mevcut mesai durumu
- `/mesai-gecmisi` - Son 10 mesai kaydı
- `/hedef-belirle` - Günlük/haftalık hedef belirle
- `/siralama` - İnteraktif mesai sıralaması
- `/istatistik` - Kişisel veya kullanıcı istatistikleri

### 🛠️ Admin Komutları
- `/admin-panel` - Admin kontrol paneli
- `/kullanici-mesai` - Kullanıcı mesai yönetimi

## 🏗️ Proje Yapısı

```
discord-mesai-bot/
├── bot.py                 # Ana bot dosyası
├── config.py             # Yapılandırma yönetimi
├── database.py           # Veritabanı işlemleri
├── requirements.txt      # Python bağımlılıkları
├── setup.py             # Kurulum scripti
├── .env.example         # Örnek ortam değişkenleri
├── cogs/                # Bot modülleri
│   ├── work_commands.py # Mesai komutları
│   ├── leaderboard.py   # Sıralama sistemi
│   └── admin_panel.py   # Admin paneli
├── data/               # Veritabanı dosyaları
└── backups/           # Otomatik yedekler
```

## 🗄️ Veritabanı Şeması

### Users Tablosu
- `user_id`: Discord kullanıcı ID'si
- `username`: Kullanıcı adı
- `daily_goal_minutes`: Günlük hedef (dakika)
- `weekly_goal_minutes`: Haftalık hedef (dakika)

### Work Sessions Tablosu
- `user_id`: Kullanıcı ID'si
- `start_time`: Başlangıç zamanı
- `end_time`: Bitiş zamanı
- `duration_minutes`: Süre (dakika)
- `is_active`: Aktif durumu
- `auto_ended`: Otomatik bitirildi mi

### Weekly/Monthly Stats Tabloları
- Haftalık ve aylık toplam istatistikler
- Performans takibi için optimize edilmiş

## ⚙️ Yapılandırma Seçenekleri

### `.env` Dosyası Ayarları
```env
# Discord ayarları
DISCORD_TOKEN=bot_token
GUILD_ID=guild_id
ADMIN_CHANNEL_ID=channel_id

# Veritabanı ayarları  
DATABASE_PATH=./data/mesai_bot.db
BACKUP_DIRECTORY=./backups/

# Bot ayarları
AUTO_WORK_LIMIT_HOURS=12
WEEKLY_RESET_DAY=6
WEEKLY_RESET_HOUR=23
WEEKLY_RESET_MINUTE=59
BACKUP_INTERVAL_HOURS=24
```

## 🔄 Otomatik İşlemler

### Haftalık Sıfırlama
- Her Pazar 23:59'da çalışır
- Haftalık istatistikleri sıfırlar
- Kullanıcılara bildirim gönderir

### Otomatik Yedekleme
- 24 saatte bir çalışır
- Veritabanını `backups/` dizinine yedekler
- Admin kanalına bildirim gönderir

### Uzun Mesai Kontrolü
- 30 dakikada bir kontrol eder
- 12 saatten uzun mesaileri otomatik bitirir
- Kullanıcı ve admine uyarı gönderir

### Günlük Hatırlatmalar
- Günde 3 kez kontrol eder (09:00, 13:00, 18:00)
- Hedefini %80'den az tamamlayanlara DM gönderir
- Sadece aktif mesaisi olmayan kullanıcılara

## 🛠️ Geliştirme

### Yeni Özellik Ekleme
1. İlgili cog dosyasını düzenleyin
2. Gerekirse veritabanı şemasını güncelleyin
3. Komutları test edin
4. Dokümantasyonu güncelleyin

### Test Etme
```bash
# Bot'u test modunda çalıştır
python bot.py
```

### Loglama
Bot tüm hataları ve önemli olayları loglar:
- Konsol çıktısı
- Admin kanalına embed gönderimi
- Otomatik hata yakalama

## 📄 Lisans

Bu proje MIT lisansı altında yayınlanmıştır.

## 🤝 Katkıda Bulunma

1. Bu repoyu fork edin
2. Özellik dalı oluşturun (`git checkout -b feature/AmazingFeature`)
3. Değişikliklerinizi commit edin (`git commit -m 'Add some AmazingFeature'`)
4. Dalınıza push edin (`git push origin feature/AmazingFeature`)
5. Pull Request oluşturun

## 📞 İletişim

- **Discord**: @d4s
- **Email**: d4si+github@outlook.com.tr

---

Made with ❤️ by [d4s1337](https://github.com/d4s1337)

