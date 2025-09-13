"""
Django management command for database capacity management and cleanup
"""
import logging
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.utils import timezone
from django.contrib.auth import get_user_model

from accounts.models import AIUsageTracking, PaymentHistory
from review.models import ReviewHistory
from analytics.models import UserSession

User = get_user_model()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Manage database capacity by cleaning up old data and optimizing storage'

    def add_arguments(self, parser):
        parser.add_argument(
            '--cleanup-days',
            type=int,
            default=365,
            help='Clean up data older than N days (default: 365)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be cleaned without actually deleting'
        )
        parser.add_argument(
            '--vacuum',
            action='store_true',
            help='Run VACUUM ANALYZE on database tables'
        )
        parser.add_argument(
            '--analyze-size',
            action='store_true',
            help='Analyze database size and table statistics'
        )
        parser.add_argument(
            '--cleanup-logs',
            action='store_true',
            help='Clean up old log files'
        )

    def handle(self, *args, **options):
        self.cleanup_days = options['cleanup_days']
        self.dry_run = options['dry_run']

        if self.dry_run:
            self.stdout.write(self.style.WARNING('🔍 DRY RUN MODE - No changes will be made'))

        self.stdout.write(self.style.SUCCESS(f'Starting database capacity management...'))
        self.stdout.write(f'Cleanup threshold: {self.cleanup_days} days')

        if options['analyze_size']:
            self.analyze_database_size()

        if options['cleanup_logs']:
            self.cleanup_old_logs()

        self.cleanup_old_data()

        if options['vacuum']:
            self.vacuum_database()

        self.stdout.write(self.style.SUCCESS('✅ Database capacity management completed'))

    def analyze_database_size(self):
        """Analyze database size and table statistics"""
        self.stdout.write(self.style.SUCCESS('\n📊 Database Size Analysis'))
        self.stdout.write('=' * 50)

        with connection.cursor() as cursor:
            # Get database size
            cursor.execute("""
                SELECT pg_size_pretty(pg_database_size(current_database())) as db_size,
                       pg_database_size(current_database()) as db_size_bytes
            """)
            db_size, db_size_bytes = cursor.fetchone()
            self.stdout.write(f'Database Size: {db_size} ({db_size_bytes:,} bytes)')

            # Get table sizes
            cursor.execute("""
                SELECT schemaname, tablename,
                       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                       pg_total_relation_size(schemaname||'.'||tablename) as size_bytes,
                       pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as table_size,
                       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) -
                                     pg_relation_size(schemaname||'.'||tablename)) as index_size
                FROM pg_tables
                WHERE schemaname = 'public'
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                LIMIT 20
            """)

            self.stdout.write('\n📋 Largest Tables:')
            self.stdout.write('-' * 80)
            self.stdout.write(f'{"Table":<30} {"Total Size":<12} {"Table Size":<12} {"Index Size":<12}')
            self.stdout.write('-' * 80)

            for row in cursor.fetchall():
                table_name, size, size_bytes, table_size, index_size = row[1], row[2], row[3], row[4], row[5]
                self.stdout.write(f'{table_name:<30} {size:<12} {table_size:<12} {index_size:<12}')

            # Get index usage statistics
            cursor.execute("""
                SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
                FROM pg_stat_user_indexes
                WHERE idx_scan = 0
                ORDER BY pg_relation_size(indexrelid) DESC
                LIMIT 10
            """)

            unused_indexes = cursor.fetchall()
            if unused_indexes:
                self.stdout.write('\n⚠️  Unused Indexes (candidates for removal):')
                self.stdout.write('-' * 60)
                for row in unused_indexes:
                    self.stdout.write(f'{row[0]}.{row[1]}.{row[2]} - Never used')

            # Get row counts for main tables
            cursor.execute("""
                SELECT schemaname, tablename, n_tup_ins, n_tup_upd, n_tup_del, n_live_tup, n_dead_tup
                FROM pg_stat_user_tables
                WHERE schemaname = 'public'
                ORDER BY n_live_tup DESC
                LIMIT 15
            """)

            self.stdout.write('\n📊 Table Statistics:')
            self.stdout.write('-' * 90)
            self.stdout.write(f'{"Table":<25} {"Live Rows":<12} {"Dead Rows":<12} {"Inserts":<12} {"Updates":<12}')
            self.stdout.write('-' * 90)

            for row in cursor.fetchall():
                table_name, n_tup_ins, n_tup_upd, n_tup_del, n_live_tup, n_dead_tup = row[1], row[2], row[3], row[4], row[5], row[6]
                self.stdout.write(f'{table_name:<25} {n_live_tup:<12,} {n_dead_tup:<12,} {n_tup_ins:<12,} {n_tup_upd:<12,}')

    def cleanup_old_data(self):
        """Clean up old data based on retention policies"""
        self.stdout.write(self.style.SUCCESS('\n🧹 Cleaning up old data'))
        self.stdout.write('=' * 50)

        cutoff_date = timezone.now() - timedelta(days=self.cleanup_days)
        self.stdout.write(f'Cutoff date: {cutoff_date.strftime("%Y-%m-%d %H:%M:%S")}')

        total_cleaned = 0

        # Clean old AI usage tracking records (keep 6 months)
        ai_usage_cutoff = timezone.now() - timedelta(days=180)
        ai_usage_count = AIUsageTracking.objects.filter(date__lt=ai_usage_cutoff.date()).count()

        if ai_usage_count > 0:
            if not self.dry_run:
                deleted_count = AIUsageTracking.objects.filter(date__lt=ai_usage_cutoff.date()).delete()[0]
                self.stdout.write(f'✅ Deleted {deleted_count:,} old AI usage records')
                total_cleaned += deleted_count
            else:
                self.stdout.write(f'🔍 Would delete {ai_usage_count:,} old AI usage records')

        # Clean old review history (keep 2 years for analytics)
        review_cutoff = timezone.now() - timedelta(days=730)
        review_count = ReviewHistory.objects.filter(review_date__lt=review_cutoff).count()

        if review_count > 0:
            if not self.dry_run:
                # Delete in batches to avoid memory issues
                batch_size = 1000
                deleted_total = 0

                while True:
                    batch_ids = list(
                        ReviewHistory.objects.filter(review_date__lt=review_cutoff)
                        .values_list('id', flat=True)[:batch_size]
                    )

                    if not batch_ids:
                        break

                    deleted_count = ReviewHistory.objects.filter(id__in=batch_ids).delete()[0]
                    deleted_total += deleted_count

                    self.stdout.write(f'   Deleted batch: {deleted_count:,} review records')

                self.stdout.write(f'✅ Deleted {deleted_total:,} old review history records')
                total_cleaned += deleted_total
            else:
                self.stdout.write(f'🔍 Would delete {review_count:,} old review history records')

        # Clean old user sessions (keep 30 days)
        if hasattr(UserSession, 'objects'):
            session_cutoff = timezone.now() - timedelta(days=30)
            try:
                session_count = UserSession.objects.filter(created_at__lt=session_cutoff).count()

                if session_count > 0:
                    if not self.dry_run:
                        deleted_count = UserSession.objects.filter(created_at__lt=session_cutoff).delete()[0]
                        self.stdout.write(f'✅ Deleted {deleted_count:,} old session records')
                        total_cleaned += deleted_count
                    else:
                        self.stdout.write(f'🔍 Would delete {session_count:,} old session records')
            except:
                pass  # UserSession model might not exist

        # Clean up orphaned payment history (very old, unsuccessful payments)
        old_failed_payments = PaymentHistory.objects.filter(
            created_at__lt=cutoff_date,
            payment_type='failed'
        ).count()

        if old_failed_payments > 0:
            if not self.dry_run:
                deleted_count = PaymentHistory.objects.filter(
                    created_at__lt=cutoff_date,
                    payment_type='failed'
                ).delete()[0]
                self.stdout.write(f'✅ Deleted {deleted_count:,} old failed payment records')
                total_cleaned += deleted_count
            else:
                self.stdout.write(f'🔍 Would delete {old_failed_payments:,} old failed payment records')

        if not self.dry_run and total_cleaned > 0:
            self.stdout.write(f'\n📊 Total records cleaned: {total_cleaned:,}')

    def cleanup_old_logs(self):
        """Clean up old log files"""
        self.stdout.write(self.style.SUCCESS('\n📁 Cleaning up log files'))
        self.stdout.write('=' * 50)

        import os
        import glob
        from pathlib import Path

        log_dirs = ['/app/logs', '/backups/logs', '/var/log']
        cutoff_date = datetime.now() - timedelta(days=self.cleanup_days)
        total_files_cleaned = 0
        total_size_cleaned = 0

        for log_dir in log_dirs:
            if not os.path.exists(log_dir):
                continue

            # Find old log files
            log_patterns = [
                '*.log.*',  # Rotated logs
                '*.log.????-??-??',  # Date-stamped logs
                'backup*.log',  # Backup logs
                'django*.log',  # Django logs
            ]

            for pattern in log_patterns:
                for log_file in glob.glob(os.path.join(log_dir, pattern)):
                    try:
                        file_path = Path(log_file)
                        if file_path.is_file():
                            file_time = datetime.fromtimestamp(file_path.stat().st_mtime)

                            if file_time < cutoff_date:
                                file_size = file_path.stat().st_size

                                if not self.dry_run:
                                    file_path.unlink()
                                    self.stdout.write(f'✅ Deleted: {log_file} ({file_size:,} bytes)')
                                else:
                                    self.stdout.write(f'🔍 Would delete: {log_file} ({file_size:,} bytes)')

                                total_files_cleaned += 1
                                total_size_cleaned += file_size

                    except Exception as e:
                        self.stdout.write(f'❌ Error processing {log_file}: {e}')

        if total_files_cleaned > 0:
            size_mb = total_size_cleaned / 1024 / 1024
            action = "Cleaned" if not self.dry_run else "Would clean"
            self.stdout.write(f'\n📊 {action} {total_files_cleaned} log files ({size_mb:.1f} MB)')

    def vacuum_database(self):
        """Run VACUUM ANALYZE to reclaim space and update statistics"""
        if self.dry_run:
            self.stdout.write('🔍 Would run VACUUM ANALYZE on database tables')
            return

        self.stdout.write(self.style.SUCCESS('\n🔄 Running VACUUM ANALYZE'))
        self.stdout.write('=' * 50)

        with connection.cursor() as cursor:
            # Get list of tables to vacuum
            cursor.execute("""
                SELECT tablename
                FROM pg_tables
                WHERE schemaname = 'public'
                ORDER BY tablename
            """)

            tables = [row[0] for row in cursor.fetchall()]

            for table in tables:
                try:
                    start_time = timezone.now()
                    cursor.execute(f'VACUUM ANALYZE {table}')
                    duration = (timezone.now() - start_time).total_seconds()

                    self.stdout.write(f'✅ Vacuumed {table} ({duration:.2f}s)')

                except Exception as e:
                    self.stdout.write(f'❌ Error vacuuming {table}: {e}')

        self.stdout.write('✅ VACUUM ANALYZE completed')

    def optimize_database(self):
        """Run additional database optimization commands"""
        if self.dry_run:
            return

        with connection.cursor() as cursor:
            try:
                # Update table statistics
                cursor.execute('ANALYZE')
                self.stdout.write('✅ Updated table statistics')

                # Reindex if needed (careful in production)
                if not hasattr(connection, 'in_production') or not connection.in_production:
                    cursor.execute('REINDEX DATABASE resee_db')
                    self.stdout.write('✅ Reindexed database')

            except Exception as e:
                self.stdout.write(f'⚠️  Optimization warning: {e}')