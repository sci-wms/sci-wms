from django.core.management.base import BaseCommand, CommandError
import pywms.grid_init_script as grid_cache

class Command(BaseCommand):
    args = '<dataset_id dataset_id ...>'
    help = 'Updates the cache for specific datasets'
    
    def handle(self, *args, **options):
        grid_cache.do(args)
