import os
import django
from django.contrib.auth import get_user_model

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sensores_project.settings")
django.setup()

User = get_user_model()

def create_admin():
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )
        print("Usuário admin criado com sucesso!")
    else:
        print("Usuário admin já existe.")

if __name__ == "__main__":
    create_admin()