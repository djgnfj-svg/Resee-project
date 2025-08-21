# Generated migration for business intelligence app

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('content', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='SystemUsageMetrics',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(db_index=True, unique=True)),
                ('total_users', models.IntegerField(default=0)),
                ('active_users_daily', models.IntegerField(default=0)),
                ('new_users', models.IntegerField(default=0)),
                ('churned_users', models.IntegerField(default=0)),
                ('free_users', models.IntegerField(default=0)),
                ('basic_users', models.IntegerField(default=0)),
                ('pro_users', models.IntegerField(default=0)),
                ('subscription_revenue_usd', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('total_content_created', models.IntegerField(default=0)),
                ('total_reviews_completed', models.IntegerField(default=0)),
                ('average_success_rate', models.FloatField(default=0.0)),
                ('ai_questions_generated', models.IntegerField(default=0)),
                ('ai_cost_usd', models.DecimalField(decimal_places=4, default=0.0, max_digits=8)),
                ('ai_tokens_used', models.BigIntegerField(default=0)),
                ('average_api_response_time_ms', models.IntegerField(default=0)),
                ('error_rate_percentage', models.FloatField(default=0.0)),
                ('uptime_percentage', models.FloatField(default=100.0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'bi_system_usage_metrics',
                'ordering': ['-date'],
            },
        ),
        migrations.CreateModel(
            name='SubscriptionAnalytics',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subscription_tier', models.CharField(choices=[('FREE', 'Free'), ('BASIC', 'Basic'), ('PRO', 'Pro')], default='FREE', max_length=20)),
                ('tier_start_date', models.DateTimeField()),
                ('tier_end_date', models.DateTimeField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('total_content_created', models.IntegerField(default=0)),
                ('total_reviews_completed', models.IntegerField(default=0)),
                ('total_ai_questions_used', models.IntegerField(default=0)),
                ('total_session_time_hours', models.FloatField(default=0.0)),
                ('days_active', models.IntegerField(default=0, help_text='Number of days user was active')),
                ('average_daily_reviews', models.FloatField(default=0.0)),
                ('feature_adoption_score', models.FloatField(default=0.0, help_text='Percentage of features used (0-100)', validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(100.0)])),
                ('upgrade_probability', models.FloatField(default=0.0, help_text='ML-calculated upgrade probability (0-100)', validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(100.0)])),
                ('churn_risk_score', models.FloatField(default=0.0, help_text='Risk of subscription cancellation (0-100)', validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(100.0)])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subscription_analytics', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'bi_subscription_analytics',
                'ordering': ['-tier_start_date'],
            },
        ),
        migrations.CreateModel(
            name='LearningPattern',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(db_index=True)),
                ('contents_created', models.IntegerField(default=0, help_text='Contents created today')),
                ('reviews_completed', models.IntegerField(default=0, help_text='Reviews completed today')),
                ('ai_questions_generated', models.IntegerField(default=0, help_text='AI questions generated today')),
                ('session_duration_minutes', models.IntegerField(default=0, help_text='Total session time in minutes')),
                ('success_rate', models.FloatField(default=0.0, help_text='Daily success rate percentage', validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(100.0)])),
                ('average_review_time_seconds', models.IntegerField(default=0, help_text='Average time spent per review in seconds')),
                ('peak_activity_hour', models.IntegerField(blank=True, help_text='Hour of day with most activity (0-23)', null=True, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(23)])),
                ('login_count', models.IntegerField(default=0, help_text='Number of logins today')),
                ('consecutive_days', models.IntegerField(default=0, help_text='Current learning streak')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='learning_patterns', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'bi_learning_pattern',
                'ordering': ['-date'],
            },
        ),
        migrations.CreateModel(
            name='ContentEffectiveness',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('total_reviews', models.IntegerField(default=0)),
                ('successful_reviews', models.IntegerField(default=0)),
                ('average_difficulty_rating', models.FloatField(default=0.0, help_text='User-rated difficulty (1-5 scale)', validators=[django.core.validators.MinValueValidator(1.0), django.core.validators.MaxValueValidator(5.0)])),
                ('average_review_time_seconds', models.IntegerField(default=0)),
                ('time_to_master_days', models.IntegerField(blank=True, help_text='Days taken to consistently remember (3 successful reviews in a row)', null=True)),
                ('ai_questions_generated', models.IntegerField(default=0)),
                ('ai_questions_success_rate', models.FloatField(default=0.0, validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(100.0)])),
                ('last_reviewed', models.DateTimeField(blank=True, null=True)),
                ('abandonment_risk_score', models.FloatField(default=0.0, help_text='Risk score for content abandonment (0-100)', validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(100.0)])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('content', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='effectiveness_stats', to='content.content')),
            ],
            options={
                'db_table': 'bi_content_effectiveness',
            },
        ),
        migrations.AddIndex(
            model_name='subscriptionanalytics',
            index=models.Index(fields=['user', 'tier_start_date'], name='bi_subscrip_user_id_8d1e9a_idx'),
        ),
        migrations.AddIndex(
            model_name='subscriptionanalytics',
            index=models.Index(fields=['subscription_tier', 'is_active'], name='bi_subscrip_subscri_dc6a19_idx'),
        ),
        migrations.AddIndex(
            model_name='subscriptionanalytics',
            index=models.Index(fields=['upgrade_probability'], name='bi_subscrip_upgrade_af5e87_idx'),
        ),
        migrations.AddIndex(
            model_name='subscriptionanalytics',
            index=models.Index(fields=['churn_risk_score'], name='bi_subscrip_churn_r_b0a2c1_idx'),
        ),
        migrations.AddIndex(
            model_name='learningpattern',
            index=models.Index(fields=['user', 'date'], name='bi_learning_user_id_3d7f5e_idx'),
        ),
        migrations.AddIndex(
            model_name='learningpattern',
            index=models.Index(fields=['date', 'success_rate'], name='bi_learning_date_25a6b7_idx'),
        ),
        migrations.AddIndex(
            model_name='learningpattern',
            index=models.Index(fields=['consecutive_days'], name='bi_learning_consecu_8c4f1a_idx'),
        ),
        migrations.AddIndex(
            model_name='contenteffectiveness',
            index=models.Index(fields=['average_difficulty_rating'], name='bi_content__average_9d8e3b_idx'),
        ),
        migrations.AddIndex(
            model_name='contenteffectiveness',
            index=models.Index(fields=['abandonment_risk_score'], name='bi_content__abandon_7f2a5c_idx'),
        ),
        migrations.AddIndex(
            model_name='contenteffectiveness',
            index=models.Index(fields=['time_to_master_days'], name='bi_content__time_to_1e6d9f_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='learningpattern',
            unique_together={('user', 'date')},
        ),
    ]