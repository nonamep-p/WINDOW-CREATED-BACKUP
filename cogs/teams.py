import discord
from discord.ext import commands
from discord import app_commands

class TeamsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="team", description="Team coordination commands")
    async def team_command(self, interaction: discord.Interaction, action: str, 
                          activity: str = None, team_id: str = None):
        """Main team coordination command"""
        await interaction.response.send_message("Team system is working!", ephemeral=True)
    
    @app_commands.command(name="effort", description="Check your effort-based rewards")
    async def effort_command(self, interaction: discord.Interaction):
        """Check player's effort and reward summary"""
        await interaction.response.send_message("Effort system is working!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(TeamsCog(bot))
