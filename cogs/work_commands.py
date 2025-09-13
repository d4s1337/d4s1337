"""Work session commands for Discord Mesai Bot."""

import asyncio
import aiosqlite
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

import discord
from discord.ext import commands
from discord import app_commands

from config import Config

class WorkCommands(commands.Cog):
    """Work session management commands."""
    
    def __init__(self, bot):
        """Initialize the cog."""
        self.bot = bot
    
    @app_commands.command(name="mesai-baslat", description="Mesai başlat")
    async def start_work(self, interaction: discord.Interaction) -> None:
        """Start a work session."""
        try:
            user_id = interaction.user.id
            username = str(interaction.user)
            
            success = await self.bot.db.start_work_session(user_id, username)
            
            if success:
                embed = discord.Embed(
                    title="✅ Mesai Başladı",
                    description=f"{interaction.user.mention} mesaiye başladı!",
                    color=Config.COLOR_SUCCESS,
                    timestamp=datetime.now()
                )
                embed.add_field(
                    name="Başlangıç Zamanı", 
                    value=f"<t:{int(datetime.now().timestamp())}:F>", 
                    inline=False
                )
                embed.set_footer(text="İyi çalışmalar! 💪")
            else:
                embed = discord.Embed(
                    title="⚠️ Zaten Aktif Mesai Var",
                    description="Zaten aktif bir mesainiz bulunuyor. Önce mevcut mesaiyi bitirin.",
                    color=Config.COLOR_WARNING
                )
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await self.bot.log_error("Start Work Command", str(e))
            await interaction.response.send_message("❌ Mesai başlatılırken bir hata oluştu.", ephemeral=True)
    
    @app_commands.command(name="mesai-bitir", description="Mesai bitir")
    async def end_work(self, interaction: discord.Interaction) -> None:
        """End a work session."""
        try:
            user_id = interaction.user.id
            session = await self.bot.db.end_work_session(user_id)
            
            if session:
                duration_hours = session['duration_minutes'] / 60
                
                embed = discord.Embed(
                    title="🏁 Mesai Bitti",
                    description=f"{interaction.user.mention} mesaiyi tamamladı!",
                    color=Config.COLOR_SUCCESS,
                    timestamp=datetime.now()
                )
                embed.add_field(
                    name="Başlangıç", 
                    value=f"<t:{int(session['start_time'].timestamp())}:F>", 
                    inline=True
                )
                embed.add_field(
                    name="Bitiş", 
                    value=f"<t:{int(session['end_time'].timestamp())}:F>", 
                    inline=True
                )
                embed.add_field(
                    name="Toplam Süre", 
                    value=f"{duration_hours:.1f} saat ({session['duration_minutes']} dk)", 
                    inline=False
                )
                
                if session['auto_ended']:
                    embed.add_field(
                        name="⚠️ Uyarı", 
                        value="Mesai otomatik olarak bitirildi (12 saat sınırı)", 
                        inline=False
                    )
                
                embed.set_footer(text="Harika iş! 🎉")
            else:
                embed = discord.Embed(
                    title="⚠️ Aktif Mesai Bulunamadı",
                    description="Bitirilecek aktif bir mesainiz bulunmuyor.",
                    color=Config.COLOR_WARNING
                )
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await self.bot.log_error("End Work Command", str(e))
            await interaction.response.send_message("❌ Mesai bitirilirken bir hata oluştu.", ephemeral=True)
    
    @app_commands.command(name="mesai-durum", description="Mevcut mesai durumunu göster")
    async def work_status(self, interaction: discord.Interaction) -> None:
        """Show current work status."""
        try:
            user_id = interaction.user.id
            session = await self.bot.db.get_active_session(user_id)
            
            if session:
                start_time = datetime.fromisoformat(session['start_time'])
                current_duration = datetime.now() - start_time
                duration_minutes = int(current_duration.total_seconds() / 60)
                duration_hours = duration_minutes / 60
                
                embed = discord.Embed(
                    title="⏰ Mevcut Mesai Durumu",
                    description=f"{interaction.user.mention} aktif mesaisi",
                    color=Config.COLOR_INFO,
                    timestamp=datetime.now()
                )
                embed.add_field(
                    name="Başlangıç Zamanı", 
                    value=f"<t:{int(start_time.timestamp())}:F>", 
                    inline=False
                )
                embed.add_field(
                    name="Geçen Süre", 
                    value=f"{duration_hours:.1f} saat ({duration_minutes} dk)", 
                    inline=False
                )
                
                # Warning if approaching 12 hour limit
                if duration_hours >= 10:
                    embed.add_field(
                        name="⚠️ Uyarı", 
                        value=f"12 saat sınırına yaklaşıyorsunuz! ({12 - duration_hours:.1f} saat kaldı)", 
                        inline=False
                    )
            else:
                embed = discord.Embed(
                    title="😴 Mesai Durumu",
                    description=f"{interaction.user.mention} şu anda mesaide değil.",
                    color=Config.COLOR_INFO
                )
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await self.bot.log_error("Work Status Command", str(e))
            await interaction.response.send_message("❌ Durum gösterilirken bir hata oluştu.", ephemeral=True)
    
    @app_commands.command(name="mesai-gecmisi", description="Son 10 mesai kaydını göster")
    async def work_history(self, interaction: discord.Interaction) -> None:
        """Show work history."""
        try:
            user_id = interaction.user.id
            history = await self.bot.db.get_user_work_history(user_id, 10)
            
            if not history:
                embed = discord.Embed(
                    title="📋 Mesai Geçmişi",
                    description="Henüz mesai kaydınız bulunmuyor.",
                    color=Config.COLOR_INFO
                )
                await interaction.response.send_message(embed=embed)
                return
            
            embed = discord.Embed(
                title="📋 Mesai Geçmişi",
                description=f"{interaction.user.mention} - Son {len(history)} mesai kaydı",
                color=Config.COLOR_INFO,
                timestamp=datetime.now()
            )
            
            total_minutes = 0
            for i, session in enumerate(history, 1):
                start_time = datetime.fromisoformat(session['start_time'])
                duration_hours = session['duration_minutes'] / 60
                total_minutes += session['duration_minutes']
                
                auto_ended_text = " (Otomatik)" if session['auto_ended'] else ""
                
                embed.add_field(
                    name=f"{i}. {start_time.strftime('%d.%m.%Y')}",
                    value=f"🕐 {duration_hours:.1f} saat{auto_ended_text}",
                    inline=True
                )
            
            embed.add_field(
                name="📊 Toplam",
                value=f"{total_minutes / 60:.1f} saat ({len(history)} oturum)",
                inline=False
            )
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await self.bot.log_error("Work History Command", str(e))
            await interaction.response.send_message("❌ Geçmiş gösterilirken bir hata oluştu.", ephemeral=True)
    
    @app_commands.command(name="hedef-belirle", description="Günlük veya haftalık mesai hedefi belirle")
    @app_commands.describe(
        tip="Hedef tipi (günlük veya haftalık)",
        saat="Hedef saat (örn: 8 saat için 8 yazın)"
    )
    @app_commands.choices(tip=[
        app_commands.Choice(name="Günlük", value="daily"),
        app_commands.Choice(name="Haftalık", value="weekly")
    ])
    async def set_goal(
        self, 
        interaction: discord.Interaction, 
        tip: app_commands.Choice[str],
        saat: float
    ) -> None:
        """Set daily or weekly work goal."""
        try:
            if saat <= 0 or saat > 24:
                await interaction.response.send_message("❌ Geçersiz saat değeri! (0-24 arası olmalı)", ephemeral=True)
                return
            
            user_id = interaction.user.id
            username = str(interaction.user)
            minutes = int(saat * 60)
            
            # Get or create user
            await self.bot.db.get_or_create_user(user_id, username)
            
            # Update goal
            async with self.bot.db.get_connection() as db:
                if tip.value == "daily":
                    await db.execute(
                        'UPDATE users SET daily_goal_minutes = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?',
                        (minutes, user_id)
                    )
                    goal_type = "günlük"
                else:
                    await db.execute(
                        'UPDATE users SET weekly_goal_minutes = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?',
                        (minutes, user_id)
                    )
                    goal_type = "haftalık"
                
                await db.commit()
            
            embed = discord.Embed(
                title="🎯 Hedef Belirlendi",
                description=f"{goal_type.capitalize()} mesai hedefiniz {saat} saat olarak güncellendi!",
                color=Config.COLOR_SUCCESS,
                timestamp=datetime.now()
            )
            embed.add_field(name="Yeni Hedef", value=f"{saat} saat ({minutes} dakika)", inline=False)
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await self.bot.log_error("Set Goal Command", str(e))
            await interaction.response.send_message("❌ Hedef belirlenirken bir hata oluştu.", ephemeral=True)
    
    async def check_long_sessions_task(self) -> None:
        """Check for sessions longer than 12 hours and auto-end them."""
        try:
            limit_minutes = Config.AUTO_WORK_LIMIT_HOURS * 60
            cutoff_time = datetime.now() - timedelta(hours=Config.AUTO_WORK_LIMIT_HOURS)
            
            async with self.bot.db.get_connection() as db:
                db.row_factory = aiosqlite.Row
                async with db.execute('''
                    SELECT user_id, start_time FROM work_sessions 
                    WHERE is_active = 1 AND start_time <= ?
                ''', (cutoff_time,)) as cursor:
                    long_sessions = await cursor.fetchall()
            
            for session in long_sessions:
                user_id = session['user_id']
                session_data = await self.bot.db.end_work_session(user_id, auto_ended=True)
                
                if session_data:
                    # Notify user
                    user = self.bot.get_user(user_id)
                    if user:
                        try:
                            embed = discord.Embed(
                                title="⏰ Otomatik Mesai Bitişi",
                                description=f"Mesainiz 12 saat sınırına ulaştığı için otomatik olarak bitirildi.",
                                color=Config.COLOR_WARNING,
                                timestamp=datetime.now()
                            )
                            embed.add_field(
                                name="Toplam Süre", 
                                value=f"{session_data['duration_minutes'] / 60:.1f} saat", 
                                inline=False
                            )
                            embed.add_field(
                                name="Neden?", 
                                value="Uzun çalışma saatleri sağlığınız için zararlı olabilir. Dinlenmeyi unutmayın! 😊", 
                                inline=False
                            )
                            
                            await user.send(embed=embed)
                        except discord.Forbidden:
                            pass  # User has DMs disabled
                    
                    # Notify admin
                    if self.bot.admin_channel:
                        embed = discord.Embed(
                            title="🚨 Otomatik Mesai Bitişi",
                            description=f"<@{user_id}> kullanıcısının mesaisi 12 saat sınırı nedeniyle otomatik bitirildi.",
                            color=Config.COLOR_WARNING,
                            timestamp=datetime.now()
                        )
                        embed.add_field(
                            name="Toplam Süre", 
                            value=f"{session_data['duration_minutes'] / 60:.1f} saat", 
                            inline=False
                        )
                        
                        await self.bot.admin_channel.send(embed=embed)
        
        except Exception as e:
            await self.bot.log_error("Check Long Sessions", str(e))

async def setup(bot):
    """Setup function for the cog."""
    await bot.add_cog(WorkCommands(bot))