from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("mess", "0002_monthcycle_email_sent_at"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="monthcycle",
            name="email_sent_at",
        ),
    ]