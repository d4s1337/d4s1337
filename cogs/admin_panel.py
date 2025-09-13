"""Admin panel for Discord Mesai Bot."""

import os
from datetime import datetime, timedelta
from typing import List, Dict, Any

import discord
from discord.ext import commands
from discord import app_commands

from config import Config

class AdminPanelView(discord.ui.View):
    """Admin panel view with control buttons."""
    
    def __init__(self, bot, timeout: float = 300):
        """Initialize the admin panel view."""
        super().__init__(timeout=timeout)
        self.bot = bot
    
    @discord.ui.button(label="🚫 Tüm Mesaileri Kapat", style=discord.ButtonStyle.danger, row=0)
    async def close_all_sessions(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Close all active work sessions."""
        if not await self.check_admin(interaction):
            return
        
        try:
            async with self.bot.db.get_connection() as db:
                db.row_factory = lambda cursor, row: dict(zip([column[0] for column in cursor.description], row))
                
                # Get all active sessions
                async with db.execute('SELECT user_id FROM work_sessions WHERE is_active = 1') as cursor:
                    active_sessions = await cursor.fetchall()
                
                closed_count = 0
                for session in active_sessions:
                    user_id = session['user_id']
                    session_data = await self.bot.db.end_work_session(user_id, auto_ended=False)
                    if session_data:
                        closed_count += 1
                        
                        # Notify user
                        user = self.bot.get_user(user_id)
                        if user:
                            try:
                                embed = discord.Embed(
                                    title="🚫 Mesai Kapatıldı",
                                    description="Mesainiz admin tarafından kapatıldı.",
                                    color=Config.COLOR_WARNING,
                                    timestamp=datetime.now()
                                )
                                embed.add_field(
                                    name="Toplam Süre",
                                    value=f"{session_data['duration_minutes'] / 60:.1f} saat",
                                    inline=False
                                )
                                await user.send(embed=embed)
                            except discord.Forbidden:
                                pass  # User has DMs disabled
                
                embed = discord.Embed(
                    title="✅ İşlem Tamamlandı",
                    description=f"{closed_count} aktif mesai kapatıldı.",
                    color=Config.COLOR_SUCCESS,
                    timestamp=datetime.now()
                )
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
                
        except Exception as e:
            await self.bot.log_error("Admin Close All Sessions", str(e))
            await interaction.response.send_message("❌ İşlem sırasında hata oluştu.", ephemeral=True)
    
    @discord.ui.button(label="🔄 Haftalık Sıfırla", style=discord.ButtonStyle.secondary, row=0)
    async def reset_weekly(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Reset weekly statistics."""
        if not await self.check_admin(interaction):
            return
        
        try:
            users_count = await self.bot.db.reset_weekly_stats()
            
            embed = discord.Embed(
                title="✅ Haftalık İstatistikler Sıfırlandı",
                description=f"{users_count} kullanıcının haftalık istatistikleri sıfırlandı.",
                color=Config.COLOR_SUCCESS,
                timestamp=datetime.now()
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            await self.bot.log_error("Admin Reset Weekly", str(e))
            await interaction.response.send_message("❌ İşlem sırasında hata oluştu.", ephemeral=True)
    
    @discord.ui.button(label="💾 Yedek Al", style=discord.ButtonStyle.success, row=0)
    async def create_backup(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Create database backup."""
        if not await self.check_admin(interaction):
            return
        
        try:
            backup_path = await self.bot.db.backup_database()
            
            embed = discord.Embed(
                title="✅ Yedek Oluşturuldu",
                description=f"Veritabanı yedeği başarıyla oluşturuldu.",
                color=Config.COLOR_SUCCESS,
                timestamp=datetime.now()
            )
            embed.add_field(name="Dosya Yolu", value=f"`{backup_path}`", inline=False)
            embed.add_field(name="Dosya Boyutu", value=f"{os.path.getsize(backup_path) / 1024:.1f} KB", inline=True)
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            await self.bot.log_error("Admin Create Backup", str(e))
            await interaction.response.send_message("❌ Yedek oluşturulurken hata oluştu.", ephemeral=True)
    
    @discord.ui.button(label="📊 Sistem Durumu", style=discord.ButtonStyle.primary, row=1)
    async def system_status(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show system status."""
        if not await self.check_admin(interaction):
            return
        
        try:
            async with self.bot.db.get_connection() as db:
                # Get statistics
                async with db.execute('SELECT COUNT(*) FROM users') as cursor:
                    total_users = (await cursor.fetchone())[0]
                
                async with db.execute('SELECT COUNT(*) FROM work_sessions WHERE is_active = 1') as cursor:
                    active_sessions = (await cursor.fetchone())[0]
                
                async with db.execute('SELECT COUNT(*) FROM work_sessions WHERE is_active = 0') as cursor:
                    completed_sessions = (await cursor.fetchone())[0]
                
                # Get today's stats
                today = datetime.now().date()
                async with db.execute(
                    'SELECT COUNT(*) FROM work_sessions WHERE DATE(start_time) = ?',
                    (today,)
                ) as cursor:
                    today_sessions = (await cursor.fetchone())[0]
                
                # Database size
                db_size = os.path.getsize(self.bot.db.db_path) / 1024  # KB
            
            embed = discord.Embed(
                title="📊 Sistem Durumu",
                color=Config.COLOR_ADMIN,
                timestamp=datetime.now()
            )
            
            embed.add_field(name="👥 Toplam Kullanıcı", value=str(total_users), inline=True)
            embed.add_field(name="⏰ Aktif Mesai", value=str(active_sessions), inline=True)
            embed.add_field(name="✅ Tamamlanan Mesai", value=str(completed_sessions), inline=True)
            embed.add_field(name="📅 Bugünkü Mesailer", value=str(today_sessions), inline=True)
            embed.add_field(name="💾 Veritabanı Boyutu", value=f"{db_size:.1f} KB", inline=True)
            embed.add_field(name="🤖 Bot Durumu", value="🟢 Çalışıyor", inline=True)
            
            # Uptime
            if hasattr(self.bot, 'start_time'):
                uptime = datetime.now() - self.bot.start_time
                embed.add_field(
                    name="⏱️ Çalışma Süresi",
                    value=f"{uptime.days} gün, {uptime.seconds // 3600} saat",
                    inline=True
                )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            await self.bot.log_error("Admin System Status", str(e))
            await interaction.response.send_message("❌ Sistem durumu alınırken hata oluştu.", ephemeral=True)
    
    @discord.ui.button(label="🔍 Kullanıcı Ara", style=discord.ButtonStyle.secondary, row=1)
    async def search_user(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Search user statistics."""
        if not await self.check_admin(interaction):
            return
        
        # This would open a modal for user search
        # For simplicity, we'll just show a message
        await interaction.response.send_message(
            "🔍 Kullanıcı aramak için `/istatistik @kullanici` komutunu kullanın.",
            ephemeral=True
        )
    
    @discord.ui.button(label="📝 Günlük Rapor", style=discord.ButtonStyle.success, row=1)
    async def daily_report(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Generate daily report."""
        if not await self.check_admin(interaction):
            return
        
        try:
            today = datetime.now().date()
            yesterday = today - timedelta(days=1)
            
            async with self.bot.db.get_connection() as db:
                db.row_factory = lambda cursor, row: dict(zip([column[0] for column in cursor.description], row))
                
                # Today's sessions
                async with db.execute('''
                    SELECT COUNT(*) as count, COALESCE(SUM(duration_minutes), 0) as total_minutes
                    FROM work_sessions 
                    WHERE DATE(start_time) = ? AND is_active = 0
                ''', (today,)) as cursor:
                    today_data = await cursor.fetchone()
                
                # Yesterday's sessions
                async with db.execute('''
                    SELECT COUNT(*) as count, COALESCE(SUM(duration_minutes), 0) as total_minutes
                    FROM work_sessions 
                    WHERE DATE(start_time) = ? AND is_active = 0
                ''', (yesterday,)) as cursor:
                    yesterday_data = await cursor.fetchone()
                
                # Active sessions
                async with db.execute('SELECT COUNT(*) FROM work_sessions WHERE is_active = 1') as cursor:
                    active_count = (await cursor.fetchone())[0]
                
                # Top performers today
                async with db.execute('''
                    SELECT u.username, SUM(ws.duration_minutes) as total_minutes
                    FROM work_sessions ws
                    JOIN users u ON ws.user_id = u.user_id
                    WHERE DATE(ws.start_time) = ? AND ws.is_active = 0
                    GROUP BY u.user_id, u.username
                    ORDER BY total_minutes DESC
                    LIMIT 5
                ''', (today,)) as cursor:
                    top_performers = await cursor.fetchall()
            
            embed = discord.Embed(
                title="📝 Günlük Mesai Raporu",
                description=f"**{today.strftime('%d.%m.%Y')}** tarihli rapor",
                color=Config.COLOR_ADMIN,
                timestamp=datetime.now()
            )
            
            # Today's stats
            today_hours = today_data['total_minutes'] / 60 if today_data['total_minutes'] else 0
            embed.add_field(
                name="📅 Bugün",
                value=f"**{today_data['count']}** mesai\n**{today_hours:.1f}** saat toplam",
                inline=True
            )
            
            # Yesterday comparison
            yesterday_hours = yesterday_data['total_minutes'] / 60 if yesterday_data['total_minutes'] else 0
            change = today_data['count'] - yesterday_data['count']
            change_emoji = "📈" if change > 0 else "📉" if change < 0 else "➡️"
            
            embed.add_field(
                name="📊 Dün ile Karşılaştırma",
                value=f"{change_emoji} **{change:+d}** mesai farkı\n**{yesterday_hours:.1f}** saat (dün)",
                inline=True
            )
            
            # Active sessions
            embed.add_field(
                name="⏰ Şu Anda",
                value=f"**{active_count}** aktif mesai",
                inline=True
            )
            
            # Top performers
            if top_performers:
                top_text = ""
                for i, performer in enumerate(top_performers[:3], 1):
                    hours = performer['total_minutes'] / 60
                    top_text += f"{i}. **{performer['username']}** - {hours:.1f}h\n"
                
                embed.add_field(
                    name="🏆 Bugünün En Çok Çalışanları",
                    value=top_text,
                    inline=False
                )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            await self.bot.log_error("Admin Daily Report", str(e))
            await interaction.response.send_message("❌ Rapor oluşturulurken hata oluştu.", ephemeral=True)
    
    async def check_admin(self, interaction: discord.Interaction) -> bool:
        """Check if user has admin permissions."""
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Bu komutu kullanmak için admin yetkisine sahip olmalısınız.", ephemeral=True)
            return False
        return True

class AdminCommands(commands.Cog):
    """Admin commands for the bot."""
    
    def __init__(self, bot):
        """Initialize the cog."""
        self.bot = bot
        self.bot.start_time = datetime.now()  # Track bot start time
    
    @app_commands.command(name="admin-panel", description="Admin kontrol panelini aç")
    async def admin_panel(self, interaction: discord.Interaction) -> None:
        """Open admin control panel."""
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Bu komutu kullanmak için admin yetkisine sahip olmalısınız.", ephemeral=True)
            return
        
        try:
            view = AdminPanelView(self.bot)
            
            embed = discord.Embed(
                title="🛠️ Admin Kontrol Paneli",
                description="Bot yönetimi için kontrol paneli",
                color=Config.COLOR_ADMIN,
                timestamp=datetime.now()
            )
            embed.add_field(
                name="📋 Mevcut Özellikler",
                value="• Tüm mesaileri kapat\n• Haftalık istatistikleri sıfırla\n• Veritabanı yedeği al\n• Sistem durumunu görüntüle\n• Günlük rapor oluştur",
                inline=False
            )
            embed.set_footer(text="Butonları kullanarak işlemlerinizi gerçekleştirin.")
            
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            
        except Exception as e:
            await self.bot.log_error("Admin Panel Command", str(e))
            await interaction.response.send_message("❌ Admin paneli açılırken bir hata oluştu.", ephemeral=True)
    
    @app_commands.command(name="kullanici-mesai", description="Belirli kullanıcının mesaisini yönet")
    @app_commands.describe(
        kullanici="Mesaisi yönetilecek kullanıcı",
        islem="Yapılacak işlem"
    )
    @app_commands.choices(islem=[
        app_commands.Choice(name="Mesaiyi Bitir", value="end"),
        app_commands.Choice(name="Mesaiyi Sıfırla", value="reset")
    ])
    async def manage_user_work(
        self,
        interaction: discord.Interaction,
        kullanici: discord.Member,
        islem: app_commands.Choice[str]
    ) -> None:
        """Manage specific user's work session."""
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Bu komutu kullanmak için admin yetkisine sahip olmalısınız.", ephemeral=True)
            return
        
        try:
            if islem.value == "end":
                session_data = await self.bot.db.end_work_session(kullanici.id, auto_ended=False)
                
                if session_data:
                    embed = discord.Embed(
                        title="✅ Mesai Bitirildi",
                        description=f"{kullanici.mention} kullanıcısının mesaisi admin tarafından bitirildi.",
                        color=Config.COLOR_SUCCESS,
                        timestamp=datetime.now()
                    )
                    embed.add_field(
                        name="Toplam Süre",
                        value=f"{session_data['duration_minutes'] / 60:.1f} saat",
                        inline=False
                    )
                    
                    # Notify user
                    try:
                        user_embed = discord.Embed(
                            title="🚫 Mesai Bitirildi",
                            description="Mesainiz admin tarafından bitirildi.",
                            color=Config.COLOR_WARNING,
                            timestamp=datetime.now()
                        )
                        user_embed.add_field(
                            name="Toplam Süre",
                            value=f"{session_data['duration_minutes'] / 60:.1f} saat",
                            inline=False
                        )
                        await kullanici.send(embed=user_embed)
                    except discord.Forbidden:
                        pass  # User has DMs disabled
                    
                else:
                    embed = discord.Embed(
                        title="⚠️ Uyarı",
                        description=f"{kullanici.mention} kullanıcısının aktif mesaisi bulunamadı.",
                        color=Config.COLOR_WARNING
                    )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            await self.bot.log_error("Manage User Work Command", str(e))
            await interaction.response.send_message("❌ İşlem sırasında hata oluştu.", ephemeral=True)

async def setup(bot):
    """Setup function for the cog."""
    await bot.add_cog(AdminCommands(bot))