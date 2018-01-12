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

from RISparser import readris, TAG_KEY_MAPPING
from publications.models import Publication


# Load a csv file with the bibliography (exported from Zotero).
with open('publications/data/test.txt', 'r') as f:
    results = list(readris(f, mapping=TAG_KEY_MAPPING))

for result in results:
    title = result.get('title', '')
    abstract = result.get('abstract', '')
    authors = result.get('authors', '')
    year = result.get('year', '')
    journal = result.get('secondary_title', '')
    volume = result.get('volume', '')
    issue = result.get('number', '')
    start_page = result.get('start_page', '')
    end_page = result.get('end_page', '')
    doi = result.get('doi', '')
    url = result.get('url', '')

    if start_page != '' and end_page != '':
        pages = '{start_page}-{end_page}'.format(start_page=start_page, end_page=end_page)
    else:
        pages = start_page

    # Check that the data do not exceed the maximum lengths in the database. They should not, except in the case of errors in the data (or metadata in the same field). If the length is exceeded, delete the excess.
    if len(title) > 510:
        title = title[0:510]
    if len(str(year)) > 30:
        year = year[0:30]
    if len(journal) > 510:
        journal = journal[0:510]
    if len(str(issue)) > 30:
        issue = issue[0:30]
    if len(str(volume)) > 30:
        volume = volume[0:30]
    if len(pages) > 30:
        pages = pages[0:30]
    if len(doi) > 510:
        doi = ''  # A broken DOI will not work.
    if len(url) > 510:
        doi = ''  # A broken URL will not work.

    record = Publication(
        title=title,
        abstract=abstract,
        authors=authors,
        year=year,
        journal=journal,
        volume=volume,
        issue=issue,
        pages=pages,
        doi=doi,
        url=url
    )
    record.save()
