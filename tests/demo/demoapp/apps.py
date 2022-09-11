from django.contrib.admin.apps import AppConfig


class Config(AppConfig):
    name = "demoapp"

    def ready(self):
        from smart_admin.decorators import smart_register

        from django.contrib.auth.models import User, UserManager
        from django.db.models.signals import post_migrate

        from admin_sync.conf import config

        from .admin import SyncUserAdmin

        def uget_by_natural_key(self, username):
            return self.get(username=username)

        def unatural_key(self):
            return (self.username,)

        UserManager.get_by_natural_key = uget_by_natural_key
        User.natural_key = unatural_key

        smart_register(User)(SyncUserAdmin)

        if not config.REMOTE_SERVER:
            post_migrate.connect(create_sample_data, sender=self)


def create_sample_data(sender, **kwargs):
    from .factories import DetailFactory

    DetailFactory.create_batch(
        10,
        base__parent__parent=None,
        brother__brother=None,
        brother__base__parent=None,
    )
