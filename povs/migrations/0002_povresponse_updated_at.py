from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('povs', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='povresponse',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
