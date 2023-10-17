import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "GRJOJ.settings")
django.setup()

from GRJOJAPP.models import Informations

def create_initial_informations():
    informations, created = Informations.objects.get_or_create(
        prise1="OFF",
        prise2="OFF",
        startplage1=None,
        endplage1=None,
        startplage2=None,
        endplage2=None
    )

if __name__ == "__main__":
    create_initial_informations()
