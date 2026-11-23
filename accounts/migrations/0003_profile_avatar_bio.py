from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="avatar",
            field=models.ImageField(blank=True, upload_to="avatars/", verbose_name="Фото профілю"),
        ),
        migrations.AlterField(
            model_name="profile",
            name="bio",
            field=models.CharField(blank=True, help_text="Короткий опис, до 300 символів", max_length=300, verbose_name="Про себе"),
        ),
    ]
