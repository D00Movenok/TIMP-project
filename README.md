# СТАВКИ 31337bet

## Установка

1. Установить Docker
https://docs.docker.com/engine/install/debian/

2. Установка docker-compose
https://docs.docker.com/compose/install/

3. Запуск проекта
```bash
sudo docker-compose up --build -d
```

4. Проверка, что все запустилось
```bash
sudo docker ps -a
```

После установки на 127.0.0.1:10005 должен работать сервис.

Для использования его в глобальной сети рекомендуется прокидывать доступ к сервису через reverse-proxy (nginx, apache2).
Исключая использование reverse-proxy, можно в `docker-compose.yml` заменить `"127.0.0.1:10005:5000"` на `"0.0.0.0:10005:5000"`, тогда порт `10005` будет доступен не только для локальных адресов.

## Настройка

1. В файлике `app/settings.py` установить пароль администратора и соль.
