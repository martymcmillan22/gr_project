from django.conf import settings
from django.db import migrations


ADMIN_EMAIL = 'martymcmillan22@gmail.com'


def forwards(apps, schema_editor):
    story_session_model = apps.get_model('storytelling_dashboard', 'StorySession')
    user_app_label, user_model_name = settings.AUTH_USER_MODEL.split('.')
    user_model = apps.get_model(user_app_label, user_model_name)

    admin_user = user_model.objects.filter(email=ADMIN_EMAIL).first()
    if admin_user is None:
        return

    story_session_model.objects.update(owner=admin_user)


def backwards(apps, schema_editor):
    story_session_model = apps.get_model('storytelling_dashboard', 'StorySession')
    story_session_model.objects.update(owner=None)


class Migration(migrations.Migration):

    dependencies = [
        ('storytelling_dashboard', '0003_storysession_owner'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]