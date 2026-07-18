from django.conf import settings
from django.db import migrations


ADMIN_EMAIL = 'martymcmillan22@gmail.com'


def forwards(apps, schema_editor):
    story_session_model = apps.get_model('storytelling_dashboard', 'StorySession')
    user_app_label, user_model_name = settings.AUTH_USER_MODEL.split('.')
    user_model = apps.get_model(user_app_label, user_model_name)

    from storytelling_dashboard.markdown_parser import StoryMarkdownParser

    admin_user = user_model.objects.filter(email=ADMIN_EMAIL).first()
    if admin_user is None:
        return

    for story in StoryMarkdownParser.load_all_stories():
        story_session_model.objects.update_or_create(
            entry_id=story.entry_id,
            defaults={
                'title': story.title,
                'status': story.status,
                'format': story.format,
                'progress': story.calculate_progress(),
                'owner': admin_user,
                'last_edited_by': admin_user,
            },
        )


def backwards(apps, schema_editor):
    story_session_model = apps.get_model('storytelling_dashboard', 'StorySession')
    story_session_model.objects.filter(owner__email=ADMIN_EMAIL).update(owner=None)


class Migration(migrations.Migration):

    dependencies = [
        ('storytelling_dashboard', '0004_backfill_storysession_owner'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]