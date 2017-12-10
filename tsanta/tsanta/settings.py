import os


APP_VERSION = '0.0.3'

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = '2unty@irwi_gg5=+k#y+45q8om=cbag&8=zwf0wfq&t=aoacmw'

DEBUG = True

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'api',
    'front',
    'panel',
    'rest_framework',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'tsanta.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'tsanta.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'tsanta_db',
        'HOST': '127.0.0.1',
        'PORT': 3306,
        'USER': 'tsanta',
        'PASSWORD': 'password'
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'ru-ru'

TIME_ZONE = 'Europe/Moscow'

USE_I18N = True

USE_L10N = True

USE_TZ = True

STATIC_URL = '/static/'

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    )
}

LOGIN_URL = '/panel/login'

API_DATETIME_FORMAT = '%d.%m.%Y %H:%M:%S'

# Количество ответов на вопросы, при котором вопрос можно удалить
QUESTION_DELETE_TRESHOLD = 0

# Те слова, которые не могут употреблять пользователи в своих slug
RESERVED_SLUG_WORDS = [
    'thanks',
    'confirm',
    'santa',
    'recipient',
    'ward',
    'panel',
    'admin']


DOMAIN_NAME = 't-santa.ru'
MAILGUN_SECRET_KEY = 'key'
MAILGUN_API_URL = 'https://api.mailgun.net/v3/'
MAILGUN_LIMIT = 100

MAIL_FROM = ('Тайный Санта', 'magician@t-santa.ru')
MAIL_REPLY_TO = 'schoolof.training.hse@gmail.com'

EMAILS_TEMPLATES_DIR = os.path.join(BASE_DIR, 'api', 'templates', 'emails')
