# Generated manually for auto-renewal functionality
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0011_add_payment_history'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscription',
            name='auto_renewal',
            field=models.BooleanField(default=True, help_text='Whether to auto-renew subscription'),
        ),
        migrations.AddField(
            model_name='subscription',
            name='next_billing_date',
            field=models.DateTimeField(blank=True, help_text='Next automatic billing date', null=True),
        ),
        migrations.AddField(
            model_name='subscription',
            name='payment_method',
            field=models.CharField(blank=True, default='', help_text='Payment method identifier (e.g., card last 4 digits)', max_length=50),
        ),
    ]