# Generated by Django 2.0 on 2018-04-11 11:29

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('publications', '0008_auto_20180406_1546'),
    ]

    operations = [
        migrations.CreateModel(
            name='AssessmentStatus',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('assessment_order', models.TextField()),
                ('next_assessment', models.IntegerField(blank=True, null=True)),
                ('completed_assessments', models.TextField(blank=True)),
                ('subject', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='publications.Subject')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'assessment statuses',
            },
        ),
    ]