# Generated by Django 2.0 on 2019-04-18 13:07

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('publications', '0035_auto_20190418_1257'),
    ]

    operations = [
        migrations.RenameField(
            model_name='date',
            old_name='day',
            new_name='start_day',
        ),
        migrations.RenameField(
            model_name='date',
            old_name='month',
            new_name='start_month',
        ),
        migrations.RenameField(
            model_name='date',
            old_name='year',
            new_name='start_year',
        ),
        migrations.AddField(
            model_name='date',
            name='end_day',
            field=models.IntegerField(blank=True, choices=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8), (9, 9), (10, 10), (11, 11), (12, 12), (13, 13), (14, 14), (15, 15), (16, 16), (17, 17), (18, 18), (19, 19), (20, 20), (21, 21), (22, 22), (23, 23), (24, 24), (25, 25), (26, 26), (27, 27), (28, 28), (29, 29), (30, 30), (31, 31)], null=True),
        ),
        migrations.AddField(
            model_name='date',
            name='end_month',
            field=models.IntegerField(blank=True, choices=[(1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'), (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'), (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')], null=True),
        ),
        migrations.AddField(
            model_name='date',
            name='end_year',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='date',
            name='experiment',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='dates_experiment', to='publications.Experiment'),
        ),
        migrations.AddField(
            model_name='date',
            name='experiment_index',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='dates_experiment_index', to='publications.Experiment'),
        ),
        migrations.AddField(
            model_name='date',
            name='outcome',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='dates_outcome', to='publications.ExperimentPopulationOutcome'),
        ),
        migrations.AddField(
            model_name='date',
            name='outcome_index',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='dates_outcome_index', to='publications.ExperimentPopulationOutcome'),
        ),
        migrations.AddField(
            model_name='date',
            name='population',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='dates_population', to='publications.ExperimentPopulation'),
        ),
        migrations.AddField(
            model_name='date',
            name='population_index',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='dates_population_index', to='publications.ExperimentPopulation'),
        ),
        migrations.AddField(
            model_name='date',
            name='publication_index',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='dates_publication_index', to='publications.Publication'),
        ),
        migrations.AlterField(
            model_name='date',
            name='publication',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='dates_publication', to='publications.Publication'),
        ),
    ]