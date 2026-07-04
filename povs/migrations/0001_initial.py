import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ExpoFact',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('content', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_by', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='expo_facts',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': 'Expository Fact Set',
                'verbose_name_plural': 'Expository Fact Sets',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='POVResponse',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_person', models.TextField(blank=True)),
                ('first_person_at', models.DateTimeField(blank=True, null=True)),
                ('prediction', models.TextField(blank=True)),
                ('prediction_at', models.DateTimeField(blank=True, null=True)),
                ('narrative', models.TextField(blank=True)),
                ('narrative_at', models.DateTimeField(blank=True, null=True)),
                ('probable_outcome', models.TextField(blank=True)),
                ('probable_outcome_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expo_fact', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='responses',
                    to='povs.expofact',
                )),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='pov_responses',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AlterUniqueTogether(
            name='povresponse',
            unique_together={('user', 'expo_fact')},
        ),
    ]
