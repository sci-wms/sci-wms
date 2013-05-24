from django.core.management.base import BaseCommand, CommandError
from pywms.wms.models import Dataset
import pywms.grid_init_script as grid_cache

class Command(BaseCommand):
    args = 'None'
    help = 'Updates the cache for sall datasets in the database'
    
    def handle(self, *args, **options):
        grid_cache.check_topology_age()
