"""
Django settings for config project.
"""

import os
from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

# -------------------------------------
# ⚙️ Configurações básicas
# -------------------------------------
SECRET_KEY = config("DJANGO_SECRET_KEY", default="django-insecure-ug!1qg^wmr4^#$!b6xygi$&y137@ww2l(knfd#a7+)sv_^-x1*")
DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = ["*"]

CSRF_TRUSTED_ORIGINS = [
    "https://sistema-gabarito-production.up.railway.app",
    "https://29e746f66a131c8b93b08e85021c83c0.r2.cloudflarestorage.com",
    "http://localhost:8000",
]

# -------------------------------------
# 🧩 Aplicativos
# -------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "django_filters",
    "exams",
    "storages",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# -------------------------------------
# 🗄️ Banco de dados
# -------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# -------------------------------------
# ☁️ Cloudflare R2 Storage
# -------------------------------------
AWS_ACCESS_KEY_ID = config("R2_ACCESS_KEY_ID", default=None)
AWS_SECRET_ACCESS_KEY = config("R2_SECRET_ACCESS_KEY", default=None)
AWS_STORAGE_BUCKET_NAME = config("R2_BUCKET_NAME", default=None)
AWS_S3_ENDPOINT_URL = config("R2_ENDPOINT_URL", default=None)
AWS_S3_REGION_NAME = config("R2_REGION_NAME", default="auto")
AWS_S3_SIGNATURE_VERSION = "s3v4"
AWS_DEFAULT_ACL = None
AWS_QUERYSTRING_AUTH = False

# -------------------------------------
# 📁 Arquivos estáticos e de mídia
# -------------------------------------
# if DEBUG:
#     # Ambiente local
#     STATIC_URL = "/static/"
#     STATIC_ROOT = BASE_DIR / "staticfiles"
#     MEDIA_URL = "/media/"
#     MEDIA_ROOT = BASE_DIR / "media"
# else:
# Produção (Railway + Cloudflare R2)
STATIC_URL = f"{AWS_S3_ENDPOINT_URL}/{AWS_STORAGE_BUCKET_NAME}/static/"
MEDIA_URL = f"{AWS_S3_ENDPOINT_URL}/{AWS_STORAGE_BUCKET_NAME}/media/"

STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
        "OPTIONS": {
            "access_key": AWS_ACCESS_KEY_ID,
            "secret_key": AWS_SECRET_ACCESS_KEY,
            "bucket_name": AWS_STORAGE_BUCKET_NAME,
            "endpoint_url": AWS_S3_ENDPOINT_URL,
        },
    },
    "staticfiles": {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
        "OPTIONS": {
            "access_key": AWS_ACCESS_KEY_ID,
            "secret_key": AWS_SECRET_ACCESS_KEY,
            "bucket_name": AWS_STORAGE_BUCKET_NAME,
            "endpoint_url": AWS_S3_ENDPOINT_URL,
            "location": "static",
        },
    },
}

# -------------------------------------
# 🔐 Validação de senha
# -------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# -------------------------------------
# 🌍 Internacionalização
# -------------------------------------
LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

# -------------------------------------
# ⚙️ Outras configurações
# -------------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

REST_FRAMEWORK = {
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
}

OPENAI_API_KEY = config("OPENAI_API_KEY", default="")
