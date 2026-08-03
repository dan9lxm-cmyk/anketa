# commands/admin_commands.py
import discord
from discord.ext import commands

try:
    from config import *
except ImportError:
    print("⚠️ config.py не найден")

from models.database import ApplicationsDB, ChatsDB


class AdminCommands(commands.Cog):
    """Административные команды"""
    
    def __init__(self, bot):
        self.bot = bot
        self.apps_db = ApplicationsDB()
        self.chats_db = ChatsDB()
    
    @commands.command(name='clean_apps')
    @commands.has_permissions(administrator=True)
    async def clean_apps(self, ctx):
        """Очищает неактивные заявки"""
        try:
            applications = self.apps_db.get_all()
            deleted = 0
            
            for app_id, app_data in list(applications.items()):
                if not app_data.get("is_active", True):
                    del applications[app_id]
                    deleted += 1
            
            self.apps_db.save({"applications": applications})
            await ctx.send(f"✅ Удалено неактивных заявок: {deleted}")
        except Exception as e:
            print(f"❌ Ошибка в clean_apps: {e}")
            await ctx.send("❌ Произошла ошибка.", ephemeral=True)
    
    @commands.command(name='set_welcome')
    @commands.has_permissions(administrator=True)
    async def set_welcome(self, ctx, style: str = None):
        """Устанавливает стиль приветствия"""
        try:
            if not style:
                styles = ", ".join(WELCOME_STYLES.keys())
                await ctx.send(f"📋 Доступные стили: {styles}\nИспользуйте `!set_welcome <название_стиля>`")
                return
            
            if set_welcome_style(style):
                await ctx.send(f"✅ Стиль приветствия изменен на: **{style}**")
                
                welcome_channel = discord.utils.get(ctx.guild.channels, name=WELCOME_CHANNEL_NAME)
                if welcome_channel:
                    await create_welcome_message(welcome_channel, ctx.guild)
            else:
                styles = ", ".join(WELCOME_STYLES.keys())
                await ctx.send(f"❌ Стиль '{style}' не найден! Доступные: {styles}")
        except Exception as e:
            print(f"❌ Ошибка в set_welcome: {e}")
            await ctx.send("❌ Произошла ошибка.", ephemeral=True)
    
    @commands.command(name='reset_welcome')
    @commands.has_permissions(administrator=True)
    async def reset_welcome(self, ctx):
        """Сбрасывает приветственное сообщение"""
        try:
            welcome_channel = discord.utils.get(ctx.guild.channels, name=WELCOME_CHANNEL_NAME)
            if welcome_channel:
                await create_welcome_message(welcome_channel, ctx.guild)
                await ctx.send("✅ Приветственное сообщение пересоздано!")
            else:
                await ctx.send(f"❌ Канал '{WELCOME_CHANNEL_NAME}' не найден!")
        except Exception as e:
            print(f"❌ Ошибка в reset_welcome: {e}")
            await ctx.send("❌ Произошла ошибка.", ephemeral=True)
    
    @commands.command(name='moderate')
    @commands.has_permissions(administrator=True)
    async def moderate(self, ctx, channel: discord.TextChannel = None):
        """Запускает модерацию канала"""
        try:
            if not channel:
                channel = discord.utils.get(ctx.guild.channels, name=DATING_CHANNEL_NAME)
                if not channel:
                    await ctx.send(f"❌ Канал '{DATING_CHANNEL_NAME}' не найден!")
                    return
            
            await ctx.send(f"🔍 Начинаю проверку канала {channel.mention}...")
            await moderate_existing_messages(channel)
            await ctx.send("✅ Модерация завершена!")
        except Exception as e:
            print(f"❌ Ошибка в moderate: {e}")
            await ctx.send("❌ Произошла ошибка.", ephemeral=True)
    
    @commands.command(name='stats')
    async def stats(self, ctx):
        """Показывает статистику бота"""
        try:
            apps_count = len(self.apps_db.get_all())
            chats_count = len(self.chats_db.get_all())
            
            embed = discord.Embed(
                title="📊 Статистика бота",
                color=discord.Color.blue()
            )
            embed.add_field(name="📝 Всего заявок", value=str(apps_count), inline=True)
            embed.add_field(name="💬 Всего диалогов", value=str(chats_count), inline=True)
            embed.add_field(name="🤖 Пользователей", value=str(len(self.bot.users)), inline=True)
            embed.add_field(name="🔄 Серверов", value=str(len(self.bot.guilds)), inline=True)
            
            await ctx.send(embed=embed)
        except Exception as e:
            print(f"❌ Ошибка в stats: {e}")
            await ctx.send("❌ Произошла ошибка.", ephemeral=True)