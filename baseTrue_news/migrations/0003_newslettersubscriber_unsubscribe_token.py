import uuid

from django.db import migrations, models


def populate_unsubscribe_tokens(apps, schema_editor):
    NewsletterSubscriber = apps.get_model("baseTrue_news", "NewsletterSubscriber")
    for subscriber in NewsletterSubscriber.objects.filter(unsubscribe_token__isnull=True):
        subscriber.unsubscribe_token = uuid.uuid4()
        subscriber.save(update_fields=["unsubscribe_token"])


class Migration(migrations.Migration):

    dependencies = [
        ("baseTrue_news", "0002_newslettersubscriber"),
    ]

    operations = [
        migrations.AddField(
            model_name="newslettersubscriber",
            name="unsubscribe_token",
            field=models.UUIDField(null=True, editable=False),
        ),
        migrations.RunPython(populate_unsubscribe_tokens, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="newslettersubscriber",
            name="unsubscribe_token",
            field=models.UUIDField(default=uuid.uuid4, unique=True, editable=False),
        ),
    ]
