import asyncio
import time
from typing import Dict, Optional
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    def __init__(self):
        self.command_cooldowns: Dict[str, Dict[int, float]] = defaultdict(dict)
        self.user_cooldowns: Dict[int, Dict[str, float]] = defaultdict(dict)
        self.global_cooldowns: Dict[str, float] = {}
    
    def is_rate_limited(self, user_id: int, command: str, cooldown: int) -> bool:
        """Check if a user is rate limited for a specific command"""
        current_time = time.time()
        user_commands = self.user_cooldowns[user_id]
        
        if command in user_commands:
            last_used = user_commands[command]
            if current_time - last_used < cooldown:
                return True
        
        return False
    
    def set_cooldown(self, user_id: int, command: str):
        """Set a cooldown for a user and command"""
        current_time = time.time()
        self.user_cooldowns[user_id][command] = current_time
    
    def get_remaining_cooldown(self, user_id: int, command: str, cooldown: int) -> float:
        """Get remaining cooldown time for a user and command"""
        current_time = time.time()
        user_commands = self.user_cooldowns[user_id]
        
        if command in user_commands:
            last_used = user_commands[command]
            remaining = cooldown - (current_time - last_used)
            return max(0, remaining)
        
        return 0
    
    def is_global_rate_limited(self, command: str, cooldown: int) -> bool:
        """Check if a command is globally rate limited"""
        current_time = time.time()
        
        if command in self.global_cooldowns:
            last_used = self.global_cooldowns[command]
            if current_time - last_used < cooldown:
                return True
        
        return False
    
    def set_global_cooldown(self, command: str):
        """Set a global cooldown for a command"""
        current_time = time.time()
        self.global_cooldowns[command] = current_time
    
    def cleanup_old_cooldowns(self):
        """Clean up old cooldown entries to prevent memory leaks"""
        current_time = time.time()
        max_age = 3600  # 1 hour
        
        # Clean user cooldowns
        for user_id in list(self.user_cooldowns.keys()):
            user_commands = self.user_cooldowns[user_id]
            for command in list(user_commands.keys()):
                if current_time - user_commands[command] > max_age:
                    del user_commands[command]
            
            if not user_commands:
                del self.user_cooldowns[user_id]
        
        # Clean global cooldowns
        for command in list(self.global_cooldowns.keys()):
            if current_time - self.global_cooldowns[command] > max_age:
                del self.global_cooldowns[command]
    
    async def start_cleanup_task(self):
        """Start the cleanup task"""
        while True:
            try:
                await asyncio.sleep(300)  # Clean up every 5 minutes
                self.cleanup_old_cooldowns()
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
