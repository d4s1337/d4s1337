"""Configuration management for Discord Mesai Bot."""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Bot configuration class."""
    
    # Discord settings
    DISCORD_TOKEN: str = os.getenv('DISCORD_TOKEN', '')
    
    # Parse GUILD_ID safely
    _guild_id = os.getenv('GUILD_ID', '')
    GUILD_ID: Optional[int] = None
    if _guild_id and _guild_id.isdigit():
        GUILD_ID = int(_guild_id)
    
    # Parse ADMIN_CHANNEL_ID safely  
    _admin_channel_id = os.getenv('ADMIN_CHANNEL_ID', '')
    ADMIN_CHANNEL_ID: Optional[int] = None
    if _admin_channel_id and _admin_channel_id.isdigit():
        ADMIN_CHANNEL_ID = int(_admin_channel_id)
    
    # Database settings
    DATABASE_PATH: str = os.getenv('DATABASE_PATH', './data/mesai_bot.db')
    BACKUP_DIRECTORY: str = os.getenv('BACKUP_DIRECTORY', './backups/')
    
    # Bot settings
    AUTO_WORK_LIMIT_HOURS: int = int(os.getenv('AUTO_WORK_LIMIT_HOURS', '12'))
    WEEKLY_RESET_DAY: int = int(os.getenv('WEEKLY_RESET_DAY', '6'))  # Sunday
    WEEKLY_RESET_HOUR: int = int(os.getenv('WEEKLY_RESET_HOUR', '23'))
    WEEKLY_RESET_MINUTE: int = int(os.getenv('WEEKLY_RESET_MINUTE', '59'))
    BACKUP_INTERVAL_HOURS: int = int(os.getenv('BACKUP_INTERVAL_HOURS', '24'))
    
    # Embed colors
    COLOR_SUCCESS = 0x00ff00
    COLOR_ERROR = 0xff0000
    COLOR_WARNING = 0xffaa00
    COLOR_INFO = 0x0099ff
    COLOR_ADMIN = 0x9900ff
    
    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration."""
        if not cls.DISCORD_TOKEN:
            print("❌ DISCORD_TOKEN is required!")
            return False
        return True