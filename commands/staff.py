"""
Команда /staff для управления Embed со списком администрации.
"""

import logging
import discord
from discord import app_commands
from services.staff_embed import StaffEmbedService

logger = logging.getLogger(__name__)


class StaffCommand:
    """
    Команда /staff.
    """
    
    def __init__(self, bot: discord.Client, staff_embed_service: StaffEmbedService):
        """
        Инициализировать команду.
        
        Args:
            bot: Экземпляр Discord бота
            staff_embed_service: Сервис для работы с Embed
        """
        self.bot = bot
        self.staff_embed_service = staff_embed_service
    
    def register_commands(self, tree: app_commands.CommandTree):
        """
        Зарегистрировать команды в дереве команд.
        
        Args:
            tree: Дерево команд Discord
        """
        
        @tree.command(name="staff", description="Создать/обновить Embed со списком администрации")
        async def staff_command(interaction: discord.Interaction):
            """Команда /staff"""
            await interaction.response.defer(ephemeral=True)
            
            try:
                guild = interaction.guild
                if guild is None:
                    await interaction.followup.send("❌ Команда доступна только на сервере", ephemeral=True)
                    return
                
                # Создаём или получаем сообщение
                message = await self.staff_embed_service.get_or_create_staff_message(guild)
                
                if message:
                    await interaction.followup.send(
                        f"✅ Embed создан/обновлён в канале <#{message.channel.id}>",
                        ephemeral=True
                    )
                else:
                    await interaction.followup.send(
                        "❌ Ошибка при создании Embed. Проверьте логи.",
                        ephemeral=True
                    )
                    
            except Exception as e:
                logger.error(f"Ошибка в команде /staff: {e}", exc_info=True)
                await interaction.followup.send(
                    "❌ Произошла ошибка при выполнении команды",
                    ephemeral=True
                )
        
        @tree.command(name="staff_refresh", description="Принудительно обновить Embed /staff")
        async def staff_refresh_command(interaction: discord.Interaction):
            """Команда /staff refresh"""
            await interaction.response.defer(ephemeral=True)
            
            try:
                guild = interaction.guild
                if guild is None:
                    await interaction.followup.send("❌ Команда доступна только на сервере", ephemeral=True)
                    return
                
                # Обновляем Embed
                success = await self.staff_embed_service.update_staff_message(guild)
                
                if success:
                    await interaction.followup.send("✅ Embed обновлён", ephemeral=True)
                else:
                    await interaction.followup.send(
                        "❌ Ошибка при обновлении Embed. Проверьте логи.",
                        ephemeral=True
                    )
                    
            except Exception as e:
                logger.error(f"Ошибка в команде /staff refresh: {e}", exc_info=True)
                await interaction.followup.send(
                    "❌ Произошла ошибка при выполнении команды",
                    ephemeral=True
                )

