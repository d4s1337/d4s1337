"""Leaderboard system for Discord Mesai Bot."""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

import discord
from discord.ext import commands
from discord import app_commands

from config import Config

class LeaderboardView(discord.ui.View):
    """Interactive leaderboard view with buttons."""
    
    def __init__(self, bot, timeout: float = 300):
        """Initialize the view."""
        super().__init__(timeout=timeout)
        self.bot = bot
        self.current_period = "weekly"
    
    async def get_leaderboard_data(self, period: str) -> List[Dict[str, Any]]:
        """Get leaderboard data for specified period."""
        async with self.bot.db.get_connection() as db:
            db.row_factory = lambda cursor, row: dict(zip([column[0] for column in cursor.description], row))
            
            if period == "weekly":
                # Current week
                today = datetime.now().date()
                week_start = today - timedelta(days=today.weekday())
                
                query = '''
                    SELECT u.username, u.user_id, ws.total_minutes, ws.sessions_count
                    FROM weekly_stats ws
                    JOIN users u ON ws.user_id = u.user_id
                    WHERE ws.week_start = ?
                    ORDER BY ws.total_minutes DESC
                    LIMIT 10
                '''
                params = (week_start,)
                
            elif period == "monthly":
                # Current month
                today = datetime.now().date()
                month_start = today.replace(day=1)
                
                query = '''
                    SELECT u.username, u.user_id, ms.total_minutes, ms.sessions_count
                    FROM monthly_stats ms
                    JOIN users u ON ms.user_id = u.user_id
                    WHERE ms.month_start = ?
                    ORDER BY ms.total_minutes DESC
                    LIMIT 10
                '''
                params = (month_start,)
                
            else:  # overall
                query = '''
                    SELECT u.username, u.user_id, 
                           SUM(ws.duration_minutes) as total_minutes,
                           COUNT(ws.id) as sessions_count
                    FROM work_sessions ws
                    JOIN users u ON ws.user_id = u.user_id
                    WHERE ws.is_active = 0
                    GROUP BY u.user_id, u.username
                    ORDER BY total_minutes DESC
                    LIMIT 10
                '''
                params = ()
            
            async with db.execute(query, params) as cursor:
                return await cursor.fetchall()
    
    async def create_embed(self, period: str) -> discord.Embed:
        """Create leaderboard embed."""
        data = await self.get_leaderboard_data(period)
        
        period_names = {
            "weekly": "Bu Hafta",
            "monthly": "Bu Ay", 
            "overall": "Genel Sıralama"
        }
        
        period_emojis = {
            "weekly": "📅",
            "monthly": "📆",
            "overall": "🏆"
        }
        
        embed = discord.Embed(
            title=f"{period_emojis[period]} Mesai Sıralaması - {period_names[period]}",
            color=Config.COLOR_INFO,
            timestamp=datetime.now()
        )
        
        if not data:
            embed.description = "Henüz veri bulunmuyor."
            return embed
        
        leaderboard_text = ""
        medal_emojis = ["🥇", "🥈", "🥉"]
        
        for i, user_data in enumerate(data):
            rank = i + 1
            username = user_data['username']
            total_hours = user_data['total_minutes'] / 60
            sessions = user_data['sessions_count']
            
            medal = medal_emojis[i] if i < 3 else f"{rank}."
            
            leaderboard_text += f"{medal} **{username}**\n"
            leaderboard_text += f"   ⏱️ {total_hours:.1f} saat ({sessions} oturum)\n\n"
        
        embed.description = leaderboard_text
        
        # Add period info
        if period == "weekly":
            today = datetime.now().date()
            week_start = today - timedelta(days=today.weekday())
            week_end = week_start + timedelta(days=6)
            embed.set_footer(text=f"Hafta: {week_start.strftime('%d.%m')} - {week_end.strftime('%d.%m.%Y')}")
        elif period == "monthly":
            today = datetime.now().date()
            embed.set_footer(text=f"Ay: {today.strftime('%B %Y')}")
        else:
            embed.set_footer(text="Tüm zamanlar")
        
        return embed
    
    @discord.ui.button(label="📅 Haftalık", style=discord.ButtonStyle.primary, custom_id="weekly")
    async def weekly_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show weekly leaderboard."""
        self.current_period = "weekly"
        await self.update_leaderboard(interaction)
    
    @discord.ui.button(label="📆 Aylık", style=discord.ButtonStyle.secondary, custom_id="monthly")
    async def monthly_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show monthly leaderboard."""
        self.current_period = "monthly"
        await self.update_leaderboard(interaction)
    
    @discord.ui.button(label="🏆 Genel", style=discord.ButtonStyle.success, custom_id="overall")
    async def overall_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show overall leaderboard."""
        self.current_period = "overall"
        await self.update_leaderboard(interaction)
    
    @discord.ui.button(label="🔄 Yenile", style=discord.ButtonStyle.gray, custom_id="refresh")
    async def refresh_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Refresh current leaderboard."""
        await self.update_leaderboard(interaction)
    
    async def update_leaderboard(self, interaction: discord.Interaction):
        """Update the leaderboard display."""
        try:
            # Update button styles
            for item in self.children:
                if isinstance(item, discord.ui.Button) and item.custom_id in ["weekly", "monthly", "overall"]:
                    if item.custom_id == self.current_period:
                        item.style = discord.ButtonStyle.primary
                    else:
                        item.style = discord.ButtonStyle.secondary
            
            embed = await self.create_embed(self.current_period)
            await interaction.response.edit_message(embed=embed, view=self)
            
        except Exception as e:
            await interaction.response.send_message("❌ Sıralama güncellenirken bir hata oluştu.", ephemeral=True)
            print(f"Leaderboard update error: {e}")

class LeaderboardCommands(commands.Cog):
    """Leaderboard commands."""
    
    def __init__(self, bot):
        """Initialize the cog."""
        self.bot = bot
    
    @app_commands.command(name="siralama", description="Mesai sıralamasını göster")
    async def leaderboard(self, interaction: discord.Interaction) -> None:
        """Show interactive leaderboard."""
        try:
            view = LeaderboardView(self.bot)
            embed = await view.create_embed("weekly")
            
            await interaction.response.send_message(embed=embed, view=view)
            
        except Exception as e:
            await self.bot.log_error("Leaderboard Command", str(e))
            await interaction.response.send_message("❌ Sıralama gösterilirken bir hata oluştu.", ephemeral=True)
    
    @app_commands.command(name="istatistik", description="Kişisel mesai istatistiklerini göster")
    async def personal_stats(self, interaction: discord.Interaction, kullanici: discord.Member = None) -> None:
        """Show personal work statistics."""
        try:
            target_user = kullanici if kullanici else interaction.user
            user_id = target_user.id
            
            # Get user data
            async with self.bot.db.get_connection() as db:
                db.row_factory = lambda cursor, row: dict(zip([column[0] for column in cursor.description], row))
                
                # Get user info and goals
                async with db.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)) as cursor:
                    user_data = await cursor.fetchone()
                
                if not user_data:
                    embed = discord.Embed(
                        title="📊 Kişisel İstatistikler",
                        description=f"{target_user.mention} henüz mesai sistemi kullanmamış.",
                        color=Config.COLOR_INFO
                    )
                    await interaction.response.send_message(embed=embed)
                    return
                
                # Get weekly stats
                today = datetime.now().date()
                week_start = today - timedelta(days=today.weekday())
                async with db.execute(
                    'SELECT * FROM weekly_stats WHERE user_id = ? AND week_start = ?',
                    (user_id, week_start)
                ) as cursor:
                    weekly_data = await cursor.fetchone()
                
                # Get monthly stats
                month_start = today.replace(day=1)
                async with db.execute(
                    'SELECT * FROM monthly_stats WHERE user_id = ? AND month_start = ?',
                    (user_id, month_start)
                ) as cursor:
                    monthly_data = await cursor.fetchone()
                
                # Get overall stats
                async with db.execute('''
                    SELECT COUNT(*) as total_sessions, 
                           COALESCE(SUM(duration_minutes), 0) as total_minutes
                    FROM work_sessions 
                    WHERE user_id = ? AND is_active = 0
                ''', (user_id,)) as cursor:
                    overall_data = await cursor.fetchone()
                
                # Get current active session
                async with db.execute(
                    'SELECT * FROM work_sessions WHERE user_id = ? AND is_active = 1',
                    (user_id,)
                ) as cursor:
                    active_session = await cursor.fetchone()
            
            embed = discord.Embed(
                title="📊 Kişisel İstatistikler",
                description=f"{target_user.mention} mesai özeti",
                color=Config.COLOR_INFO,
                timestamp=datetime.now()
            )
            
            # Goals
            daily_goal_hours = user_data['daily_goal_minutes'] / 60
            weekly_goal_hours = user_data['weekly_goal_minutes'] / 60
            embed.add_field(
                name="🎯 Hedefler",
                value=f"Günlük: {daily_goal_hours:.1f} saat\nHaftalık: {weekly_goal_hours:.1f} saat",
                inline=True
            )
            
            # Weekly stats
            weekly_minutes = weekly_data['total_minutes'] if weekly_data else 0
            weekly_hours = weekly_minutes / 60
            weekly_progress = (weekly_hours / weekly_goal_hours * 100) if weekly_goal_hours > 0 else 0
            
            embed.add_field(
                name="📅 Bu Hafta",
                value=f"{weekly_hours:.1f} saat\n{weekly_progress:.1f}% hedef",
                inline=True
            )
            
            # Monthly stats
            monthly_minutes = monthly_data['total_minutes'] if monthly_data else 0
            monthly_hours = monthly_minutes / 60
            
            embed.add_field(
                name="📆 Bu Ay",
                value=f"{monthly_hours:.1f} saat",
                inline=True
            )
            
            # Overall stats
            total_hours = overall_data['total_minutes'] / 60
            total_sessions = overall_data['total_sessions']
            
            embed.add_field(
                name="🏆 Genel Toplam",
                value=f"{total_hours:.1f} saat\n{total_sessions} oturum",
                inline=True
            )
            
            # Active session
            if active_session:
                start_time = datetime.fromisoformat(active_session['start_time'])
                current_duration = datetime.now() - start_time
                current_minutes = int(current_duration.total_seconds() / 60)
                current_hours = current_minutes / 60
                
                embed.add_field(
                    name="⏰ Aktif Mesai",
                    value=f"{current_hours:.1f} saat",
                    inline=True
                )
            else:
                embed.add_field(
                    name="😴 Durum",
                    value="Mesaide değil",
                    inline=True
                )
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await self.bot.log_error("Personal Stats Command", str(e))
            await interaction.response.send_message("❌ İstatistikler gösterilirken bir hata oluştu.", ephemeral=True)

async def setup(bot):
    """Setup function for the cog."""
    await bot.add_cog(LeaderboardCommands(bot))