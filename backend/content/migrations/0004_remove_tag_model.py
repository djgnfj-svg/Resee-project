# Generated migration to remove Tag model and related fields

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0003_category_user_alter_category_name_and_more'),
    ]

    operations = [
        # Remove tags field from Content model
        migrations.RemoveField(
            model_name='content',
            name='tags',
        ),
        # Delete Tag model
        migrations.DeleteModel(
            name='Tag',
        ),
    ]