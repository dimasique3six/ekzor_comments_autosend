#!/bin/bash
# Скрипт установки Ekzor Comments AutoSend Bot

set -e

echo "====================================="
echo "Установка Ekzor Comments AutoSend Bot"
echo "====================================="
echo ""

# Проверка прав root
if [ "$EUID" -ne 0 ]; then 
    echo "Пожалуйста, запустите скрипт с правами root (sudo)"
    exit 1
fi

# Устанавливаем необходимые пакеты
echo "Шаг 1: Установка необходимых пакетов..."
apt-get update
apt-get install -y python3 python3-pip python3-venv

# Создаем пользователя для бота
echo "Шаг 2: Создание пользователя telegram-bot..."
if ! id "telegram-bot" &>/dev/null; then
    useradd -r -s /bin/false telegram-bot
    echo "Пользователь telegram-bot создан"
else
    echo "Пользователь telegram-bot уже существует"
fi

# Создаем директорию для бота
echo "Шаг 3: Создание директории /opt/ekzor_comments_autosend..."
mkdir -p /opt/ekzor_comments_autosend
cd /opt/ekzor_comments_autosend

# Копируем файлы (предполагается, что они находятся в текущей директории)
echo "Шаг 4: Копирование файлов бота..."
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
if [ -f "$SCRIPT_DIR/ekzor_comments_autosend.py" ]; then
    cp "$SCRIPT_DIR/ekzor_comments_autosend.py" /opt/ekzor_comments_autosend/
    cp "$SCRIPT_DIR/requirements.txt" /opt/ekzor_comments_autosend/
    cp "$SCRIPT_DIR/.env.example" /opt/ekzor_comments_autosend/
    echo "Файлы скопированы из $SCRIPT_DIR"
else
    echo "ОШИБКА: Файлы бота не найдены в директории $SCRIPT_DIR"
    echo "Пожалуйста, запустите скрипт из директории с файлами бота"
    exit 1
fi

# Создаем виртуальное окружение
echo "Шаг 5: Создание виртуального окружения Python..."
python3 -m venv /opt/ekzor_comments_autosend/venv

# Устанавливаем зависимости
echo "Шаг 6: Установка зависимостей..."
/opt/ekzor_comments_autosend/venv/bin/pip install --upgrade pip
/opt/ekzor_comments_autosend/venv/bin/pip install -r /opt/ekzor_comments_autosend/requirements.txt

# Создаем директорию для логов
echo "Шаг 7: Создание директории для логов..."
mkdir -p /var/log
touch /var/log/ekzor_comments_autosend.log
chown telegram-bot:telegram-bot /var/log/ekzor_comments_autosend.log

# Устанавливаем права
echo "Шаг 8: Настройка прав доступа..."
chown -R telegram-bot:telegram-bot /opt/ekzor_comments_autosend
chmod +x /opt/ekzor_comments_autosend/ekzor_comments_autosend.py

# Создаем файл конфигурации
echo "Шаг 9: Создание файла конфигурации..."
if [ ! -f /opt/ekzor_comments_autosend/.env ]; then
    cp /opt/ekzor_comments_autosend/.env.example /opt/ekzor_comments_autosend/.env
    echo "Создан файл .env - НЕОБХОДИМО ЗАПОЛНИТЬ ЕГО СВОИМИ ДАННЫМИ!"
else
    echo "Файл .env уже существует, пропускаем"
fi

# Обновляем путь к Python в скрипте бота
echo "Шаг 10: Обновление пути к Python..."
sed -i '1s|.*|#!/opt/ekzor_comments_autosend/venv/bin/python3|' /opt/ekzor_comments_autosend/ekzor_comments_autosend.py

# Устанавливаем systemd service
echo "Шаг 11: Установка systemd service..."
if [ -f "$SCRIPT_DIR/ekzor_comments_autosend.service" ]; then
    # Обновляем пути в service файле
    cp "$SCRIPT_DIR/ekzor_comments_autosend.service" /tmp/ekzor_comments_autosend.service
    sed -i "s|ExecStart=/usr/bin/python3|ExecStart=/opt/ekzor_comments_autosend/venv/bin/python3|" /tmp/ekzor_comments_autosend.service
    cp /tmp/ekzor_comments_autosend.service /etc/systemd/system/
    rm /tmp/ekzor_comments_autosend.service
    systemctl daemon-reload
    echo "Service установлен"
else
    echo "ПРЕДУПРЕЖДЕНИЕ: файл ekzor_comments_autosend.service не найден в $SCRIPT_DIR"
fi

echo ""
echo "====================================="
echo "Установка завершена!"
echo "====================================="
echo ""
echo "СЛЕДУЮЩИЕ ШАГИ:"
echo ""
echo "1. Отредактируйте конфигурацию:"
echo "   nano /opt/ekzor_comments_autosend/.env"
echo ""
echo "2. Поместите картинку для комментариев:"
echo "   cp your_image.jpg /opt/ekzor_comments_autosend/image.jpg"
echo ""
echo "3. Запустите бота:"
echo "   systemctl start ekzor_comments_autosend"
echo ""
echo "4. Добавьте в автозагрузку:"
echo "   systemctl enable ekzor_comments_autosend"
echo ""
echo "5. Проверьте статус:"
echo "   systemctl status ekzor_comments_autosend"
echo ""
echo "6. Просмотр логов:"
echo "   journalctl -u ekzor_comments_autosend -f"
echo "   или"
echo "   tail -f /var/log/ekzor_comments_autosend.log"
echo ""
