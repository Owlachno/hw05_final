# **Yatube**
___ 

## *Описание проекта*

Проект Yatube - социальная сеть-блог.

Зарегистрированный пользователь может публиковать посты, подписываться на других пользователей, оставлять комментарии к постам.
___

### *Технологии*
- Python 3.7
- Django
- SQLite
___

## Установка

Cоздать и активировать виртуальное окружение:
```sh
python -m venv env

source venv/scripts/activate
```

Установить зависимости из файла requirements.txt:
```sh
pip install -r requirements.txt
```
Выполнить миграции:
```sh
python manage.py migrate
```
Запустить проект:
```sh
python manage.py runserver
```
** Для установки на Linux и MacOs использовать команды python3 и source env/bin/activate
___

## *Дополнительная информация*

К проекту написаны Unittest

Запуск тестов:

```sh
python manage.py test
```
