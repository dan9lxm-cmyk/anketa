# utils/error_handler.py
import discord
from discord.ext import commands
import logging
import traceback
import sys
import asyncio
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot_errors.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('discord_bot')

class ErrorHandler(commands.Cog):
    """Глобальный обработчик ошибок"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Обработка ошибок команд"""
        
        if isinstance(error, commands.CommandNotFound):
            return
        
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ У вас нет прав для этой команды!", delete_after=10)
            return
        
        if isinstance(error, commands.BadArgument):
            await ctx.send(f"❌ Неправильный аргумент: {error}", delete_after=10)
            return
        
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Не хватает аргумента: {error.param.name}", delete_after=10)
            return
        
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"⏳ Подождите {error.retry_after:.1f} секунд!", delete_after=10)
            return
        
        error_msg = f"❌ Ошибка в команде {ctx.command}:\n{error}\n{traceback.format_exc()}"
        logger.error(error_msg)
        await self.log_error(ctx, error)
        
        try:
            await ctx.send("❌ Произошла ошибка. Администраторы уведомлены.", delete_after=15)
        except:
            pass
    
    @commands.Cog.listener()
    async def on_error(self, event, *args, **kwargs):
        error_msg = f"❌ Критическая ошибка в событии {event}:\n{traceback.format_exc()}"
        logger.critical(error_msg)
        await self.log_error(None, error_msg, critical=True)
    
    async def log_error(self, ctx, error, critical=False):
        try:
            from config import LOG_CHANNEL_ID
            channel = self.bot.get_channel(LOG_CHANNEL_ID)
            if not channel:
                return
            
            embed = discord.Embed(
                title="⚠️ ОШИБКА" if not critical else "💀 КРИТИЧЕСКАЯ ОШИБКА",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            
            if ctx:
                embed.add_field(
                    name="📌 Команда",
                    value=f"`{ctx.command}`" if ctx.command else "Неизвестно",
                    inline=True
                )
                embed.add_field(
                    name="👤 Пользователь",
                    value=f"{ctx.author.mention} ({ctx.author.id})",
                    inline=True
                )
                embed.add_field(
                    name="📂 Канал",
                    value=f"{ctx.channel.mention}" if ctx.channel else "Неизвестно",
                    inline=True
                )
            
            error_text = str(error)
            if len(error_text) > 1000:
                error_text = error_text[:997] + "..."
            
            embed.add_field(
                name="📝 Ошибка",
                value=f"```py\n{error_text}\n```",
                inline=False
            )
            
            if hasattr(error, '__traceback__'):
                tb = ''.join(traceback.format_tb(error.__traceback__))
                if len(tb) > 1000:
                    tb = tb[:997] + "..."
                embed.add_field(
                    name="🔍 Трассировка",
                    value=f"```py\n{tb}\n```",
                    inline=False
                )
            
            await channel.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Ошибка при отправке лога: {e}")
    
    @commands.Cog.listener()
    async def on_ready(self):
        logger.info(f"✅ Бот {self.bot.user} запущен и готов к работе!")


async def setup_error_handling(bot):
    """Настройка глобальной обработки ошибок"""
    
    # Регистрируем ког
    await bot.add_cog(ErrorHandler(bot))
    
    # Глобальный перехват исключений
    def global_exception_handler(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        error_msg = f"💀 Необработанное исключение:\n{exc_type.__name__}: {exc_value}\n{''.join(traceback.format_tb(exc_traceback))}"
        logger.critical(error_msg)
        
        try:
            from config import LOG_CHANNEL_ID
            channel = bot.get_channel(LOG_CHANNEL_ID)
            if channel:
                embed = discord.Embed(
                    title="💀 КРИТИЧЕСКАЯ ОШИБКА",
                    description=f"```py\n{error_msg[:1900]}\n```",
                    color=discord.Color.red()
                )
                asyncio.create_task(channel.send(embed=embed))
        except:
            pass
    
    sys.excepthook = global_exception_handler