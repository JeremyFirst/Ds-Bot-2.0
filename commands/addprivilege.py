"""
Команда /addprivilege для добавления/обновления привилегий.
"""

import logging
import discord
from discord import app_commands
from datetime import datetime
from typing import Optional
from config.config_loader import get_config
from database.connection import get_db_session
from database.models import UserPrivilege
from services.rcon import RCONClient
from services.staff_embed import StaffEmbedService
from utils.steam import validate_steam_id
from utils.pinfo_parser import parse_pinfo_response
from utils.timezone import format_datetime_utc3

logger = logging.getLogger(__name__)


class AddPrivilegeCommand:
    """
    Команда /addprivilege.
    """
    
    def __init__(self, bot: discord.Client, rcon_client: RCONClient, staff_embed_service: StaffEmbedService):
        """
        Инициализировать команду.
        
        Args:
            bot: Экземпляр Discord бота
            rcon_client: RCON клиент
            staff_embed_service: Сервис для обновления Embed
        """
        self.bot = bot
        self.rcon_client = rcon_client
        self.staff_embed_service = staff_embed_service
        self.config = get_config()
        self.high_staff_roles = self.config['discord']['high_staff_roles']
        self.privilege_groups = self.config['privileges']['groups']
        self.command_channel_id = self.config['discord'].get('command_channel_id')
    
    def _check_high_staff(self, member: discord.Member) -> bool:
        """
        Проверить, имеет ли участник роль High Staff.
        
        Args:
            member: Участник Discord
            
        Returns:
            True если имеет роль High Staff, False иначе
        """
        member_role_ids = [role.id for role in member.roles]
        return any(role_id in member_role_ids for role_id in self.high_staff_roles)
    
    def _get_discord_role_by_privilege(self, guild: discord.Guild, privilege_group: str) -> Optional[discord.Role]:
        """
        Получить Discord роль по названию группы привилегии.
        
        Args:
            guild: Discord сервер
            privilege_group: Название группы привилегии
            
        Returns:
            discord.Role или None
        """
        # Ищем роль в конфигурации admin_roles по названию
        for role_config in self.config['discord']['admin_roles']:
            role_name = role_config['name'].lower()
            # Простое сопоставление (можно улучшить)
            if privilege_group.lower() in role_name or role_name in privilege_group.lower():
                role_id = role_config['role_id']
                return guild.get_role(role_id)
        
        return None
    
    async def _notify_user(self, user: discord.User, message: str, guild: discord.Guild) -> bool:
        """
        Уведомить пользователя (в ЛС или в канале).
        
        Args:
            user: Пользователь для уведомления
            message: Сообщение
            guild: Discord сервер
            
        Returns:
            True если уведомление отправлено, False иначе
        """
        try:
            # Пытаемся отправить в ЛС
            await user.send(message)
            return True
        except discord.Forbidden:
            # ЛС недоступно, отправляем в канал команды
            if self.command_channel_id:
                channel = guild.get_channel(self.command_channel_id)
                if channel:
                    try:
                        await channel.send(f"{user.mention} {message}")
                        return True
                    except Exception as e:
                        logger.error(f"Ошибка при отправке сообщения в канал: {e}")
        
        return False
    
    def register_commands(self, tree: app_commands.CommandTree):
        """
        Зарегистрировать команды в дереве команд.
        
        Args:
            tree: Дерево команд Discord
        """
        
        @tree.command(name="addprivilege", description="Добавить/обновить привилегию пользователя")
        @app_commands.describe(
            user="Discord пользователь",
            steam_id="SteamID пользователя"
        )
        async def addprivilege_command(
            interaction: discord.Interaction,
            user: discord.User,
            steam_id: str
        ):
            """Команда /addprivilege @DiscordUser SteamID"""
            await interaction.response.defer(ephemeral=True)
            
            try:
                guild = interaction.guild
                if guild is None:
                    await interaction.followup.send("❌ Команда доступна только на сервере", ephemeral=True)
                    return
                
                member = guild.get_member(interaction.user.id)
                if member is None:
                    await interaction.followup.send("❌ Не удалось найти вас на сервере", ephemeral=True)
                    return
                
                # Проверка прав доступа
                if not self._check_high_staff(member):
                    await interaction.followup.send(
                        "❌ У вас нет прав для выполнения этой команды",
                        ephemeral=True
                    )
                    return
                
                # Валидация SteamID
                if not validate_steam_id(steam_id):
                    await interaction.followup.send(
                        "❌ Неверный формат SteamID",
                        ephemeral=True
                    )
                    return
                
                # Проверка наличия пользователя на сервере
                target_member = guild.get_member(user.id)
                if target_member is None:
                    await interaction.followup.send(
                        f"❌ Пользователь {user.mention} не найден на сервере",
                        ephemeral=True
                    )
                    return
                
                # Выполняем RCON команду pinfo
                rcon_config = self.config.get('rcon', {})
                timeout = rcon_config.get('timeout', 10)
                retry_attempts = rcon_config.get('retry_attempts', 3)
                
                pinfo_response = self.rcon_client.get_player_info(steam_id, timeout, retry_attempts)
                
                if pinfo_response is None:
                    logger.error(f"RCON ошибка при выполнении pinfo для SteamID {steam_id}")
                    await interaction.followup.send(
                        "⚠️ Не удалось получить информацию с сервера. Попробуйте позже.",
                        ephemeral=True
                    )
                    return
                
                # Парсим ответ
                parsed_info = parse_pinfo_response(pinfo_response, self.privilege_groups)
                
                if parsed_info is None:
                    logger.error(f"Не удалось распарсить ответ pinfo: {pinfo_response}")
                    await interaction.followup.send(
                        "⚠️ Не удалось обработать ответ сервера. Попробуйте позже.",
                        ephemeral=True
                    )
                    return
                
                # Если привилегии нет
                if not parsed_info['has_privilege']:
                    await interaction.followup.send(
                        f"ℹ️ У игрока {steam_id} нет привилегий на сервере",
                        ephemeral=True
                    )
                    return
                
                # Получаем данные из парсера
                privilege_group = parsed_info['group']
                expires_at = parsed_info['expires_at']
                
                # Работа с БД
                db = get_db_session()
                try:
                    # Ищем существующую запись
                    user_privilege = db.query(UserPrivilege).filter_by(steam_id=steam_id).first()
                    
                    # Проверяем, изменились ли данные
                    data_changed = False
                    
                    if user_privilege is None:
                        # Новая запись
                        user_privilege = UserPrivilege(
                            discord_user_id=user.id,
                            steam_id=steam_id,
                            privilege_group=privilege_group,
                            expires_at=expires_at
                        )
                        db.add(user_privilege)
                        data_changed = True
                        logger.info(f"ACTION: Создана новая запись привилегии для {steam_id}")
                    else:
                        # Проверяем изменения
                        if user_privilege.privilege_group != privilege_group:
                            data_changed = True
                            user_privilege.privilege_group = privilege_group
                        
                        if user_privilege.expires_at != expires_at:
                            data_changed = True
                            user_privilege.expires_at = expires_at
                        
                        if user_privilege.discord_user_id != user.id:
                            data_changed = True
                            user_privilege.discord_user_id = user.id
                        
                        if data_changed:
                            user_privilege.updated_at = datetime.utcnow()
                            logger.info(f"ACTION: Обновлена запись привилегии для {steam_id}")
                        else:
                            logger.info(f"ACTION: Данные не изменились для {steam_id}, обновление не требуется")
                    
                    if not data_changed:
                        # Данные не изменились - ничего не делаем
                        await interaction.followup.send(
                            "✅ Информация проверена. Изменений не обнаружено.",
                            ephemeral=True
                        )
                        db.commit()
                        return
                    
                    # Сохраняем изменения
                    db.commit()
                    
                    # Выдаём/обновляем Discord роль
                    discord_role = self._get_discord_role_by_privilege(guild, privilege_group)
                    if discord_role:
                        try:
                            # Удаляем старые роли администрации
                            for role_config in self.config['discord']['admin_roles']:
                                old_role = guild.get_role(role_config['role_id'])
                                if old_role and old_role in target_member.roles:
                                    await target_member.remove_roles(old_role, reason="Обновление привилегии")
                            
                            # Выдаём новую роль
                            if discord_role not in target_member.roles:
                                await target_member.add_roles(discord_role, reason="Выдача привилегии")
                        except discord.Forbidden:
                            logger.error(f"Бот не имеет прав для выдачи ролей")
                        except Exception as e:
                            logger.error(f"Ошибка при выдаче роли: {e}")
                    
                    # Обновляем Embed /staff
                    await self.staff_embed_service.update_staff_message(guild)
                    
                    # Формируем сообщение для пользователя
                    expires_str = "бессрочно"
                    if expires_at:
                        expires_str = format_datetime_utc3(expires_at)
                    
                    notification_message = (
                        f"✅ Ваша привилегия обновлена!\n"
                        f"**Группа:** {privilege_group}\n"
                        f"**Истекает:** {expires_str}"
                    )
                    
                    # Уведомляем пользователя
                    await self._notify_user(user, notification_message, guild)
                    
                    await interaction.followup.send(
                        f"✅ Привилегия успешно обновлена для {user.mention}",
                        ephemeral=True
                    )
                    
                except Exception as e:
                    logger.error(f"Ошибка при работе с БД: {e}", exc_info=True)
                    db.rollback()
                    await interaction.followup.send(
                        "❌ Ошибка при сохранении данных. Проверьте логи.",
                        ephemeral=True
                    )
                finally:
                    db.close()
                    
            except Exception as e:
                logger.error(f"Ошибка в команде /addprivilege: {e}", exc_info=True)
                await interaction.followup.send(
                    "❌ Произошла ошибка при выполнении команды",
                    ephemeral=True
                )

