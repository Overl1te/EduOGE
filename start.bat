@echo off
setlocal EnableDelayedExpansion

REM ============================
REM LOAD .env
REM ============================
if not exist .env (
    echo .env not found
    exit /b 1
)

for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
    set "%%A=%%B"
)

REM ============================
REM VENV
REM ============================
if not exist venv\Scripts\python.exe (
    py -3 -m venv venv
)

call venv\Scripts\activate

REM ============================
REM MIGRATIONS
REM ============================
python manage.py migrate
if errorlevel 1 exit /b 1

REM ============================
REM CREATE SUPERUSER
REM ============================
python manage.py shell -c "import os; from django.contrib.auth import get_user_model; User=get_user_model(); u=os.environ['DJANGO_SUPERUSER_USERNAME']; p=os.environ['DJANGO_SUPERUSER_PASSWORD']; e=os.environ.get('DJANGO_SUPERUSER_EMAIL',''); User.objects.filter(username=u).exists() or User.objects.create_superuser(u,e,p)"

if errorlevel 1 (
    echo superuser failed
    exit /b 1
)

REM ============================
REM CREATE EXERCISE TYPE
REM ============================
python manage.py shell -c "from EduOGE.models import ExerciseType; ExerciseType.objects.get_or_create(code=16, defaults={'title':'Программирование','description':'Напишите программу ...','is_active':True,'sort_order':100})"

if errorlevel 1 (
    echo exercisetype failed
    exit /b 1
)

REM ============================
REM RUN
REM ============================
python manage.py runserver
