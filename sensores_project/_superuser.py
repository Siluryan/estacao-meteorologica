import os
import django
from django.contrib.auth import get_user_model

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sensores_project.settings")
django.setup()

User = get_user_model()

def create_admin():
    username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
    email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
    password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
    
    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(
            username=username,
            email=email,
            password=password
        )
        print("Usuário admin criado com sucesso!")
    else:
        user = User.objects.get(username=username)
        user.set_password(password)
        user.save()
        print("Senha do usuário admin atualizada com sucesso!")

if __name__ == "__main__":
    create_admin()