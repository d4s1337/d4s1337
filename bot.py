"""Discord Mesai Bot - Advanced work time tracking bot."""

import asyncio
import logging
import traceback
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

import discord
from discord.ext import commands, tasks
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import Config
from database import Database

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MesaiBot(commands.Bot):
    """Advanced Discord work time tracking bot."""
    
    def __init__(self):
        """Initialize the bot."""
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        
        super().__init__(
            command_prefix='!',
            intents=intents,
            help_command=None
        )
        
        self.db = Database()
        self.scheduler = AsyncIOScheduler()
        self.admin_channel: Optional[discord.TextChannel] = None
    
    async def setup_hook(self) -> None:
        """Setup bot after login."""
        # Initialize database
        await self.db.init_db()
        
        # Load cogs
        await self.load_extension('cogs.work_commands')
        await self.load_extension('cogs.leaderboard')
        await self.load_extension('cogs.admin_panel')
        
        # Setup admin channel
        if Config.ADMIN_CHANNEL_ID:
            self.admin_channel = self.get_channel(Config.ADMIN_CHANNEL_ID)
        
        # Start background tasks
        self.check_long_sessions.start()
        self.daily_reminders.start()
        
        # Setup scheduler
        self.scheduler.start()
        
        # Schedule weekly reset
        self.scheduler.add_job(
            self.weekly_reset,
            'cron',
            day_of_week=Config.WEEKLY_RESET_DAY,
            hour=Config.WEEKLY_RESET_HOUR,
            minute=Config.WEEKLY_RESET_MINUTE,
            id='weekly_reset'
        )
        
        # Schedule database backup
        self.scheduler.add_job(
            self.create_backup,
            'interval',
            hours=Config.BACKUP_INTERVAL_HOURS,
            id='database_backup'
        )
        
        logger.info(f"Bot setup complete. Logged in as {self.user}")
    
    async def on_ready(self) -> None:
        """Called when bot is ready."""
        logger.info(f"Bot is ready! Logged in as {self.user}")
        
        # Sync commands
        if Config.GUILD_ID:
            guild = discord.Object(id=Config.GUILD_ID)
            synced = await self.tree.sync(guild=guild)
            logger.info(f"Synced {len(synced)} commands to guild {Config.GUILD_ID}")
        else:
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} commands globally")
    
    async def on_error(self, event: str, *args, **kwargs) -> None:
        """Handle bot errors."""
        error_msg = f"Error in event {event}: {traceback.format_exc()}"
        logger.error(error_msg)
        await self.log_error("Bot Error", error_msg, event)
    
    async def log_error(self, title: str, description: str, event: str = None) -> None:
        """Log error to admin channel."""
        if not self.admin_channel:
            return
        
        embed = discord.Embed(
            title=f"🚨 {title}",
            description=f"```\n{description[:1900]}\n```",
            color=Config.COLOR_ERROR,
            timestamp=datetime.now()
        )
        
        if event:
            embed.add_field(name="Event", value=event, inline=False)
        
        try:
            await self.admin_channel.send(embed=embed)
        except Exception as e:
            logger.error(f"Failed to send error log: {e}")
    
    @tasks.loop(minutes=30)
    async def check_long_sessions(self) -> None:
        """Check for work sessions longer than limit and auto-end them."""
        try:
            # Get the work commands cog and call its long session check
            work_cog = self.get_cog('WorkCommands')
            if work_cog:
                await work_cog.check_long_sessions_task()
        except Exception as e:
            await self.log_error("Long Sessions Check", str(e))
    
    @tasks.loop(hours=8)  # Check 3 times a day
    async def daily_reminders(self) -> None:
        """Send daily reminders for incomplete goals."""
        try:
            current_hour = datetime.now().hour
            # Only send reminders during work hours (9 AM, 1 PM, 6 PM)
            if current_hour not in [9, 13, 18]:
                return
            
            today = datetime.now().date()
            
            async with self.db.get_connection() as db:
                db.row_factory = lambda cursor, row: dict(zip([column[0] for column in cursor.description], row))
                
                # Get users with goals but no active session and insufficient daily progress
                async with db.execute('''
                    SELECT u.user_id, u.username, u.daily_goal_minutes,
                           COALESCE(SUM(ws.duration_minutes), 0) as today_minutes
                    FROM users u
                    LEFT JOIN work_sessions ws ON u.user_id = ws.user_id 
                        AND DATE(ws.start_time) = ? AND ws.is_active = 0
                    WHERE u.daily_goal_minutes > 0
                    AND NOT EXISTS (
                        SELECT 1 FROM work_sessions ws2 
                        WHERE ws2.user_id = u.user_id AND ws2.is_active = 1
                    )
                    GROUP BY u.user_id, u.username, u.daily_goal_minutes
                    HAVING today_minutes < u.daily_goal_minutes * 0.8  -- 80% of goal
                ''', (today,)) as cursor:
                    users_needing_reminder = await cursor.fetchall()
            
            for user_data in users_needing_reminder:
                user = self.get_user(user_data['user_id'])
                if user:
                    try:
                        daily_goal_hours = user_data['daily_goal_minutes'] / 60
                        completed_hours = user_data['today_minutes'] / 60
                        remaining_hours = daily_goal_hours - completed_hours
                        
                        embed = discord.Embed(
                            title="⏰ Günlük Mesai Hatırlatması",
                            description="Günlük mesai hedefinizi henüz tamamlamadınız!",
                            color=Config.COLOR_WARNING,
                            timestamp=datetime.now()
                        )
                        embed.add_field(
                            name="📊 Bugünkü Durum",
                            value=f"Hedef: {daily_goal_hours:.1f} saat\nTamamlanan: {completed_hours:.1f} saat\nKalan: {remaining_hours:.1f} saat",
                            inline=False
                        )
                        embed.add_field(
                            name="💡 Öneri",
                            value="Hedefinizi tamamlamak için mesaiye başlayabilirsiniz!",
                            inline=False
                        )
                        embed.set_footer(text="Bu hatırlatmayı almak istemiyorsanız hedeflerinizi sıfırlayabilirsiniz.")
                        
                        await user.send(embed=embed)
                        
                    except discord.Forbidden:
                        pass  # User has DMs disabled
                    except Exception as e:
                        logger.error(f"Failed to send reminder to user {user_data['user_id']}: {e}")
                        
        except Exception as e:
            await self.log_error("Daily Reminders", str(e))
    
    @check_long_sessions.before_loop
    @daily_reminders.before_loop
    async def before_loops(self) -> None:
        """Wait for bot to be ready before starting loops."""
        await self.wait_until_ready()
    
    async def weekly_reset(self) -> None:
        """Reset weekly statistics."""
        try:
            users_count = await self.db.reset_weekly_stats()
            
            embed = discord.Embed(
                title="📊 Haftalık İstatistik Sıfırlandı",
                description=f"Yeni hafta başladı! {users_count} kullanıcının haftalık istatistikleri sıfırlandı.",
                color=Config.COLOR_INFO,
                timestamp=datetime.now()
            )
            
            if self.admin_channel:
                await self.admin_channel.send(embed=embed)
            
            logger.info(f"Weekly reset completed for {users_count} users")
            
        except Exception as e:
            await self.log_error("Weekly Reset", str(e))
    
    async def create_backup(self) -> None:
        """Create database backup."""
        try:
            backup_path = await self.db.backup_database()
            
            embed = discord.Embed(
                title="💾 Veritabanı Yedeği Oluşturuldu",
                description=f"Yedek dosyası: `{backup_path}`",
                color=Config.COLOR_SUCCESS,
                timestamp=datetime.now()
            )
            
            if self.admin_channel:
                await self.admin_channel.send(embed=embed)
            
            logger.info(f"Database backup created: {backup_path}")
            
        except Exception as e:
            await self.log_error("Database Backup", str(e))

def main():
    """Main function to run the bot."""
    if not Config.validate():
        return
    
    bot = MesaiBot()
    
    try:
        bot.run(Config.DISCORD_TOKEN)
    except Exception as e:
        logger.error(f"Failed to run bot: {e}")

if __name__ == "__main__":
    main()