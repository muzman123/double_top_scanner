"""
Notifier Module
Handles email notifications and CSV export
"""

import pandas as pd
import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class Notifier:
    """Handles notifications via email and CSV export"""
    
    def __init__(self, config):
        """
        Initialize notifier
        
        Args:
            config (dict): Configuration dictionary
        """
        self.config = config
        self.notification_config = config['notification']
        self.output_config = config['output']
    
    def notify(self, results):
        """
        Send notifications based on config
        
        Args:
            results (list): List of candidate dictionaries
        """
        # Generate CSV
        csv_path = None
        if self.output_config['csv_enabled']:
            csv_path = self.export_csv(results)
        
        # Send email
        if self.notification_config['method'] in ['email', 'both'] and self.notification_config['email_enabled']:
            self.send_email(results, csv_path)
        
        # Console output
        if self.notification_config['method'] in ['console', 'both']:
            self.print_console(results)
    
    def export_csv(self, results):
        """
        Export results to CSV file
        
        Args:
            results (list): List of candidate dictionaries
        
        Returns:
            str: Path to CSV file
        """
        if not results:
            logger.info("No results to export")
            return None
        
        # Convert to DataFrame
        df = pd.DataFrame(results)
        
        # Format date in filename
        date_str = datetime.now().strftime('%Y-%m-%d')
        csv_path = self.output_config['csv_path'].format(date=date_str)
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        
        # Export
        df.to_csv(csv_path, index=False)
        logger.info(f"Results exported to {csv_path}")
        
        return csv_path
    
    def send_email(self, results, csv_path=None):
        """
        Send email notification with results
        
        Args:
            results (list): List of candidate dictionaries
            csv_path (str): Path to CSV file to attach
        """
        try:
            # Get SMTP credentials
            smtp_username = self.notification_config.get('smtp_username') or os.environ.get('SMTP_USERNAME')
            smtp_password = self.notification_config.get('smtp_password') or os.environ.get('SMTP_PASSWORD')
            
            if not smtp_username or not smtp_password:
                logger.error("SMTP credentials not configured. Set SMTP_USERNAME and SMTP_PASSWORD environment variables.")
                return
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.notification_config['email_from']
            msg['To'] = self.notification_config['email_to']
            
            # Subject
            date_str = datetime.now().strftime('%Y-%m-%d')
            subject = f"{self.notification_config['email_subject_prefix']} - {len(results)} Opportunities - {date_str}"
            msg['Subject'] = subject
            
            # Email body
            body = self._create_email_body(results)
            msg.attach(MIMEText(body, 'html'))
            
            # Attach CSV if available
            if csv_path and self.notification_config['attach_csv']:
                try:
                    with open(csv_path, 'rb') as f:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(f.read())
                    
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', f'attachment; filename={os.path.basename(csv_path)}')
                    msg.attach(part)
                except Exception as e:
                    logger.error(f"Error attaching CSV: {e}")
            
            # Send email
            smtp_host = self.notification_config['smtp_host']
            smtp_port = self.notification_config['smtp_port']
            
            server = smtplib.SMTP(smtp_host, smtp_port)
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email sent to {self.notification_config['email_to']}")
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")
    
    def _create_email_body(self, results):
        """
        Create HTML email body
        
        Args:
            results (list): List of candidate dictionaries
        
        Returns:
            str: HTML email body
        """
        # Group by score
        premium = [r for r in results if r['score'] == 6]
        high_quality = [r for r in results if r['score'] == 5]
        good = [r for r in results if r['score'] == 4]
        watchlist = [r for r in results if r['score'] == 3]
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                h2 {{ color: #333; }}
                table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
                th {{ background-color: #4CAF50; color: white; padding: 12px; text-align: left; }}
                td {{ padding: 8px; border-bottom: 1px solid #ddd; }}
                tr:hover {{ background-color: #f5f5f5; }}
                .premium {{ background-color: #FFD700; }}
                .high {{ background-color: #90EE90; }}
                .good {{ background-color: #87CEEB; }}
                .watch {{ background-color: #DDA0DD; }}
                .summary {{ background-color: #f0f0f0; padding: 15px; margin-bottom: 20px; }}
            </style>
        </head>
        <body>
            <h1>🎯 Double Top Scanner Results</h1>
            <p><strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
            
            <div class="summary">
                <h3>Summary</h3>
                <ul>
                    <li><strong>Premium Candidates (6/6):</strong> {len(premium)}</li>
                    <li><strong>High-Quality Candidates (5/6):</strong> {len(high_quality)}</li>
                    <li><strong>Good Candidates (4/6):</strong> {len(good)}</li>
                    <li><strong>Watchlist (3/6):</strong> {len(watchlist)}</li>
                    <li><strong>Total Opportunities:</strong> {len(results)}</li>
                </ul>
            </div>
        """
        
        # Premium Candidates
        if premium:
            html += self._create_table_section("🏆 Premium Candidates (Score 6/6)", premium, "premium")
        
        # High-Quality Candidates
        if high_quality:
            html += self._create_table_section("⭐ High-Quality Candidates (Score 5/6)", high_quality, "high")
        
        # Good Candidates
        if good:
            html += self._create_table_section("✅ Good Candidates (Score 4/6)", good, "good")
        
        # Watchlist
        if watchlist:
            html += self._create_table_section("👀 Watchlist (Score 3/6)", watchlist, "watch")
        
        html += """
            <hr>
            <p><em>This is an automated alert from Double Top Scanner. Review patterns manually before trading.</em></p>
        </body>
        </html>
        """
        
        return html
    
    def _create_table_section(self, title, candidates, css_class):
        """Create HTML table section for a group of candidates"""
        
        html = f"<h2>{title}</h2>"
        html += f'<table class="{css_class}">'
        html += """
            <tr>
                <th>Symbol</th>
                <th>Price</th>
                <th>Change %</th>
                <th>Peak 1</th>
                <th>Peak 2</th>
                <th>Trough Depth</th>
                <th>RSI Daily</th>
                <th>RSI Div</th>
                <th>Chart</th>
            </tr>
        """
        
        for c in candidates:
            rsi_daily = f"{c['rsi_daily']:.1f}" if c['rsi_daily'] else "N/A"
            rsi_div = "" if c['rsi_divergence'] else "✗"
            
            html += f"""
            <tr>
                <td><strong>{c['symbol']}</strong></td>
                <td>${c['current_price']:.2f}</td>
                <td>{c['price_change_pct']:+.2f}%</td>
                <td>${c['peak1_price']:.2f}</td>
                <td>${c['peak2_price']:.2f}</td>
                <td>{c['trough_depth_pct']:.1f}%</td>
                <td>{rsi_daily}</td>
                <td>{rsi_div}</td>
                <td><a href="{c['chart_link']}">View</a></td>
            </tr>
            """
        
        html += "</table>"
        return html
    
    def print_console(self, results):
        """
        Print results to console
        
        Args:
            results (list): List of candidate dictionaries
        """
        print("\n" + "="*100)
        print(f"DOUBLE TOP SCANNER RESULTS - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print("="*100)
        
        if not results:
            print("No opportunities found.")
            return
        
        # Group by score
        for score in [6, 5, 4, 3]:
            candidates = [r for r in results if r['score'] == score]
            if not candidates:
                continue
            
            score_labels = {6: "PREMIUM", 5: "HIGH-QUALITY", 4: "GOOD", 3: "WATCHLIST"}
            print(f"\n{score_labels[score]} CANDIDATES (Score {score}/6): {len(candidates)}")
            print("-" * 100)
            
            for c in candidates:
                rsi_daily = f"{c['rsi_daily']:.1f}" if c['rsi_daily'] else "N/A"
                print(f"{c['symbol']:8} | ${c['current_price']:8.2f} | "
                      f"Peak1: ${c['peak1_price']:7.2f} | Peak2: ${c['peak2_price']:7.2f} | "
                      f"Trough: {c['trough_depth_pct']:5.1f}% | RSI: {rsi_daily:>5} | "
                      f"Div: {'' if c['rsi_divergence'] else '✗'}")
        
        print("\n" + "="*100)
        print(f"Total: {len(results)} opportunities")
        print("="*100 + "\n")


if __name__ == "__main__":
    # Test notifier with sample data
    import yaml
    
    logging.basicConfig(level=logging.INFO)
    
    # Load config
    with open('../config/settings.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Create sample results
    sample_results = [
        {
            'date': '2025-10-22',
            'symbol': 'AAPL',
            'asset_type': 'stocks',
            'score': 6,
            'current_price': 175.23,
            'price_change_pct': -1.23,
            'peak1_price': 178.45,
            'peak2_price': 177.89,
            'trough_price': 172.10,
            'trough_depth_pct': 3.56,
            'rsi_daily': 73.5,
            'rsi_divergence': True,
            'chart_link': 'https://finance.yahoo.com/chart/AAPL'
        },
        {
            'date': '2025-10-22',
            'symbol': 'MSFT',
            'asset_type': 'stocks',
            'score': 4,
            'current_price': 410.67,
            'price_change_pct': 0.45,
            'peak1_price': 415.23,
            'peak2_price': 414.89,
            'trough_price': 402.10,
            'trough_depth_pct': 3.15,
            'rsi_daily': 68.2,
            'rsi_divergence': False,
            'chart_link': 'https://finance.yahoo.com/chart/MSFT'
        }
    ]
    
    notifier = Notifier(config)
    
    # Test console output
    print("Testing console output...")
    notifier.print_console(sample_results)
    
    # Test CSV export
    print("\nTesting CSV export...")
    csv_path = notifier.export_csv(sample_results)
    print(f"CSV exported to: {csv_path}")
