import os
import sys
from django.core.management.base import BaseCommand


ENV_PREFIX = "WAGTAIL_INIT_SUPERUSER_"


class InitSuperuserConfig():
    def __init__(self):
        self.username = os.environ[f"{ENV_PREFIX}USERNAME"]
        self.password = os.environ[f"{ENV_PREFIX}PASSWORD"]
        self.email = os.environ[f"{ENV_PREFIX}EMAIL"]
        self.first_name = os.environ[f"{ENV_PREFIX}FIRST_NAME"]
        self.last_name = os.environ[f"{ENV_PREFIX}LAST_NAME"]



class Command(BaseCommand):
    help = "Ensures a superuser exists with the given credentials."

    def handle(self, *args, **options):
        from django.contrib.auth.models import User
        from django.db import transaction
        from django.db.utils import IntegrityError
        from django.core.exceptions import ObjectDoesNotExist

        config = InitSuperuserConfig()

        with transaction.atomic():
            try:
                changes = False
                user = User.objects.get(username=config.username)
                if not user.check_password(config.password):
                    user.set_password(config.password)
                    changes = True
                if user.email != config.email:
                    user.email = config.email
                    changes = True
                if user.first_name != config.first_name:
                    user.first_name = config.first_name
                    changes = True
                if user.last_name != config.last_name:
                    user.last_name = config.last_name
                    changes = True
                if changes:
                    user.save()
                    self.stderr.write(self.style.SUCCESS("Superuser updated."))
                else:
                    self.stderr.write(self.style.SUCCESS("Superuser already exists and does not need to be updated."))
            except ObjectDoesNotExist:
                try:
                    User.objects.create_superuser(
                        username=config.username,
                        password=config.password,
                        email=config.email,
                        first_name=config.first_name,
                        last_name=config.last_name,
                    )
                    # No need to save, create_superuser does that.
                    self.stderr.write(self.style.SUCCESS("Superuser created."))
                except IntegrityError:
                    self.stderr.write(self.style.ERROR("Superuser already exists and we tried to create it again."))
                    sys.exit(1)
