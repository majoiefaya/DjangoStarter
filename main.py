import os
import subprocess
from datetime import timedelta
from pathlib import Path
import re

def run_command(command):
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Erreur: {result.stderr}")
    else:
        print(result.stdout)

def create_django_project(project_name):
    print(f"Création du projet Django: {project_name}")
    run_command(f"django-admin startproject {project_name}")
    update_settings(project_name)
    update_middleware(project_name)
    update_installed_apps(project_name)
    update_urls(project_name)
    create_utils_and_assets(project_name)

def create_django_app(project_name, app_name):
    print(f"Création de l'application Django: {app_name}")
    os.chdir(project_name)
    run_command(f"python manage.py startapp {app_name}")
    os.chdir("..")
    create_app_structure(project_name, app_name)
    update_app_urls(project_name, app_name)

def create_app_structure(project_name, app_name):
    print(f"Configuration de la structure de l'application: {app_name}")
    base_path = os.path.join(project_name, app_name)
    app_directories = ['models', 'views', 'serializers', 'services', 'filters', 'templates', 'tests']
    for directory in app_directories:
        dir_path = os.path.join(base_path, directory)
        os.makedirs(dir_path, exist_ok=True)
        open(os.path.join(dir_path, '__init__.py'), 'w').close()

    # Création du fichier urls.py
    with open(os.path.join(base_path, 'urls.py'), 'w') as f:
        f.write("""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

app_name = "{}"
router = DefaultRouter()

# Ajouter vos viewsets ici
# Exemple: router.register(r'example', ExampleViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
""".format(app_name))

def create_model(app_name, model_name):
    model_content = f"""
from django.db import models

class {model_name}(models.Model):
    # Ajouter vos champs ici
    pass
"""
    with open(os.path.join(app_name, 'models', f'{model_name.lower()}.py'), 'w') as f:
        f.write(model_content)

def create_serializer(app_name, serializer_name):
    serializer_content = f"""
from rest_framework import serializers
from .models import {serializer_name}

class {serializer_name}Serializer(serializers.ModelSerializer):
    class Meta:
        model = {serializer_name}
        fields = '__all__'
"""
    with open(os.path.join(app_name, 'serializers', f'{serializer_name.lower()}_serializer.py'), 'w') as f:
        f.write(serializer_content)

def create_view(app_name, view_name):
    view_content = f"""
from rest_framework import viewsets
from .models import {view_name}
from .serializers import {view_name}Serializer

class {view_name}ViewSet(viewsets.ModelViewSet):
    queryset = {view_name}.objects.all()
    serializer_class = {view_name}Serializer
"""
    with open(os.path.join(app_name, 'views', f'{view_name.lower()}_view.py'), 'w') as f:
        f.write(view_content)

def update_app_urls(project_name, app_name):
    views_path = os.path.join(project_name, app_name, 'views')
    urls_path = os.path.join(project_name, app_name, 'urls.py')
    
    viewset_imports = []
    router_registers = []

    for view_file in os.listdir(views_path):
        if view_file.endswith('_view.py'):
            viewset_name = view_file.replace('_view.py', 'ViewSet')
            viewset_imports.append(f'from .{view_file.replace(".py", "")} import {viewset_name}')
            router_registers.append(f"router.register(r'{view_file.replace('_view.py', '')}', {viewset_name})")

    with open(urls_path, 'r') as f:
        content = f.read()

    if viewset_imports:
        imports_str = '\n'.join(viewset_imports)
        registers_str = '\n'.join(router_registers)
        content = content.replace("# Ajouter vos viewsets ici", f"{imports_str}\n\n# Ajouter vos viewsets ici\n{registers_str}")

    with open(urls_path, 'w') as f:
        f.write(content)

    # Mise à jour du fichier urls.py principal pour inclure les URLs de l'application
    main_urls_path = os.path.join(project_name, project_name, 'urls.py')
    with open(main_urls_path, 'r') as f:
        main_content = f.read()

    app_url_pattern = f"path('api/{app_name}/', include('{app_name}.urls')),"
    if app_url_pattern not in main_content:
        main_content = main_content.replace("urlpatterns = [", f"urlpatterns = [\n    {app_url_pattern}")

    with open(main_urls_path, 'w') as f:
        f.write(main_content)

def update_settings(project_name):
    settings_path = os.path.join(project_name, project_name, 'settings.py')
    with open(settings_path, 'r') as f:
        content = f.read()

    # Suppression des lignes DEBUG et ALLOWED_HOSTS
    content = re.sub(r'DEBUG = True\n', '', content)
    content = re.sub(r'ALLOWED_HOSTS = \[\]\n', '', content)

    with open(settings_path, 'w') as f:
        f.write(content)

    with open(settings_path, 'a') as f:
        f.write("""
import os
from pathlib import Path
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent
MEDIA_URL = '/assets/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'assets')

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
}

SIMPLE_JWT = {
    'USER_ID_FIELD': 'pk',
    'AUTH_HEADER_TYPES': ('JWT',),
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=7),
    'SLIDING_TOKEN_LIFETIME': timedelta(days=30),
    'SLIDING_TOKEN_REFRESH_LIFETIME_SLIDING': timedelta(days=7),
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'ROTATE_REFRESH_TOKENS': False,
    'SLIDING_TOKEN_REFRESH_IMMUTABLE': False,
    'SLIDING_TOKEN_REFRESH_EACH_TIME': True,
    'SLIDING_TOKEN_LIFETIME_ZERO_REFRESH': False,
    'SLIDING_TOKEN_REFRESH_VALIDITY_LEEWAY': 0,
    'SLIDING_TOKEN_INACTIVE_REFRESH_LIFETIME': timedelta(days=7),
    'SLIDING_TOKEN_FIRST_USE_SLACK': timedelta(seconds=0),
    'SLIDING_TOKEN_USE_SLACK': timedelta(seconds=0),
}

CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_HEADERS = [
    'Authorization',
    'Content-Type',
]

STATIC_URL = 'static/'
ALLOWED_HOSTS = ['10.0.2.2', 'localhost', '127.0.0.1']
""")

def update_middleware(project_name):
    settings_path = os.path.join(project_name, project_name, 'settings.py')
    with open(settings_path, 'r') as f:
        content = f.read()

    middleware_settings = """\
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'appUsers.middleware.CurrentUserMiddleware',
"""

    if 'MIDDLEWARE = [' in content:
        content = re.sub(r'MIDDLEWARE = \[.*?\]', f'MIDDLEWARE = [\n{middleware_settings}]', content, flags=re.DOTALL)

    with open(settings_path, 'w') as f:
        f.write(content)

def update_installed_apps(project_name):
    settings_path = os.path.join(project_name, project_name, 'settings.py')
    with open(settings_path, 'r') as f:
        content = f.read()

    installed_apps = """\
    'rest_framework',
    'corsheaders',
    'rest_framework.authtoken',
    'rest_framework_swagger',
    'drf_yasg',
"""

    if 'INSTALLED_APPS = [' in content:
        content = content.replace('INSTALLED_APPS = [', f'INSTALLED_APPS = [\n{installed_apps}', 1)

    with open(settings_path, 'w') as f:
        f.write(content)

def update_urls(project_name):
    urls_path = os.path.join(project_name, project_name, 'urls.py')
    with open(urls_path, 'w') as f:
        f.write("""\
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from utils.swagger_utils import schema_view

urlpatterns = [
    path('docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'), # swagger url
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
""")

def create_utils_and_assets(project_name):
    os.makedirs(os.path.join(project_name, 'utils'), exist_ok=True)
    os.makedirs(os.path.join(project_name, 'assets'), exist_ok=True)

    pagination_utils = """\
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

class CustomPageNumberPagination(PageNumberPagination):
    def get_paginated_response(self, data):
        return Response({
            'links': {
                'next': self.get_next_link(),
                'previous': self.get_previous_link()
            },
            'total_pages': self.page.paginator.num_pages,
            'count': self.page.paginator.count,
            'page_size': self.page_size,
            'results': data
        })
"""

    swagger_utils = f"""\
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="{project_name} PROJECT",
        default_version='v1',
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)
"""

    with open(os.path.join(project_name, 'utils', 'pagination_utils.py'), 'w') as f:
        f.write(pagination_utils)

    with open(os.path.join(project_name, 'utils', 'swagger_utils.py'), 'w') as f:
        f.write(swagger_utils)

def main():
    project_name = input("Entrez le nom du projet Django: ")
    create_django_project(project_name)

    apps = input("Entrez les noms des applications séparés par des virgules: ").split(',')

    for app in apps:
        app_name = app.strip()
        create_django_app(project_name, app_name)

        models = input(f"Entrez les noms des modèles pour l'application {app_name}, séparés par des virgules: ").split(',')
        for model in models:
            model_name = model.strip()
            create_model(os.path.join(project_name, app_name), model_name)

        serializers = input(f"Entrez les noms des serializers pour l'application {app_name}, séparés par des virgules: ").split(',')
        for serializer in serializers:
            serializer_name = serializer.strip()
            create_serializer(os.path.join(project_name, app_name), serializer_name)

        views = input(f"Entrez les noms des views pour l'application {app_name}, séparés par des virgules: ").split(',')
        for view in views:
            view_name = view.strip()
            create_view(os.path.join(project_name, app_name), view_name)

        update_app_urls(project_name, app_name)

    # Installation des dépendances
    dependencies = [
        "djangorestframework",
        "markdown",
        "django-filter",
        "django-cors-headers",
        "djangorestframework_simplejwt",
        "django-rest-swagger",
        "drf-yasg",
    ]

    for dependency in dependencies:
        run_command(f"pip install {dependency}")

if __name__ == "__main__":
    main()
