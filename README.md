# Cоциальная сеть Yatube

### Технологии проекта:

* проект написан на Python с использованием веб-фреймворка Django.
* система управления версиями - git
* база данных - SQLite3
* работа с изображениями - sorl-thumbnail, pillow

### Как запустить проект:

* Клонировать репозиторий и перейти в него в командной строке:

```
git clone https://github.com/iliakoll/project_Yatube.git
```

```
cd api_final_yatube
```

* Cоздать и активировать виртуальное окружение:

```
python3 -m venv env
```

```
source env/bin/activate
```

* Установить зависимости из файла requirements.txt:

```
python3 -m pip install --upgrade pip
```

```
pip install -r requirements.txt
```

* Создайте в директории файл .env и поместите туда SECRET_KEY, необходимый для запуска проекта:

  Cгенерировать ключ можно на сайте [Djecrety](https://djecrety.ir)

* Выполнить миграции:

```
python3 manage.py migrate
```

* Создайте суперпользователя:

```
python manage.py createsuperuser
```

* Запустить проект:

```
python3 manage.py runserver
```
