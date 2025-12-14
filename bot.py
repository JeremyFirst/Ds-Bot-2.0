"""
Главный файл Discord-бота для административной инфраструктуры Rust-сервера.
"""

import os
import logging
import asyncio
import discord
from discord import app_commands
from discord.ext import tasks
from dotenv import load_dotenv

from config.config_loader import load_config, get_config
from database.connection import init_database, get_db_session
from database.models import StaffMessage
from services.rcon import RCONClient
from services.staff_embed import StaffEmbedService
from commands.staff import StaffCommand
from commands.addprivilege import AddPrivilegeCommand

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Настройка Discord intents
intents = discord.Intents.default()
intents.members = True
intents.message_content = False

# Создаём клиент бота
bot = discord.Client(intents=intents)
# Создаём дерево команд
tree = app_commands.CommandTree(bot)

# Глобальные сервисы
rcon_client: RCONClient = None
staff_embed_service: StaffEmbedService = None
staff_command: StaffCommand = None
addprivilege_command: AddPrivilegeCommand = None


@bot.event
async def on_ready():
    """
    Обработчик события готовности бота.
    """
    logger.info(f'Бот {bot.user} подключён к Discord')
    
    # Синхронизируем команды
    try:
        synced = await tree.sync()
        logger.info(f'Синхронизировано {len(synced)} команд')
    except Exception as e:
        logger.error(f'Ошибка при синхронизации команд: {e}')
    
    # Проверяем и восстанавливаем сообщение /staff при перезапуске
    await check_and_restore_staff_message()
    
    # Запускаем задачу автообновления Embed
    if not update_staff_embed.is_running():
        update_staff_embed.start()
    
    logger.info('Бот готов к работе')


@bot.event
async def on_member_update(before: discord.Member, after: discord.Member):
    """
    Обработчик изменения участника (в т.ч. ролей).
    Автоматически обновляет Embed /staff при изменении ролей администрации.
    """
    # Проверяем, изменились ли роли
    if before.roles != after.roles:
        config = get_config()
        admin_role_ids = [role['role_id'] for role in config['discord']['admin_roles']]
        
        # Проверяем, затронуты ли роли администрации
        before_admin_roles = [r for r in before.roles if r.id in admin_role_ids]
        after_admin_roles = [r for r in after.roles if r.id in admin_role_ids]
        
        if before_admin_roles != after_admin_roles:
            logger.info(f"Изменены роли администрации у {after.display_name}, обновляю Embed /staff")
            if staff_embed_service:
                await staff_embed_service.update_staff_message(after.guild)


@bot.event
async def on_guild_role_update(before: discord.Role, after: discord.Role):
    """
    Обработчик обновления роли.
    Если обновлена роль администрации, обновляем Embed.
    """
    config = get_config()
    admin_role_ids = [role['role_id'] for role in config['discord']['admin_roles']]
    
    if before.id in admin_role_ids:
        logger.info(f"Обновлена роль администрации {after.name}, обновляю Embed /staff")
        if staff_embed_service:
            await staff_embed_service.update_staff_message(after.guild)


async def check_and_restore_staff_message():
    """
    Проверить существование сообщения /staff и восстановить при необходимости.
    Вызывается при перезапуске бота.
    """
    config = get_config()
    staff_channel_id = config['discord']['staff_channel_id']
    
    db = get_db_session()
    try:
        staff_msg_record = db.query(StaffMessage).filter_by(channel_id=staff_channel_id).first()
        
        if staff_msg_record:
            # Пытаемся получить сообщение
            try:
                channel = bot.get_channel(staff_channel_id)
                if channel:
                    try:
                        message = await channel.fetch_message(staff_msg_record.message_id)
                        logger.info(f"Сообщение /staff найдено: {message.id}")
                        return
                    except discord.NotFound:
                        # Сообщение удалено, пересоздадим при следующем обновлении
                        logger.info("Сообщение /staff удалено, будет пересоздано при следующем обновлении")
            except Exception as e:
                logger.error(f"Ошибка при проверке сообщения /staff: {e}")
    finally:
        db.close()


@tasks.loop(minutes=5)
async def update_staff_embed():
    """
    Периодическая задача для обновления Embed /staff.
    Проверяет существование сообщения и обновляет его.
    """
    if not bot.is_ready():
        return
    
    try:
        config = get_config()
        staff_channel_id = config['discord']['staff_channel_id']
        
        # Получаем все серверы, где бот активен
        for guild in bot.guilds:
            try:
                # Проверяем существование сообщения
                channel = guild.get_channel(staff_channel_id)
                if channel is None:
                    continue
                
                db = get_db_session()
                try:
                    staff_msg_record = db.query(StaffMessage).filter_by(channel_id=staff_channel_id).first()
                    
                    if staff_msg_record:
                        try:
                            # Проверяем существование сообщения
                            await channel.fetch_message(staff_msg_record.message_id)
                            # Сообщение существует, обновляем
                            if staff_embed_service:
                                await staff_embed_service.update_staff_message(guild)
                        except discord.NotFound:
                            # Сообщение удалено, пересоздаём
                            logger.info(f"Сообщение /staff удалено на сервере {guild.name}, пересоздаю")
                            if staff_embed_service:
                                await staff_embed_service.get_or_create_staff_message(guild)
                finally:
                    db.close()
                    
            except Exception as e:
                logger.error(f"Ошибка при обновлении Embed на сервере {guild.name}: {e}")
                
    except Exception as e:
        logger.error(f"Ошибка в задаче update_staff_embed: {e}")


def main():
    """
    Главная функция запуска бота.
    """
    # Загружаем конфигурацию
    try:
        load_config()
        logger.info('Конфигурация загружена')
    except Exception as e:
        logger.error(f'Ошибка при загрузке конфигурации: {e}')
        return
    
    # Инициализируем базу данных
    try:
        init_database()
        logger.info('База данных инициализирована')
    except Exception as e:
        logger.error(f'Ошибка при инициализации БД: {e}')
        return
    
    # Инициализируем сервисы
    global rcon_client, staff_embed_service, staff_command, addprivilege_command
    
    rcon_client = RCONClient()
    staff_embed_service = StaffEmbedService(bot)
    staff_command = StaffCommand(bot, staff_embed_service)
    addprivilege_command = AddPrivilegeCommand(bot, rcon_client, staff_embed_service)
    
    # Регистрируем команды
    staff_command.register_commands(tree)
    addprivilege_command.register_commands(tree)
    
    # Получаем токен бота
    token = os.getenv('DISCORD_BOT_TOKEN')
    if not token:
        logger.error('DISCORD_BOT_TOKEN не установлен в .env')
        return
    
    # Запускаем бота
    try:
        bot.run(token)
    except Exception as e:
        logger.error(f'Ошибка при запуске бота: {e}')


if __name__ == '__main__':
    main()

