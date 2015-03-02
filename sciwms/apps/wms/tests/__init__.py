import os

from django.conf import settings
from django.contrib.auth.models import User
import django.contrib.auth.hashers as hashpass

from sciwms.apps.wms.models import Dataset, Group, Server

resource_path = os.path.join(settings.PROJECT_ROOT, 'apps', 'wms', 'resources')


def add_server():
    s = Server.objects.create()
    s.save()
    return s


def add_group():
    g = Group.objects.create(name='MyTestGroup',)
    g.save()
    return g


def add_dataset(filename):
    add_group()
    d = Dataset.objects.create(uri                   = os.path.join(resource_path, filename),
                               name                  = "test",
                               title                 = "Test dataset",
                               abstract              = "Test data set for sci-wms tests.",
                               display_all_timesteps = False,
                               keep_up_to_date       = False,)
    d.update_cache(force=True)
    d.save()
    return d


def add_user():
    u = User(username="testuser",
             first_name="test",
             last_name="user",
             email="test@yser.comn",
             password=hashpass.make_password("test"),
             is_active=True,
             is_superuser=True,
            )
    u.save()
    return u
