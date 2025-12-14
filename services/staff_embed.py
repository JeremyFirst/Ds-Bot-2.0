"""
Сервис для создания и обновления Embed сообщения /staff.
"""

import logging
from typing import List, Optional
import discord
from config.config_loader import get_config
from database.models import StaffMessage, UserPrivilege
from database.connection import get_db_session

logger = logging.getLogger(__name__)


class StaffEmbedService:
    """
    Сервис для управления Embed сообщением /staff.
    """
    
    def __init__(self, bot: discord.Client):
        """
        Инициализировать сервис.
        
        Args:
            bot: Экземпляр Discord бота
        """
        self.bot = bot
        self.config = get_config()
        self.admin_roles = self.config['discord']['admin_roles']
        self.staff_channel_id = self.config['discord']['staff_channel_id']
    
    def _get_staff_members(self, guild: discord.Guild) -> dict:
        """
        Получить список администраторов по ролям.
        
        Args:
            guild: Discord сервер
            
        Returns:
            Dict с ключами role_id и списками участников
        """
        staff_dict = {}
        
        for role_config in self.admin_roles:
            role_id = role_config['role_id']
            role = guild.get_role(role_id)
            
            if role is None:
                logger.warning(f"Роль {role_id} не найдена на сервере")
                continue
            
            # Получаем всех участников с этой ролью
            members = [member for member in guild.members if role in member.roles]
            staff_dict[role_id] = {
                'role_name': role_config['name'],
                'members': sorted(members, key=lambda m: m.display_name.lower())
            }
        
        return staff_dict
    
    def create_embed(self, guild: discord.Guild) -> discord.Embed:
        """
        Создать Embed сообщение со списком администрации.
        
        Args:
            guild: Discord сервер
            
        Returns:
            discord.Embed с информацией об администрации
        """
        staff_dict = self._get_staff_members(guild)
        
        embed = discord.Embed(
            title="📋 Список администрации",
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow()
        )
        
        # Сортируем роли по приоритету (от высших к низшим)
        sorted_roles = sorted(
            self.admin_roles,
            key=lambda x: x['priority'],
            reverse=True
        )
        
        for role_config in sorted_roles:
            role_id = role_config['role_id']
            role_name = role_config['name']
            
            if role_id not in staff_dict:
                continue
            
            members = staff_dict[role_id]['members']
            
            if not members:
                value = "*Нет участников*"
            else:
                # Формируем список участников
                member_list = []
                for member in members:
                    status_emoji = "🟢" if member.status == discord.Status.online else \
                                  "🟡" if member.status == discord.Status.idle else \
                                  "🔴" if member.status == discord.Status.dnd else "⚪"
                    member_list.append(f"{status_emoji} {member.mention}")
                
                value = "\n".join(member_list)
                if len(value) > 1024:  # Ограничение Discord для поля Embed
                    value = value[:1021] + "..."
            
            embed.add_field(
                name=f"**{role_name}**",
                value=value,
                inline=False
            )
        
        embed.set_footer(text="Обновляется автоматически при изменении ролей")
        
        return embed
    
    async def get_or_create_staff_message(self, guild: discord.Guild) -> Optional[discord.Message]:
        """
        Получить существующее сообщение /staff или создать новое.
        
        Args:
            guild: Discord сервер
            
        Returns:
            discord.Message или None при ошибке
        """
        channel = guild.get_channel(self.staff_channel_id)
        if channel is None:
            logger.error(f"Канал {self.staff_channel_id} не найден")
            return None
        
        db = get_db_session()
        try:
            staff_msg_record = db.query(StaffMessage).filter_by(channel_id=self.staff_channel_id).first()
            
            if staff_msg_record:
                # Пытаемся получить существующее сообщение
                try:
                    message = await channel.fetch_message(staff_msg_record.message_id)
                    return message
                except discord.NotFound:
                    # Сообщение удалено, создаём новое
                    logger.info("Сообщение /staff удалено, создаём новое")
                    db.delete(staff_msg_record)
                    db.commit()
            
            # Создаём новое сообщение
            embed = self.create_embed(guild)
            message = await channel.send(embed=embed)
            
            # Сохраняем в БД
            staff_msg_record = StaffMessage(
                channel_id=self.staff_channel_id,
                message_id=message.id
            )
            db.add(staff_msg_record)
            db.commit()
            
            return message
            
        except Exception as e:
            logger.error(f"Ошибка при получении/создании сообщения /staff: {e}")
            db.rollback()
            return None
        finally:
            db.close()
    
    async def update_staff_message(self, guild: discord.Guild) -> bool:
        """
        Обновить Embed сообщение /staff.
        
        Args:
            guild: Discord сервер
            
        Returns:
            True если обновление успешно, False иначе
        """
        message = await self.get_or_create_staff_message(guild)
        if message is None:
            return False
        
        try:
            embed = self.create_embed(guild)
            await message.edit(embed=embed)
            return True
        except Exception as e:
            logger.error(f"Ошибка при обновлении сообщения /staff: {e}")
            return False

