# Run this script as a "standalone" script (terminology from the Django
# documentation) that uses the Djano ORM to get data from the database.
# This requires django.setup(), which requires the settings for this project.
# Appending the root directory to the system path also prevents errors when
# importing the models from the app.
if __name__ == '__main__':
    import sys
    import os
    import django
    parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__),
        os.path.pardir))
    sys.path.append(parent_dir)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "metadataset.settings")
    django.setup()


import pandas as pd
from publications.models import IUCNThreatLevel1, IUCNThreatLevel2

# Load a csv file with the list to be added to the database.
csv = "publications/data/threat2.csv"
df = pd.read_csv(csv, encoding="utf-8")

for result in df.itertuples():
    threat1 = result.Threat1
    threat1 = IUCNThreatLevel1.objects.get(threat=threat1)
    threat2 = result.Threat2
    record = IUCNThreatLevel2(threat=threat2, parent=threat1)
    record.save()