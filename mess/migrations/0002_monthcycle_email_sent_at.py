from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("mess", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="monthcycle",
            name="email_sent_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]