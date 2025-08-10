import discord
from discord.ext import commands
import logging

from utils.helpers import create_embed, get_plagg_quote

logger = logging.getLogger(__name__)

class AliasesCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="help")
    async def prefix_help(self, ctx: commands.Context):
        """Prefix alias for help"""
        help_text = (
            "**🎮 Basic Commands:**\n"
            "• /character create — Create your character\n"
            "• /fight — Start a battle\n"
            "• /dungeon — Enter a dungeon\n"
            "• /inventory — View your items\n"
            "• /shop — Visit the shop\n"
            "• /tutorial start — Guided intro\n\n"
            "**💡 Tips:**\n"
            "• Start with /tutorial start\n"
            "• Use /play hub for a quick panel\n"
        )
        embed = create_embed(
            title="🧀 Plagg's RPG Help",
            description=f"{help_text}\n{get_plagg_quote()}",
            color=discord.Color.blue(),
        )
        await ctx.send(embed=embed)

    @commands.command(name="tutorial")
    async def prefix_tutorial(self, ctx: commands.Context, action: str = "help"):
        """Prefix alias for tutorial: !tutorial [start|continue|skip|help]"""
        user_id = ctx.author.id
        try:
            if action.lower() == "start":
                result = await self.bot.tutorial_system.start_tutorial(user_id)
                if result.get("success"):
                    step = result["step"]
                    embed = create_embed(
                        title=f"🎓 Tutorial Started - Step {step['step']}",
                        description=f"**{step['title']}**\n\n{step['description']}\n\n{get_plagg_quote()}",
                        color=discord.Color.blue(),
                    )
                else:
                    embed = create_embed(title="❌ Tutorial Error", description=result.get("message","Error"), color=discord.Color.red())
            elif action.lower() == "continue":
                result = await self.bot.tutorial_system.advance_tutorial(user_id)
                if result.get("success") and result.get("completed"):
                    embed = create_embed(title="🎉 Tutorial Complete!", description=result.get("message","Well done!"), color=discord.Color.green())
                elif result.get("success"):
                    step = result["step"]
                    embed = create_embed(title=f"🎓 Tutorial - Step {step['step']}", description=f"**{step['title']}**\n\n{step['description']}", color=discord.Color.blue())
                else:
                    embed = create_embed(title="❌ Tutorial Error", description=result.get("message","Error"), color=discord.Color.red())
            elif action.lower() == "skip":
                result = await self.bot.tutorial_system.skip_tutorial(user_id)
                embed = create_embed(title="⏭️ Tutorial Skipped", description=result.get("message","Skipped."), color=discord.Color.orange())
            else:
                # help
                help_data = self.bot.tutorial_system.get_tutorial_help()
                help_text = ""
                for section in help_data:
                    help_text += f"**{section['title']}**\n"
                    for line in section.get("commands", section.get("info", [])):
                        help_text += f"• {line}\n"
                    help_text += "\n"
                embed = create_embed(title="📚 Tutorial Help", description=f"{help_text}\n{get_plagg_quote()}", color=discord.Color.blue())
        except Exception as e:
            logger.exception("tutorial alias error")
            embed = create_embed(title="❌ Error", description=str(e), color=discord.Color.red())
        await ctx.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(AliasesCog(bot))
