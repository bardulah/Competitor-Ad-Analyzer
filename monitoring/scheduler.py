"""Monitoring and scheduling system for automated competitor tracking."""

import logging
from typing import Optional, List
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from database import AdRepository, get_session
from database.models import MonitoringJob
from scrapers.async_scraper import AsyncFacebookScraper, AsyncGoogleScraper
import asyncio

logger = logging.getLogger(__name__)


class MonitoringSystem:
    """System for monitoring competitors and sending alerts."""

    def __init__(self):
        """Initialize monitoring system."""
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        logger.info("Monitoring system initialized")

    def add_monitoring_job(self, job_name: str, advertiser: str,
                          platform: str = 'facebook',
                          schedule_type: str = 'daily',
                          schedule_time: str = '09:00',
                          alert_email: Optional[str] = None,
                          alert_threshold: int = 1) -> MonitoringJob:
        """Add a new monitoring job.

        Args:
            job_name: Name for the job
            advertiser: Advertiser to monitor
            platform: Platform to monitor
            schedule_type: 'daily', 'weekly', or 'monthly'
            schedule_time: Time to run (HH:MM format)
            alert_email: Email for alerts
            alert_threshold: Number of new ads to trigger alert

        Returns:
            Created MonitoringJob
        """
        logger.info(f"Adding monitoring job: {job_name} for {advertiser}")

        # Create database entry
        session = get_session()
        try:
            job = MonitoringJob(
                job_name=job_name,
                advertiser=advertiser,
                platform=platform,
                schedule_type=schedule_type,
                schedule_time=schedule_time,
                alert_email=alert_email,
                alert_threshold=alert_threshold,
                is_active=True
            )

            session.add(job)
            session.commit()
            session.refresh(job)

            # Schedule the job
            self._schedule_job(job)

            logger.info(f"Monitoring job {job_name} created successfully")
            return job

        finally:
            session.close()

    def _schedule_job(self, job: MonitoringJob):
        """Schedule a monitoring job with APScheduler.

        Args:
            job: MonitoringJob to schedule
        """
        hour, minute = job.schedule_time.split(':')

        if job.schedule_type == 'daily':
            trigger = CronTrigger(hour=int(hour), minute=int(minute))
        elif job.schedule_type == 'weekly':
            trigger = CronTrigger(day_of_week='mon', hour=int(hour), minute=int(minute))
        elif job.schedule_type == 'monthly':
            trigger = CronTrigger(day=1, hour=int(hour), minute=int(minute))
        else:
            logger.error(f"Unknown schedule type: {job.schedule_type}")
            return

        self.scheduler.add_job(
            func=self._run_monitoring_check,
            trigger=trigger,
            args=[job.id],
            id=f"monitor_{job.id}",
            name=job.job_name,
            replace_existing=True
        )

        logger.info(f"Scheduled job {job.job_name} with trigger: {trigger}")

    def _run_monitoring_check(self, job_id: int):
        """Run a monitoring check for a specific job.

        Args:
            job_id: ID of the MonitoringJob
        """
        session = get_session()
        try:
            job = session.query(MonitoringJob).filter_by(id=job_id).first()

            if not job or not job.is_active:
                logger.warning(f"Job {job_id} not found or inactive")
                return

            logger.info(f"Running monitoring check for: {job.job_name}")

            # Count current ads
            with AdRepository() as ad_repo:
                current_ads = ad_repo.get_ads_by_advertiser(job.advertiser, limit=10000)
                current_count = len(current_ads)

            # Compare with last count
            last_count = job.last_ads_count or 0
            new_ads_count = max(0, current_count - last_count)

            logger.info(f"Found {new_ads_count} new ads for {job.advertiser}")

            # Update job
            job.last_run = datetime.utcnow()
            job.last_ads_count = current_count

            # Calculate next run
            if job.schedule_type == 'daily':
                job.next_run = datetime.utcnow() + timedelta(days=1)
            elif job.schedule_type == 'weekly':
                job.next_run = datetime.utcnow() + timedelta(weeks=1)
            elif job.schedule_type == 'monthly':
                job.next_run = datetime.utcnow() + timedelta(days=30)

            session.commit()

            # Send alert if threshold met
            if new_ads_count >= job.alert_threshold:
                self._send_alert(job, new_ads_count, current_ads[:new_ads_count])

        except Exception as e:
            logger.error(f"Error in monitoring check for job {job_id}: {e}")
        finally:
            session.close()

    def _send_alert(self, job: MonitoringJob, new_ads_count: int, new_ads: List):
        """Send an alert about new ads.

        Args:
            job: MonitoringJob that triggered alert
            new_ads_count: Number of new ads
            new_ads: List of new Advertisement objects
        """
        logger.info(f"Sending alert for job {job.job_name}: {new_ads_count} new ads")

        # Prepare alert message
        message = self._format_alert_message(job, new_ads_count, new_ads)

        # Send email if configured
        if job.alert_email:
            try:
                self._send_email_alert(job.alert_email, job.job_name, message)
            except Exception as e:
                logger.error(f"Failed to send email alert: {e}")

        # Call webhook if configured
        if job.alert_webhook:
            try:
                self._send_webhook_alert(job.alert_webhook, {
                    'job_name': job.job_name,
                    'advertiser': job.advertiser,
                    'new_ads_count': new_ads_count,
                    'timestamp': datetime.utcnow().isoformat()
                })
            except Exception as e:
                logger.error(f"Failed to send webhook alert: {e}")

    def _format_alert_message(self, job: MonitoringJob, new_ads_count: int, new_ads: List) -> str:
        """Format alert message.

        Args:
            job: MonitoringJob
            new_ads_count: Number of new ads
            new_ads: List of new ads

        Returns:
            Formatted message string
        """
        message = f"""
Competitor Alert: {job.advertiser}

{job.advertiser} has launched {new_ads_count} new advertisements!

Recent Ads:
"""

        for i, ad in enumerate(new_ads[:5], 1):
            message += f"\n{i}. {ad.headline or 'No headline'}"
            if ad.body_text:
                message += f"\n   {ad.body_text[:100]}..."
            message += f"\n   Platform: {ad.platform}"
            message += "\n"

        message += f"\nMonitoring Job: {job.job_name}"
        message += f"\nCheck Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"

        return message

    def _send_email_alert(self, email: str, subject: str, message: str):
        """Send email alert (requires SMTP configuration).

        Args:
            email: Recipient email
            subject: Email subject
            message: Email message
        """
        # Note: This is a placeholder. In production, configure SMTP settings
        logger.info(f"Would send email to {email}: {subject}")
        # TODO: Implement actual email sending with SMTP
        pass

    def _send_webhook_alert(self, webhook_url: str, data: dict):
        """Send webhook alert.

        Args:
            webhook_url: Webhook URL
            data: Data to send
        """
        import requests

        try:
            response = requests.post(webhook_url, json=data, timeout=10)
            response.raise_for_status()
            logger.info(f"Webhook alert sent successfully to {webhook_url}")
        except Exception as e:
            logger.error(f"Failed to send webhook: {e}")

    def list_jobs(self) -> List[MonitoringJob]:
        """List all monitoring jobs.

        Returns:
            List of MonitoringJob objects
        """
        session = get_session()
        try:
            jobs = session.query(MonitoringJob).all()
            return jobs
        finally:
            session.close()

    def deactivate_job(self, job_id: int):
        """Deactivate a monitoring job.

        Args:
            job_id: ID of job to deactivate
        """
        session = get_session()
        try:
            job = session.query(MonitoringJob).filter_by(id=job_id).first()
            if job:
                job.is_active = False
                session.commit()

                # Remove from scheduler
                try:
                    self.scheduler.remove_job(f"monitor_{job_id}")
                except:
                    pass

                logger.info(f"Deactivated job {job_id}")
        finally:
            session.close()

    def shutdown(self):
        """Shutdown the monitoring system."""
        self.scheduler.shutdown()
        logger.info("Monitoring system shut down")
