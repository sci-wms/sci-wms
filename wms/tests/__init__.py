import os

from django.conf import settings
from django.contrib.auth.models import User
import django.contrib.auth.hashers as hashpass
from django.db import IntegrityError

from wms.models import Group, Server, UGridDataset, SGridDataset, RGridDataset, UGridTideDataset

from sciwms import logger

resource_path = os.path.abspath(os.path.join(settings.PROJECT_ROOT, '..', 'wms', 'resources'))


def add_server():
    s = Server.objects.create()
    s.save()
    return s


def add_group():
    g, _ = Group.objects.get_or_create(name='MyTestGroup',)
    g.save()
    return g


def add_dataset(name, klass, filename):
    add_group()

    model_class = None
    if klass.lower() == 'ugrid':
        model_class = UGridDataset
    elif klass.lower() == 'sgrid':
        model_class = SGridDataset
    elif klass.lower() == 'rgrid':
        model_class = RGridDataset
    elif klass.lower() == 'ugrid_tides':
        model_class = UGridTideDataset

    d, _ = model_class.objects.get_or_create(uri                   = os.path.join(resource_path, filename),
                                             name                  = name,
                                             title                 = "Test dataset",
                                             abstract              = "Test data set for sci-wms tests.",
                                             display_all_timesteps = False,
                                             keep_up_to_date       = False)
    return d


def add_user():
    try:
        return User.objects.create(username="testuser",
                                   first_name="test",
                                   last_name="user",
                                   email="test@yser.comn",
                                   password=hashpass.make_password("test"),
                                   is_active=True,
                                   is_superuser=True)
    except IntegrityError:
        return User.objects.filter(username='testuser').first()


def image_path(*args):
    path = os.path.join(os.path.dirname(__file__), 'images', *args)
    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))
    return path
