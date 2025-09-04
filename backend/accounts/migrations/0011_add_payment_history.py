# Generated manually
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0010_alter_subscription_max_interval_days_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='PaymentHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('payment_type', models.CharField(choices=[('upgrade', '업그레이드'), ('downgrade', '다운그레이드'), ('cancellation', '구독 취소'), ('renewal', '갱신'), ('initial', '최초 구독')], help_text='Type of payment or subscription change', max_length=20)),
                ('from_tier', models.CharField(blank=True, choices=[('free', 'Free (3일)'), ('basic', 'Basic (90일)'), ('pro', 'Pro (180일)')], help_text='Previous subscription tier', max_length=20, null=True)),
                ('to_tier', models.CharField(choices=[('free', 'Free (3일)'), ('basic', 'Basic (90일)'), ('pro', 'Pro (180일)')], help_text='New subscription tier', max_length=20)),
                ('amount', models.DecimalField(decimal_places=2, default=0, help_text='Payment amount (0 for free tier)', max_digits=10)),
                ('description', models.TextField(blank=True, help_text='Additional details about the payment')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='Transaction date and time')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payment_history', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Payment History',
                'verbose_name_plural': 'Payment Histories',
                'db_table': 'accounts_payment_history',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='paymenthistory',
            index=models.Index(fields=['user', '-created_at'], name='accounts_pa_user_id_677502_idx'),
        ),
    ]