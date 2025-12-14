# Настройка бота на Pterodactyl

## Настройка Startup Command

### Вариант 1: Автоматическое клонирование из Git (рекомендуется)

Эта команда автоматически клонирует репозиторий при первом запуске и обновляет его при последующих запусках:

```
cd /home/container && if [[ ! -d .git ]] || [[ ! -f bot.py ]]; then echo "Клонирование репозитория..."; rm -rf * .[^.]* 2>/dev/null || true; git clone https://github.com/JeremyFirst/Ds-Bot-2.0.git .; fi && if [[ -d .git ]] && [[ "${AUTO_UPDATE}" == "1" ]]; then git pull; fi && if [[ -f requirements.txt ]]; then pip install -U --prefix .local -r requirements.txt; fi && /usr/local/bin/python bot.py
```

**⚠️ ВАЖНО:** Копируйте команду БЕЗ обратных кавычек (```) в начале и конце! Вставляйте только саму команду в поле Startup Command.

**Что делает команда:**
1. Переходит в `/home/container`
2. Если нет `.git` или `bot.py` - клонирует репозиторий
3. Если `AUTO_UPDATE=1` - обновляет код через `git pull`
4. Устанавливает зависимости из `requirements.txt`
5. Запускает бота

### Вариант 2: Без автообновления

Если не хотите использовать автообновление:

```
cd /home/container && if [[ ! -d .git ]] || [[ ! -f bot.py ]]; then echo "Клонирование репозитория..."; rm -rf * .[^.]* 2>/dev/null || true; git clone https://github.com/JeremyFirst/Ds-Bot-2.0.git .; fi && if [[ -f requirements.txt ]]; then pip install -U --prefix .local -r requirements.txt; fi && /usr/local/bin/python bot.py
```

**⚠️ ВАЖНО:** Копируйте команду БЕЗ обратных кавычек (```) в начале и конце!

### Вариант 3: Прямая команда (если файлы уже загружены)

Если файлы уже загружены вручную через File Manager:

```
cd /home/container && pip install -U --prefix .local -r requirements.txt && /usr/local/bin/python bot.py
```

**⚠️ ВАЖНО:** Копируйте команду БЕЗ обратных кавычек (```) в начале и конце!

### Отладка: Проверка наличия файлов

Если бот не запускается, используйте эту команду для проверки:

```bash
cd /home/container && echo "=== Содержимое директории ===" && ls -la && echo "=== Поиск bot.py ===" && find . -name "bot.py" && echo "=== Поиск requirements.txt ===" && find . -name "requirements.txt"
```

## Переменные окружения

В разделе **Variables** создайте следующие переменные:

| Variable Name | Default Value | Description | Обязательно |
|--------------|---------------|-------------|-------------|
| `DISCORD_BOT_TOKEN` | (пусто) | Токен Discord-бота | ✅ Да |
| `DB_HOST` | `localhost` | Хост MySQL | ✅ Да |
| `DB_PORT` | `3306` | Порт MySQL | ✅ Да |
| `DB_USER` | (пусто) | Пользователь MySQL | ✅ Да |
| `DB_PASSWORD` | (пусто) | Пароль MySQL | ✅ Да |
| `DB_NAME` | `admin_log_db` | Название базы данных | ✅ Да |
| `RCON_HOST` | `localhost` | Хост RCON | ✅ Да |
| `RCON_PORT` | `28016` | Порт RCON | ✅ Да |
| `RCON_PASSWORD` | (пусто) | Пароль RCON | ✅ Да |
| `AUTO_UPDATE` | `1` | Автообновление из Git (0/1) | ❌ Нет |

**Важно:** Все переменные с пометкой "Да" должны быть заполнены перед запуском бота.

## Загрузка файлов

Убедитесь, что все файлы проекта загружены в `/home/container/`:

### Обязательные файлы:
- `bot.py`
- `requirements.txt`
- `config.yml`
- Все папки: `commands/`, `services/`, `database/`, `config/`, `utils/`

### Структура должна быть:
```
/home/container/
├── bot.py
├── requirements.txt
├── config.yml
├── commands/
│   ├── __init__.py
│   ├── staff.py
│   └── addprivilege.py
├── services/
│   ├── __init__.py
│   ├── rcon.py
│   └── staff_embed.py
├── database/
│   ├── __init__.py
│   ├── connection.py
│   └── models.py
├── config/
│   ├── __init__.py
│   └── config_loader.py
└── utils/
    ├── __init__.py
    ├── steam.py
    ├── timezone.py
    └── pinfo_parser.py
```

## Настройка Egg

1. **Egg**: Python 3.x
2. **Docker Image**: `ghcr.io/pterodactyl/yolks:python_3.11` (или другая версия Python 3.8+)
3. **Startup Command**: Используйте команду выше

## Проверка перед запуском

1. ✅ Все файлы загружены
2. ✅ `config.yml` настроен (ID каналов, ролей)
3. ✅ Переменные окружения заполнены
4. ✅ База данных MySQL создана и доступна
5. ✅ RCON доступен с указанными параметрами

## Решение проблем

### Ошибка: "can't open file '/home/container/bot.py'"

**Причины:**
1. Файлы не загружены в контейнер
2. Файлы находятся в подпапке
3. Неправильная рабочая директория

**Решение:**
1. **Проверьте загрузку файлов:**
   - В панели Pterodactyl перейдите в **File Manager**
   - Убедитесь, что `bot.py` находится в `/home/container/`
   - Если файлы в подпапке, переместите их в корень

2. **Используйте команду с `cd`:**
   ```bash
   cd /home/container && /usr/local/bin/python bot.py
   ```

3. **Проверьте структуру файлов:**
   ```bash
   cd /home/container && ls -la
   ```
   Должны быть видны: `bot.py`, `requirements.txt`, `config.yml` и папки проекта

4. **Если файлы в подпапке:**
   - Найдите путь к файлу: `find /home/container -name "bot.py"`
   - Используйте полный путь в команде запуска

### Ошибка: "You must give at least one requirement to install"
- Убедитесь, что `requirements.txt` существует и содержит зависимости
- Проверьте путь к файлу в команде запуска

### Ошибка: "ModuleNotFoundError"
- Убедитесь, что все папки проекта загружены
- Проверьте, что все `__init__.py` файлы на месте

### Ошибка подключения к MySQL
- Проверьте переменные окружения `DB_*`
- Убедитесь, что MySQL доступен из контейнера
- Проверьте, что база данных создана

## Логи

Логи бота сохраняются в файл `bot.log` в корне контейнера. Также можно просматривать логи через панель Pterodactyl в разделе **Console**.

