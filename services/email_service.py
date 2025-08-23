"""
Email service module for sending notifications and reports.
"""

import os
import logging
import smtplib
import queue
import threading
import time
from typing import Dict, List, Optional, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from core.config import Config

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending email notifications with Gmail"""
    
    def __init__(self):
        self.email_host = Config.EMAIL_HOST
        self.email_port = Config.EMAIL_PORT
        self.email_user = Config.EMAIL_USER
        self.email_password = Config.EMAIL_PASSWORD
        self.recipients = [email.strip() for email in Config.EMAIL_RECIPIENTS if email.strip()]
        
        # Feature flag to enable/disable emails
        notif_flag = os.environ.get('EMAIL_NOTIFICATIONS_ENABLED', '0').lower() in {'1', 'true', 'yes', 'on'}
        self.enabled = bool(self.email_user and self.email_password and self.recipients) and notif_flag
        
        self.app_url = Config.APP_URL
        
        # Lightweight in-memory queue with background worker
        self._queue: queue.Queue[dict] = queue.Queue()
        self._worker_started = False
        
        if self.enabled:
            logger.info(f"✅ Email notifications enabled for {len(self.recipients)} recipients")
            logger.info(f"🔗 App URL: {self.app_url}")
            # Start background worker once
            self._start_worker()
        else:
            logger.warning("⚠️ Email notifications disabled - missing configuration")
    
    def _start_worker(self):
        """Start the background email worker"""
        try:
            if not self._worker_started:
                t = threading.Thread(target=self._worker_loop, daemon=True)
                t.start()
                self._worker_started = True
                logger.info("✅ Email worker started")
        except Exception as e:
            logger.error(f"❌ Failed to start email worker: {e}")
    
    def send_notification_async(self, subject: str, content: str, item_data: Optional[Dict] = None):
        """Send a notification asynchronously"""
        if not self.enabled:
            logger.debug("Email notifications disabled")
            return
        
        # Enqueue for background worker
        try:
            self._queue.put({
                "subject": subject,
                "content": content,
                "item_data": item_data,
                "attempt": 0
            }, block=False)
            logger.debug(f"Email queued: {subject}")
        except Exception as e:
            logger.error(f"❌ Email queue full: {e}")
    
    def _worker_loop(self):
        """Background worker that processes the email queue with retries"""
        while True:
            try:
                job = self._queue.get(timeout=5)
            except:
                continue
            
            try:
                self._send_email(job.get("subject"), job.get("content"), job.get("item_data"))
            except Exception as e:
                # Retry up to 3 times with exponential backoff
                attempt = int(job.get("attempt", 0)) + 1
                if attempt <= 3:
                    backoff_seconds = min(60, 2 ** attempt)
                    logger.warning(f"📧 Retry email in {backoff_seconds}s (attempt {attempt}/3): {e}")
                    time.sleep(backoff_seconds)
                    job["attempt"] = attempt
                    try:
                        self._queue.put(job, block=False)
                    except:
                        pass
                else:
                    logger.error(f"❌ Email failed after 3 attempts: {e}")
            finally:
                try:
                    self._queue.task_done()
                except:
                    pass
    
    def _send_email(self, subject: str, content: str, item_data: Optional[Dict] = None):
        """Actually send the email via Gmail"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.email_user
            msg['To'] = ", ".join(self.recipients)
            msg['Subject'] = f"[BONVIN Collection] {subject}"
            
            # HTML content with webapp styling
            html_content = self._create_html_content(subject, content, item_data)
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            # Text fallback content
            text_content = self._create_text_content(subject, content, item_data)
            text_part = MIMEText(text_content, 'plain', 'utf-8')
            msg.attach(text_part)
            
            # Send email via Gmail
            with smtplib.SMTP(self.email_host, self.email_port) as server:
                server.starttls()
                server.login(self.email_user, self.email_password)
                server.send_message(msg)
            
            logger.info(f"✅ Email sent: {subject}")
        except Exception as e:
            logger.error(f"❌ Email send error: {e}")
            raise
    
    def send_market_report(self, report_data: Dict[str, Any]) -> bool:
        """Send a market report email"""
        if not self.enabled:
            return False
        
        try:
            subject = f"Market Report - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
            # Build content
            content_parts = []
            
            if 'summary' in report_data:
                content_parts.append(f"📊 SUMMARY\n{report_data['summary']}")
            
            if 'indices' in report_data:
                content_parts.append("\n📈 MARKET INDICES")
                for index in report_data['indices']:
                    content_parts.append(f"• {index['name']}: {index['value']} ({index['change']})")
            
            if 'stocks' in report_data:
                content_parts.append("\n💼 PORTFOLIO STOCKS")
                for stock in report_data['stocks']:
                    content_parts.append(
                        f"• {stock['symbol']}: {stock['price']} {stock['currency']} "
                        f"({stock.get('change_percent', 'N/A')})"
                    )
            
            content = "\n".join(content_parts)
            
            self.send_notification_async(subject, content, report_data)
            return True
        except Exception as e:
            logger.error(f"Error sending market report: {e}")
            return False
    
    def _create_html_content(self, subject: str, content: str, item_data: Optional[Dict] = None) -> str:
        """Create HTML email content with webapp styling"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Convert line breaks to HTML
        html_content = content.replace('\n', '<br>')
        
        # Build item details section if data provided
        item_details = ""
        if item_data:
            details = []
            if 'name' in item_data:
                details.append(f"<strong>Name:</strong> {item_data['name']}")
            if 'category' in item_data:
                details.append(f"<strong>Category:</strong> {item_data['category']}")
            if 'status' in item_data:
                details.append(f"<strong>Status:</strong> {item_data['status']}")
            if 'current_value' in item_data:
                value = item_data['current_value']
                details.append(f"<strong>Value:</strong> CHF {value:,.2f}")
            if 'stock_symbol' in item_data:
                details.append(f"<strong>Symbol:</strong> {item_data['stock_symbol']}")
            
            if details:
                item_details = f"""
                <div style="background: #f8f9fa; border-left: 4px solid #007bff; padding: 15px; margin: 20px 0;">
                    <h3 style="margin-top: 0; color: #343a40;">Item Details</h3>
                    {'<br>'.join(details)}
                </div>
                """
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; 
                     line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            
            <!-- Header -->
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        color: white; padding: 30px; border-radius: 10px 10px 0 0; text-align: center;">
                <h1 style="margin: 0; font-size: 28px;">BONVIN Collection</h1>
                <p style="margin: 10px 0 0 0; opacity: 0.9;">Private Collection Management System</p>
            </div>
            
            <!-- Content -->
            <div style="background: white; padding: 30px; border: 1px solid #e1e8ed; 
                        border-top: none; border-radius: 0 0 10px 10px;">
                <h2 style="color: #343a40; border-bottom: 2px solid #f0f0f0; padding-bottom: 10px;">
                    {subject}
                </h2>
                
                <div style="margin: 20px 0;">
                    {html_content}
                </div>
                
                {item_details}
                
                <!-- Action Button -->
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{self.app_url}" 
                       style="display: inline-block; padding: 12px 30px; 
                              background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                              color: white; text-decoration: none; border-radius: 5px;
                              font-weight: bold;">
                        View in Application
                    </a>
                </div>
            </div>
            
            <!-- Footer -->
            <div style="text-align: center; padding: 20px; color: #6c757d; font-size: 12px;">
                <p>Sent on {timestamp}</p>
                <p>© 2024 BONVIN Collection Management. All rights reserved.</p>
            </div>
        </body>
        </html>
        """
    
    def _create_text_content(self, subject: str, content: str, item_data: Optional[Dict] = None) -> str:
        """Create plain text email content"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        text_parts = [
            "=" * 50,
            "BONVIN COLLECTION",
            "Private Collection Management System",
            "=" * 50,
            "",
            subject,
            "-" * len(subject),
            "",
            content
        ]
        
        if item_data:
            text_parts.extend([
                "",
                "ITEM DETAILS:",
                "-" * 20
            ])
            
            if 'name' in item_data:
                text_parts.append(f"Name: {item_data['name']}")
            if 'category' in item_data:
                text_parts.append(f"Category: {item_data['category']}")
            if 'status' in item_data:
                text_parts.append(f"Status: {item_data['status']}")
            if 'current_value' in item_data:
                value = item_data['current_value']
                text_parts.append(f"Value: CHF {value:,.2f}")
            if 'stock_symbol' in item_data:
                text_parts.append(f"Symbol: {item_data['stock_symbol']}")
        
        text_parts.extend([
            "",
            f"View in application: {self.app_url}",
            "",
            "=" * 50,
            f"Sent on {timestamp}",
            "© 2024 BONVIN Collection Management"
        ])
        
        return "\n".join(text_parts)
    
    def test_connection(self) -> bool:
        """Test email connection"""
        if not self.enabled:
            return False
        
        try:
            with smtplib.SMTP(self.email_host, self.email_port) as server:
                server.starttls()
                server.login(self.email_user, self.email_password)
            logger.info("✅ Email connection test successful")
            return True
        except Exception as e:
            logger.error(f"❌ Email connection test failed: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get email service status"""
        return {
            'enabled': self.enabled,
            'configured': bool(self.email_user and self.email_password),
            'recipients': len(self.recipients),
            'queue_size': self._queue.qsize() if self.enabled else 0,
            'worker_running': self._worker_started
        }


# Create singleton instance
email_service = EmailService()