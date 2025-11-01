import logging
import os
import sys
from pathlib import Path

import django
from django.contrib.auth import get_user_model

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sensores_project.settings")
django.setup()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)
User = get_user_model()


def create_admin():
    """Cria ou atualiza usuário administrador."""
    username = os.environ.get("DJANGO_SUPERUSER_USERNAME")
    email = os.environ.get("DJANGO_SUPERUSER_EMAIL")
    password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")

    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(username=username, email=email, password=password)
        logger.info("Usuário admin criado com sucesso!")
    else:
        user = User.objects.get(username=username)
        user.set_password(password)
        user.save()
        logger.info("Senha do usuário admin atualizada com sucesso!")


if __name__ == "__main__":
    create_admin()
