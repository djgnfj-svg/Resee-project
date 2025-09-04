# Generated migration for enhanced billing system

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0012_add_auto_renewal_fields'),
    ]

    operations = [
        # Add new fields to Subscription
        migrations.AddField(
            model_name='subscription',
            name='billing_cycle',
            field=models.CharField(choices=[('monthly', '월간'), ('yearly', '연간')], default='monthly', help_text='Billing cycle frequency', max_length=20),
        ),
        migrations.AddField(
            model_name='subscription',
            name='next_billing_amount',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Next billing amount', max_digits=10, null=True),
        ),
        
        # Modify payment_method field in Subscription
        migrations.AlterField(
            model_name='subscription',
            name='payment_method',
            field=models.CharField(blank=True, default='', help_text='Payment method identifier (e.g., CARD-1234)', max_length=100),
        ),
        
        # Add new fields to PaymentHistory
        migrations.AddField(
            model_name='paymenthistory',
            name='refund_amount',
            field=models.DecimalField(decimal_places=2, default=0, help_text='Refund amount for downgrades', max_digits=10),
        ),
        migrations.AddField(
            model_name='paymenthistory',
            name='billing_cycle',
            field=models.CharField(choices=[('monthly', '월간'), ('yearly', '연간')], default='monthly', help_text='Billing cycle for this payment', max_length=20),
        ),
        migrations.AddField(
            model_name='paymenthistory',
            name='payment_method_used',
            field=models.CharField(blank=True, help_text='Payment method used for this transaction', max_length=100),
        ),
        migrations.AddField(
            model_name='paymenthistory',
            name='notes',
            field=models.TextField(blank=True, help_text='Internal notes about the transaction'),
        ),
        
        # Add REFUND to PaymentType choices
        migrations.AlterField(
            model_name='paymenthistory',
            name='payment_type',
            field=models.CharField(choices=[('upgrade', '업그레이드'), ('downgrade', '다운그레이드'), ('cancellation', '구독 취소'), ('renewal', '갱신'), ('initial', '최초 구독'), ('refund', '환불')], help_text='Type of payment or subscription change', max_length=20),
        ),
        
        # Create BillingSchedule model
        migrations.CreateModel(
            name='BillingSchedule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('scheduled_date', models.DateTimeField(help_text='Date when billing should occur')),
                ('amount', models.DecimalField(decimal_places=2, help_text='Amount to be billed', max_digits=10)),
                ('billing_cycle', models.CharField(choices=[('monthly', '월간'), ('yearly', '연간')], help_text='Billing cycle for this schedule', max_length=20)),
                ('status', models.CharField(choices=[('pending', '대기'), ('completed', '완료'), ('failed', '실패'), ('cancelled', '취소'), ('prepaid', '선불')], default='pending', help_text='Status of this billing schedule', max_length=20)),
                ('tier_at_billing', models.CharField(choices=[('free', 'Free (3일)'), ('basic', 'Basic (90일)'), ('pro', 'Pro (180일)')], help_text='Subscription tier when billing occurs', max_length=20)),
                ('payment_method', models.CharField(blank=True, help_text='Payment method to use for billing', max_length=100)),
                ('notes', models.TextField(blank=True, help_text='Additional notes about this billing schedule')),
                ('processed_at', models.DateTimeField(blank=True, help_text='When this billing was processed', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('subscription', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='billing_schedules', to='accounts.subscription')),
            ],
            options={
                'verbose_name': 'Billing Schedule',
                'verbose_name_plural': 'Billing Schedules',
                'db_table': 'accounts_billing_schedule',
                'ordering': ['scheduled_date'],
            },
        ),
        
        # Add indexes for BillingSchedule
        migrations.AddIndex(
            model_name='billingschedule',
            index=models.Index(fields=['subscription', 'scheduled_date'], name='accounts_bi_subscri_1b5e0e_idx'),
        ),
        migrations.AddIndex(
            model_name='billingschedule',
            index=models.Index(fields=['status', 'scheduled_date'], name='accounts_bi_status_9f2d3c_idx'),
        ),
    ]