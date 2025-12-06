import os
from pathlib import Path
import dj_database_url
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-change-me-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True  # Set to True for development

ALLOWED_HOSTS = ["healthcarepatientinformationsystem.onrender.com", "localhost", "127.0.0.1"]  # Update this in production

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'main',  # Your app
    'records',
    'inventory',
    'inventory_meds',
    'widget_tweaks',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.cache.UpdateCacheMiddleware',  # Cache middleware (must be first)
    'django.middleware.common.CommonMiddleware',
    'django.middleware.cache.FetchFromCacheMiddleware',  # Cache middleware (must be last)
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'hpis.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'main' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'hpis.wsgi.application'

# Database
# Configure to use Supabase PostgreSQL via Session Pooler
DATABASES = {
    'default': dj_database_url.config(
        default=os.getenv(
            'DATABASE_URL',
            'sqlite:///db.sqlite3'  # Fallback to SQLite if DATABASE_URL not set
        ),
        conn_max_age=600,  # Connection pooling: keep alive for 10 minutes
        conn_health_checks=True,  # Check connection health
    )
}

# SSL Configuration for Supabase
if os.getenv('DATABASE_URL'):
    DATABASES['default']['OPTIONS'] = {
        'sslmode': 'require',
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    # {
    #     'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    # },
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

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

# ================================================
# FIX for Authentication Redirects (404 Error) 
# ================================================

# This tells the @login_required decorator and other auth views 
# where to find your custom login view ('user_login' is the name 
# defined in your main/urls.py).
LOGIN_URL = 'user_login'

# This tells Django where to redirect after a successful login (optional, but clean).
LOGIN_REDIRECT_URL = 'homepage'

# ================================================
# Cache Configuration
# ================================================
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'hpis-cache',
        'TIMEOUT': 300,  # 5 minutes default timeout
        'OPTIONS': {
            'MAX_ENTRIES': 1000
        }
    }
}

# Cache time for pages
CACHE_MIDDLEWARE_ALIAS = 'default'
CACHE_MIDDLEWARE_SECONDS = 60  # Cache pages for 60 seconds
CACHE_MIDDLEWARE_KEY_PREFIX = 'hpis'

# Session optimization
SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'
SESSION_CACHE_ALIAS = 'default'
