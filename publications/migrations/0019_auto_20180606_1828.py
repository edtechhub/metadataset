# Generated by Django 2.0 on 2018-06-06 18:28

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('publications', '0018_assessmentstatus_relevant_assessments'),
    ]

    operations = [
        migrations.RenameField(
            model_name='assessmentstatus',
            old_name='relevant_assessments',
            new_name='relevant_publications',
        ),
    ]