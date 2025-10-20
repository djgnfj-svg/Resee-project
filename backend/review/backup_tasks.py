"""
Backup tasks for Celery Beat
"""
import logging
import subprocess
import os
from datetime import datetime
from celery import shared_task
from django.conf import settings

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def backup_database(self, environment='production'):
    """
    Backup database using pg_dump

    Args:
        environment: 'production' or 'development'
    """
    try:
        logger.info(f"Starting database backup for {environment}")

        # Get database settings
        db_settings = settings.DATABASES['default']
        db_name = db_settings['NAME']
        db_user = db_settings['USER']
        db_password = db_settings['PASSWORD']
        db_host = db_settings['HOST']
        db_port = db_settings.get('PORT', '5432')

        # Create backup filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"{db_name}_{environment}_{timestamp}.sql.gz"
        backup_path = f"/tmp/{backup_filename}"

        # Set PGPASSWORD environment variable
        env = os.environ.copy()
        env['PGPASSWORD'] = db_password

        # Run pg_dump with gzip compression
        dump_cmd = f"pg_dump -h {db_host} -p {db_port} -U {db_user} {db_name}"
        gzip_cmd = f"gzip > {backup_path}"
        full_cmd = f"{dump_cmd} | {gzip_cmd}"

        result = subprocess.run(
            full_cmd,
            shell=True,
            env=env,
            capture_output=True,
            text=True,
            timeout=600  # 10 minutes timeout
        )

        if result.returncode == 0:
            # Get backup file size
            file_size = os.path.getsize(backup_path)
            size_mb = file_size / (1024 * 1024)

            logger.info(f"Database backup completed: {backup_filename} ({size_mb:.2f} MB)")

            # Send Slack notification
            try:
                from utils.slack_notifications import slack_notifier
                slack_notifier.send_alert(
                    f"✅ Database backup completed successfully\n"
                    f"• Environment: {environment}\n"
                    f"• File: {backup_filename}\n"
                    f"• Size: {size_mb:.2f} MB",
                    level='success',
                    title='Backup Success'
                )
            except Exception as slack_error:
                logger.warning(f"Failed to send Slack notification: {slack_error}")

            return {
                'status': 'success',
                'filename': backup_filename,
                'size_mb': round(size_mb, 2)
            }
        else:
            error_msg = result.stderr or "Unknown error"
            logger.error(f"Database backup failed: {error_msg}")

            # Send Slack alert
            try:
                from utils.slack_notifications import slack_notifier
                slack_notifier.send_alert(
                    f"🔴 Database backup failed\n"
                    f"• Environment: {environment}\n"
                    f"• Error: {error_msg}",
                    level='error',
                    title='Backup Failed'
                )
            except Exception as slack_error:
                logger.warning(f"Failed to send Slack notification: {slack_error}")

            raise Exception(f"Backup failed: {error_msg}")

    except subprocess.TimeoutExpired:
        logger.error("Database backup timed out")
        raise self.retry(countdown=300)  # Retry after 5 minutes
    except Exception as e:
        logger.error(f"Database backup error: {e}")
        raise self.retry(countdown=300)
