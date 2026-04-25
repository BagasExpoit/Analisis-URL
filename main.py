#!/usr/bin/env python3
import os
import re
import sys
import json
import time
import socket
import random
import sqlite3
import threading
from datetime import datetime
from urllib.parse import urlparse

# ============= RICH IMPORTS =============
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn
    from rich.layout import Layout
    from rich.live import Live
    from rich.text import Text
    from rich import box
    from rich.align import Align
    from rich.columns import Columns
    from rich.markdown import Markdown
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("Please install rich: pip install rich")

# ============= COLOR SYSTEM (Fallback) =============
class Colors:
    NEON_GREEN = '\033[38;2;0;255;0m'
    NEON_RED = '\033[38;2;255;0;50m'
    NEON_BLUE = '\033[38;2;0;150;255m'
    NEON_PURPLE = '\033[38;2;180;0;255m'
    NEON_YELLOW = '\033[38;2;255;220;0m'
    NEON_CYAN = '\033[38;2;0;255;200m'
    NEON_PINK = '\033[38;2;255;0;200m'
    NEON_ORANGE = '\033[38;2;255;100;0m'
    NEON_WHITE = '\033[38;2;255;255;255m'
    MATRIX = '\033[38;2;0;255;0m'
    MATRIX_DIM = '\033[38;2;0;100;0m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    BLINK = '\033[5m'

# Initialize Rich Console
console = Console()

# ============= TRY IMPORT REQUESTS =============
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# ============= DATABASE SETUP =============
def init_database():
    conn = sqlite3.connect('threat_scans.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT,
            threat_score INTEGER,
            verdict TEXT,
            timestamp TEXT,
            domain TEXT,
            ip TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_scan(url, score, verdict, domain, ip):
    conn = sqlite3.connect('threat_scans.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO scans (url, threat_score, verdict, timestamp, domain, ip)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (url, score, verdict, datetime.now().isoformat(), domain, ip))
    conn.commit()
    conn.close()

def get_scan_history(limit=50):
    conn = sqlite3.connect('threat_scans.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT url, threat_score, verdict, timestamp, domain, ip 
        FROM scans ORDER BY id DESC LIMIT ?
    ''', (limit,))
    results = cursor.fetchall()
    conn.close()
    return results

def get_statistics():
    conn = sqlite3.connect('threat_scans.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM scans')
    total = cursor.fetchone()[0]
    cursor.execute('SELECT AVG(threat_score) FROM scans')
    avg = cursor.fetchone()[0] or 0
    cursor.execute('SELECT verdict, COUNT(*) FROM scans GROUP BY verdict')
    distribution = cursor.fetchall()
    cursor.execute('SELECT COUNT(DISTINCT domain) FROM scans')
    unique_domains = cursor.fetchone()[0]
    conn.close()
    return {
        'total': total,
        'avg_score': round(avg, 1),
        'distribution': dict(distribution),
        'unique_domains': unique_domains
    }

# ============= API CONFIGURATION =============
API_CONFIG_FILE = "api_config.json"

def load_api_keys():
    if os.path.exists(API_CONFIG_FILE):
        try:
            with open(API_CONFIG_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {"virustotal": "", "urlscan": ""}

def save_api_keys(keys):
    with open(API_CONFIG_FILE, 'w') as f:
        json.dump(keys, f, indent=2)

API_KEYS = load_api_keys()

# ============= COOL ANIMATION ENGINE (Simplified for Rich) =============
class CoolAnim:
    @staticmethod
    def clear():
        os.system('cls' if os.name == 'nt' else 'clear')
    
    @staticmethod
    def cyber_type(text, delay=0.008, color=Colors.NEON_CYAN):
        """Cyber typing with glitch effect on some chars"""
        for char in text:
            if random.random() > 0.95:
                glitch_char = random.choice(['#', '$', '%', '&', '@', '!'])
                sys.stdout.write(Colors.NEON_RED + glitch_char + Colors.RESET)
                time.sleep(0.02)
            sys.stdout.write(color + char + Colors.RESET)
            sys.stdout.flush()
            time.sleep(delay)
        print()
    
    @staticmethod
    def matrix_rain(lines=3, duration=0.5):
        """Enhanced matrix rain with falling effect"""
        chars = '01アイウエオカキクケコサシスセソタチツテト'
        for _ in range(lines):
            line = ''
            for _ in range(60):
                if random.random() > 0.8:
                    line += Colors.MATRIX + random.choice(chars) + Colors.RESET
                else:
                    line += Colors.MATRIX_DIM + random.choice(chars) + Colors.RESET
            sys.stdout.write(line + '\n')
            sys.stdout.flush()
            time.sleep(0.05)
        time.sleep(duration)
    
    @staticmethod
    def scanning_animation(duration=1.0):
        """Cool scanning radar animation"""
        radar_frames = [
            '[    ]', '[=   ]', '[==  ]', '[=== ]', '[====]',
            '[ ===]', '[  ==]', '[   =]', '[    ]'
        ]
        start = time.time()
        i = 0
        while time.time() - start < duration:
            sys.stdout.write(f'\r{Colors.NEON_CYAN}🔍 SCANNING {radar_frames[i % len(radar_frames)]}{Colors.RESET}')
            sys.stdout.flush()
            time.sleep(0.08)
            i += 1
        sys.stdout.write(f'\r{Colors.NEON_GREEN}✓ SCAN COMPLETE     {Colors.RESET}\n')
    
    @staticmethod
    def neon_progress(duration=0.6):
        """Smooth neon progress bar with glow"""
        bar_length = 45
        for i in range(bar_length + 1):
            percent = i / bar_length
            if percent < 0.25:
                color = Colors.NEON_BLUE
            elif percent < 0.5:
                color = Colors.NEON_CYAN
            elif percent < 0.75:
                color = Colors.NEON_YELLOW
            else:
                color = Colors.NEON_RED
            
            bar = ''
            for j in range(bar_length):
                if j < i:
                    if j == i - 1:
                        bar += Colors.NEON_WHITE + '█' + Colors.RESET
                    else:
                        bar += color + '█' + Colors.RESET
                else:
                    bar += Colors.DIM + '░' + Colors.RESET
            
            sys.stdout.write(f'\r  ⚡ [{bar}] {percent*100:.0f}%')
            sys.stdout.flush()
            time.sleep(duration / bar_length)
        print()
    
    @staticmethod
    def loader_cyber(message, duration=0.8):
        """Cyberpunk loading spinner"""
        spinner = ['◢', '◣', '◤', '◥']
        start = time.time()
        i = 0
        while time.time() - start < duration:
            sys.stdout.write(f'\r{Colors.NEON_CYAN}{spinner[i % len(spinner)]} {message}{Colors.RESET}')
            sys.stdout.flush()
            time.sleep(0.08)
            i += 1
        sys.stdout.write(f'\r{Colors.NEON_GREEN}✓ {message}{Colors.RESET}\n')
    
    @staticmethod
    def threat_meter(score):
        """Glowing threat meter"""
        bar_length = 45
        filled = int(bar_length * score / 100)
        
        if score < 30:
            color = Colors.NEON_GREEN
            glow = Colors.NEON_WHITE
        elif score < 60:
            color = Colors.NEON_YELLOW
            glow = Colors.NEON_WHITE
        else:
            color = Colors.NEON_RED
            glow = Colors.NEON_WHITE
        
        bar = ''
        for i in range(bar_length):
            if i < filled:
                if i == filled - 1:
                    bar += glow + '█' + Colors.RESET
                else:
                    bar += color + '█' + Colors.RESET
            else:
                bar += Colors.DIM + '░' + Colors.RESET
        
        sys.stdout.write(f'\r  🎯 [{bar}] {score}%')
        print()

# ============= RICH BANNER =============
def show_rich_banner():
    """Display cyberpunk banner using Rich"""
    console.clear()
    
    # Create cyberpunk-style banner text
    banner_text = Text()
    banner_text.append("╔══════════════════════════════════════════════════════════════════════════════╗\n", style="bold cyan")
    banner_text.append("║", style="bold cyan")
    banner_text.append("     ██╗   ██╗██████╗ ██╗         ████████╗██╗  ██╗██████╗ ███████╗ █████╗ ████████╗    ", style="bold green")
    banner_text.append("║\n", style="bold cyan")
    banner_text.append("║", style="bold cyan")
    banner_text.append("     ██║   ██║██╔══██╗██║         ╚══██╔══╝██║  ██║██╔══██╗██╔════╝██╔══██╗╚══██╔══╝    ", style="bold green")
    banner_text.append("║\n", style="bold cyan")
    banner_text.append("║", style="bold cyan")
    banner_text.append("     ██║   ██║██████╔╝██║            ██║   ███████║██████╔╝█████╗  ███████║   ██║       ", style="bold green")
    banner_text.append("║\n", style="bold cyan")
    banner_text.append("║", style="bold cyan")
    banner_text.append("     ██║   ██║██╔══██╗██║            ██║   ██╔══██║██╔══██╗██╔══╝  ██╔══██║   ██║       ", style="bold green")
    banner_text.append("║\n", style="bold cyan")
    banner_text.append("║", style="bold cyan")
    banner_text.append("     ╚██████╔╝██║  ██║███████╗       ██║   ██║  ██║██║  ██║███████╗██║  ██║   ██║       ", style="bold green")
    banner_text.append("║\n", style="bold cyan")
    banner_text.append("║", style="bold cyan")
    banner_text.append("      ╚═════╝ ╚═╝  ╚═╝╚══════╝       ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝   ╚═╝       ", style="bold green")
    banner_text.append("║\n", style="bold cyan")
    banner_text.append("╚══════════════════════════════════════════════════════════════════════════════╝", style="bold cyan")
    
    console.print(Align.center(banner_text))
    console.print()
    
    # Subtitle with animation effect
    subtitle = Panel(
        "[bold magenta]>> CYBER THREAT INTELLIGENCE TERMINAL v6.0 <<[/bold magenta]",
        border_style="cyan",
        box=box.ROUNDED
    )
    console.print(Align.center(subtitle))
    console.print()
    
    # Author and status info
    info_grid = Table.grid(padding=(0, 2))
    info_grid.add_column(style="green")
    info_grid.add_column(style="cyan")
    
    info_grid.add_row("✍️  AUTHOR:", "[bold]BAGAS RAMANDANI[/bold]")
    
    has_api = bool(API_KEYS.get("virustotal"))
    if has_api:
        info_grid.add_row("🔌 API STATUS:", "[green]● ACTIVE (VirusTotal)[/green]")
    else:
        info_grid.add_row("🔌 API STATUS:", "[yellow]○ INACTIVE (Configure in Option 5)[/yellow]")
    
    info_grid.add_row("🛡️  PROTECTION LEVEL:", "[bold cyan]MAXIMUM[/bold cyan]")
    
    console.print(Align.center(info_grid))
    console.print()
    
    # Decorative line
    console.print("═" * 70, style="dim cyan")

# Fallback banner if Rich is not available
def show_fallback_banner():
    CoolAnim.clear()
    CoolAnim.matrix_rain(2, 0.3)
    
    header = """
    ╔═══════════════════════════════════════════════════════════════╗
    ║     ██╗   ██╗██████╗ ██╗         ████████╗██╗  ██╗██████╗     ║
    ║     ██║   ██║██╔══██╗██║         ╚══██╔══╝██║  ██║██╔══██╗    ║
    ║     ██║   ██║██████╔╝██║            ██║   ███████║██████╔╝    ║
    ║     ██║   ██║██╔══██╗██║            ██║   ██╔══██║██╔══██╗    ║
    ║     ╚██████╔╝██║  ██║███████╗       ██║   ██║  ██║██║  ██║    ║
    ║      ╚═════╝ ╚═╝  ╚═╝╚══════╝       ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝    ║
    ╚═══════════════════════════════════════════════════════════════╝
    """
    for line in header.split('\n'):
        if line.strip():
            CoolAnim.cyber_type(line, 0.001, Colors.NEON_CYAN)
    
    print()
    CoolAnim.cyber_type(">> CYBER THREAT INTELLIGENCE TERMINAL v6.0 <<", 0.01, Colors.NEON_PURPLE)
    print(Colors.DIM + "═"*63 + Colors.RESET)
    CoolAnim.cyber_type(f">> AUTHOR: BAGAS RAMANDANI", 0.01, Colors.NEON_GREEN)
    
    has_api = bool(API_KEYS.get("virustotal"))
    if has_api:
        print(f"{Colors.NEON_GREEN}>> API STATUS: ACTIVE (VirusTotal){Colors.RESET}")
    else:
        print(f"{Colors.NEON_YELLOW}>> API STATUS: INACTIVE (Configure in Option 5){Colors.RESET}")
    
    print(Colors.DIM + "═"*63 + Colors.RESET)
    print()

def show_header():
    if RICH_AVAILABLE:
        show_rich_banner()
    else:
        show_fallback_banner()

# ============= THREAT INTELLIGENCE =============
class ThreatIntel:
    SUSPICIOUS_KEYWORDS = [
        'login', 'verify', 'account', 'secure', 'update', 'confirm',
        'password', 'credential', 'banking', 'wallet', 'crypto'
    ]
    SUSPICIOUS_TLDS = ['.tk', '.ml', '.ga', '.cf', '.xyz', '.top', '.club', '.work']
    URL_SHORTENERS = ['bit.ly', 'tinyurl', 'goo.gl', 'ow.ly', 'is.gd', 't.co']
    
    SAFE_DOMAINS = {
        'google.com', 'youtube.com', 'github.com', 'wikipedia.org',
        'microsoft.com', 'apple.com', 'amazon.com', 'netflix.com'
    }
    
    @staticmethod
    def extract_domain(url):
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path.split('/')[0]
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain
    
    @staticmethod
    def dns_lookup(domain):
        try:
            ip = socket.gethostbyname(domain)
            return {"resolves": True, "ip": ip}
        except:
            return {"resolves": False, "ip": None}
    
    @staticmethod
    def check_virustotal(url):
        if not API_KEYS.get("virustotal") or not REQUESTS_AVAILABLE:
            return None
        try:
            import base64
            headers = {"x-apikey": API_KEYS["virustotal"]}
            url_id = base64.urlsafe_b64encode(url.encode()).decode().strip('=')
            response = requests.get(
                f"https://www.virustotal.com/api/v3/urls/{url_id}",
                headers=headers,
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                stats = data.get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
                malicious = stats.get("malicious", 0)
                if malicious > 0:
                    return {"malicious": malicious, "source": "VirusTotal"}
            return None
        except:
            return None
    
    @classmethod
    def analyze(cls, url, use_api=True):
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        findings = []
        score = 0
        url_lower = url.lower()
        domain = cls.extract_domain(url)
        
        for safe in cls.SAFE_DOMAINS:
            if domain == safe or domain.endswith('.' + safe):
                return {"score": 0, "threat": "SAFE", "emoji": "✅", 
                        "findings": [f"Trusted domain: {safe}"], "malicious": False, "domain": domain, "url": url}
        
        if not url.startswith('https'):
            score += 20
            findings.append("⚠️ No HTTPS encryption")
        
        if re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', domain):
            score += 35
            findings.append("🔴 Direct IP address usage")
        
        for kw in cls.SUSPICIOUS_KEYWORDS:
            if kw in url_lower:
                score += 5
                findings.append(f"⚠️ Suspicious keyword: '{kw}'")
                break
        
        for short in cls.URL_SHORTENERS:
            if short in url_lower:
                score += 15
                findings.append(f"⚠️ URL shortener detected")
                break
        
        for tld in cls.SUSPICIOUS_TLDS:
            if domain.endswith(tld):
                score += 25
                findings.append(f"🔴 Suspicious TLD: {tld}")
                break
        
        if '@' in url:
            score += 45
            findings.append("🔴 '@' symbol - Phishing indicator")
        
        if len(url) > 100:
            score += 10
            findings.append("⚠️ Excessive URL length")
        
        if use_api and REQUESTS_AVAILABLE:
            vt_result = cls.check_virustotal(url)
            if vt_result:
                score = min(100, score + 30)
                findings.append(f"🔴 {vt_result['source']}: Malicious detected")
        
        score = min(100, score)
        
        if score <= 20:
            threat, emoji = "SAFE", "✅"
        elif score <= 50:
            threat, emoji = "LOW RISK", "⚠️"
        elif score <= 75:
            threat, emoji = "HIGH RISK", "🔴"
        else:
            threat, emoji = "CRITICAL", "💀"
        
        return {
            "score": score, "threat": threat, "emoji": emoji,
            "findings": findings, "malicious": score > 50,
            "domain": domain, "url": url
        }

# ============= RICH RESULT DISPLAYS =============
def display_rich_threat_report(result, url, domain, dns):
    """Display threat analysis report using Rich"""
    
    # Create main panel
    title = Panel("[bold red]THREAT ANALYSIS REPORT[/bold red]", border_style="red", box=box.DOUBLE_EDGE)
    console.print(Align.center(title))
    console.print()
    
    # URL Information
    url_panel = Panel(
        f"[bold cyan]{url}[/bold cyan]",
        title="🎯 TARGET ACQUIRED",
        border_style="cyan",
        box=box.ROUNDED
    )
    console.print(url_panel)
    console.print()
    
    # Threat Score with progress bar
    console.print("[bold yellow]⚡ THREAT LEVEL:[/bold yellow]")
    
    # Create a progress bar for threat score
    score_color = "green" if result['score'] < 30 else "yellow" if result['score'] < 60 else "red"
    progress = Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=40),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    )
    task = progress.add_task("", total=100)
    progress.start()
    progress.update(task, completed=result['score'], description=f"[{score_color}]Threat Score[/{score_color}]")
    progress.stop()
    console.print()
    
    # Verdict with appropriate styling
    if result['threat'] == "SAFE":
        verdict_color = "green"
        verdict_icon = "✓"
    elif result['threat'] == "LOW RISK":
        verdict_color = "yellow"
        verdict_icon = "⚠️"
    elif result['threat'] == "HIGH RISK":
        verdict_color = "red"
        verdict_icon = "🔴"
    else:
        verdict_color = "bold red"
        verdict_icon = "💀"
    
    verdict_panel = Panel(
        f"[{verdict_color}]{verdict_icon} VERDICT: {result['threat']} - Score: {result['score']}%[/{verdict_color}]",
        border_style=verdict_color,
        box=box.HEAVY
    )
    console.print(verdict_panel)
    console.print()
    
    # Domain Intelligence
    domain_table = Table(title="🌐 DOMAIN INTELLIGENCE", border_style="blue", box=box.ROUNDED)
    domain_table.add_column("Property", style="cyan", no_wrap=True)
    domain_table.add_column("Value", style="white")
    
    domain_table.add_row("Domain", f"[purple]{domain}[/purple]")
    if dns['resolves']:
        domain_table.add_row("IP Address", f"[green]{dns['ip']}[/green]")
        domain_table.add_row("Status", "[green]✓ Resolves[/green]")
    else:
        domain_table.add_row("IP Address", "[red]⚠️ DNS resolution failed[/red]")
        domain_table.add_row("Status", "[red]✗ Does not resolve[/red]")
    
    console.print(domain_table)
    console.print()
    
    # Threat Indicators
    if result['findings']:
        findings_table = Table(title="🔍 THREAT INDICATORS", border_style="red", box=box.ROUNDED)
        findings_table.add_column("#", style="dim", width=4)
        findings_table.add_column("Finding", style="yellow")
        
        for idx, finding in enumerate(result['findings'], 1):
            findings_table.add_row(str(idx), finding)
        
        console.print(findings_table)
    else:
        safe_panel = Panel(
            "[bold green]✅ NO THREATS DETECTED[/bold green]",
            border_style="green"
        )
        console.print(safe_panel)
    
    console.print()
    
    # Recommendation
    rec_color = "green" if result['threat'] == "SAFE" else "yellow" if result['threat'] == "LOW RISK" else "red"
    if result['threat'] == "SAFE":
        recommendation = "→ URL appears secure for access"
    elif result['threat'] == "LOW RISK":
        recommendation = "→ EXERCISE CAUTION when accessing this URL"
    else:
        recommendation = "→ DO NOT ACCESS THIS URL - Potential threat detected"
    
    rec_panel = Panel(
        f"[{rec_color}]{recommendation}[/{rec_color}]",
        title="💡 RECOMMENDATION",
        border_style=rec_color,
        box=box.ROUNDED
    )
    console.print(rec_panel)

def display_rich_batch_results(results):
    """Display batch scan results using Rich"""
    
    # Calculate statistics
    safe = sum(1 for r in results if r['threat'] == "SAFE")
    low = sum(1 for r in results if r['threat'] == "LOW RISK")
    high = sum(1 for r in results if r['threat'] == "HIGH RISK")
    critical = sum(1 for r in results if r['threat'] == "CRITICAL")
    total = len(results)
    
    # Summary Panel
    summary_text = f"""
[green]✓ SECURE: {safe} ({safe/total*100:.1f}%)[/green]
[yellow]⚠️ CAUTION: {low} ({low/total*100:.1f}%)[/yellow]
[red]🔴 DANGEROUS: {high} ({high/total*100:.1f}%)[/red]
[bold red]💀 CRITICAL: {critical} ({critical/total*100:.1f}%)[/bold red]
    """
    
    summary_panel = Panel(
        summary_text,
        title="📊 BATCH ANALYSIS SUMMARY",
        border_style="cyan",
        box=box.DOUBLE_EDGE
    )
    console.print(Align.center(summary_panel))
    console.print()
    
    # Detailed Results Table
    results_table = Table(title="🔍 DETAILED RESULTS", border_style="blue", box=box.ROUNDED)
    results_table.add_column("Status", style="cyan", width=12)
    results_table.add_column("Score", style="white", width=8, justify="center")
    results_table.add_column("URL", style="white", width=50)
    results_table.add_column("Domain", style="dim", width=30)
    
    for r in results:
        if r['threat'] == "SAFE":
            status_color = "green"
        elif r['threat'] == "LOW RISK":
            status_color = "yellow"
        else:
            status_color = "red"
        
        display_url = r['url'] if len(r['url']) < 47 else r['url'][:44] + "..."
        results_table.add_row(
            f"[{status_color}]{r['emoji']} {r['threat']}[/{status_color}]",
            f"[{status_color}]{r['score']}%[/{status_color}]",
            display_url,
            f"[dim]{r['domain']}[/dim]"
        )
    
    console.print(results_table)
    console.print()
    
    # Warning for dangerous URLs
    if high > 0 or critical > 0:
        warning = Panel(
            f"[bold red]⚠️ WARNING: {high + critical} DANGEROUS URL(S) FOUND ⚠️[/bold red]",
            border_style="red",
            box=box.HEAVY
        )
        console.print(Align.center(warning))

def display_rich_history(history):
    """Display scan history using Rich"""
    
    if not history:
        console.print(Panel("[yellow]No scan history found. Run some scans first![/yellow]", border_style="yellow"))
        return
    
    history_table = Table(title="📜 SCAN HISTORY", border_style="cyan", box=box.ROUNDED)
    history_table.add_column("URL", style="white", width=45)
    history_table.add_column("Score", justify="center", width=8)
    history_table.add_column("Verdict", width=12)
    history_table.add_column("Date", width=12)
    history_table.add_column("Domain", style="dim", width=20)
    
    for url, score, verdict, timestamp, domain, ip in history:
        if verdict == "SAFE":
            verdict_color = "green"
        elif verdict == "LOW RISK":
            verdict_color = "yellow"
        else:
            verdict_color = "red"
        
        url_short = url[:42] + "..." if len(url) > 42 else url
        date_short = timestamp.split('T')[0] if 'T' in timestamp else timestamp[:10]
        
        history_table.add_row(
            url_short,
            f"[{verdict_color}]{score}%[/{verdict_color}]",
            f"[{verdict_color}]{verdict}[/{verdict_color}]",
            date_short,
            f"[dim]{domain}[/dim]"
        )
    
    console.print(history_table)

def display_rich_statistics(stats):
    """Display statistics dashboard using Rich"""
    
    if stats['total'] == 0:
        console.print(Panel("[yellow]No data available. Run some scans first![/yellow]", border_style="yellow"))
        return
    
    # Statistics Grid
    stats_grid = Table.grid(padding=(0, 4))
    stats_grid.add_column(style="cyan", justify="center")
    stats_grid.add_column(style="white", justify="center")
    
    stats_grid.add_row("📊 TOTAL SCANS:", f"[bold green]{stats['total']}[/bold green]")
    stats_grid.add_row("🌐 UNIQUE DOMAINS:", f"[bold blue]{stats['unique_domains']}[/bold blue]")
    stats_grid.add_row("📈 AVG THREAT SCORE:", f"[bold yellow]{stats['avg_score']}%[/bold yellow]")
    
    stats_panel = Panel(stats_grid, title="📈 STATISTICS DASHBOARD", border_style="purple", box=box.DOUBLE_EDGE)
    console.print(Align.center(stats_panel))
    console.print()
    
    # Threat Distribution
    distribution = stats['distribution']
    total = stats['total']
    
    dist_table = Table(title="🎯 THREAT DISTRIBUTION", border_style="cyan", box=box.ROUNDED)
    dist_table.add_column("Category", style="white", width=15)
    dist_table.add_column("Count", justify="center", width=10)
    dist_table.add_column("Percentage", justify="center", width=12)
    dist_table.add_column("Bar", width=40)
    
    categories = ['SAFE', 'LOW RISK', 'HIGH RISK', 'CRITICAL']
    colors = ['green', 'yellow', 'red', 'bold red']
    
    for cat, color in zip(categories, colors):
        count = distribution.get(cat, 0)
        percent = (count / total * 100) if total > 0 else 0
        bar_length = int(percent / 2)
        bar = '█' * bar_length + '░' * (50 - bar_length)
        
        dist_table.add_row(
            f"[{color}]{cat}[/{color}]",
            str(count),
            f"[{color}]{percent:.1f}%[/{color}]",
            f"[{color}]{bar}[/{color}]"
        )
    
    console.print(dist_table)
    console.print()
    
    # Overall Threat Meter
    console.print("[bold cyan]📊 OVERALL THREAT METER:[/bold cyan]")
    CoolAnim.threat_meter(stats['avg_score'])
    console.print()

# ============= UI DISPLAY FUNCTIONS =============
def analyze_single():
    show_header()
    
    # Input panel
    input_panel = Panel(
        "[bold yellow]ENTER URL FOR ANALYSIS[/bold yellow]\n[dim]Format: domain.com OR https://example.com[/dim]",
        border_style="cyan",
        box=box.ROUNDED
    )
    console.print(Align.center(input_panel))
    console.print()
    
    url = console.input("[bold green]⚡ URL > [/bold green]").strip()
    
    if not url:
        return
    
    console.print()
    
    # Scanning animation
    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
        transient=True
    ) as progress:
        task = progress.add_task("[cyan]INITIALIZING THREAT SCAN...", total=100)
        for i in range(101):
            progress.update(task, completed=i)
            time.sleep(0.005)
    
    # Perform analysis
    result = ThreatIntel.analyze(url, use_api=True)
    domain = ThreatIntel.extract_domain(url)
    dns = ThreatIntel.dns_lookup(domain)
    
    # Save to database
    save_scan(url, result['score'], result['threat'], domain, dns.get('ip', 'Unknown'))
    
    # Display results
    show_header()
    display_rich_threat_report(result, url, domain, dns)
    
    console.input("\n[dim]>> Press Enter to continue...[/dim]")

def batch_scan():
    show_header()
    
    # Input panel
    input_panel = Panel(
        "[bold purple]BATCH ANALYSIS[/bold purple]\n[dim]Enter filename (default: urls.txt)[/dim]",
        border_style="purple",
        box=box.ROUNDED
    )
    console.print(Align.center(input_panel))
    console.print()
    
    filename = console.input("[bold yellow]>> FILENAME: [/bold yellow]").strip()
    if not filename:
        filename = "urls.txt"
    
    try:
        with open(filename, 'r') as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        if not urls:
            console.print(Panel("[red]NO URLS FOUND[/red]", border_style="red"))
            time.sleep(1.5)
            return
        
        console.print(f"\n[green]>> SCANNING {len(urls)} TARGETS[/green]\n")
        
        results = []
        
        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console,
            transient=False
        ) as progress:
            task = progress.add_task("[cyan]Scanning URLs...", total=len(urls))
            
            for url in urls:
                progress.update(task, advance=1, description=f"[cyan]Scanning: {url[:50]}...")
                result = ThreatIntel.analyze(url, use_api=True)
                results.append(result)
                save_scan(url, result['score'], result['threat'], 
                         ThreatIntel.extract_domain(url), 'Unknown')
                time.sleep(0.02)
        
        console.print("\n")
        show_header()
        display_rich_batch_results(results)
        
    except FileNotFoundError:
        console.print(Panel(f"[red]FILE NOT FOUND: {filename}[/red]", border_style="red"))
    
    console.input("\n[dim]>> Press Enter to continue...[/dim]")

def show_history():
    show_header()
    history = get_scan_history(20)
    display_rich_history(history)
    console.input("\n[dim]>> Press Enter to continue...[/dim]")

def show_statistics():
    show_header()
    stats = get_statistics()
    display_rich_statistics(stats)
    console.input("\n[dim]>> Press Enter to continue...[/dim]")

def setup_api():
    global API_KEYS
    show_header()
    
    api_panel = Panel(
        "[bold cyan]API CONFIGURATION[/bold cyan]\n\n"
        "[yellow]API keys are OPTIONAL - They add cloud threat intelligence[/yellow]\n\n"
        "[green]📍 Get free API keys:[/green]\n"
        "  VirusTotal: https://www.virustotal.com/gui/join-us\n"
        "  → Free tier: 500 requests/day",
        border_style="cyan",
        box=box.ROUNDED
    )
    console.print(Align.center(api_panel))
    console.print()
    
    current_vt = API_KEYS.get("virustotal", "")
    if current_vt:
        console.print(f"[green]Current VirusTotal: {current_vt[:8]}...{current_vt[-4:]}[/green]")
    
    vt_key = console.input("[bold yellow]\n>> VirusTotal API Key [ENTER to keep]: [/bold yellow]").strip()
    if vt_key:
        API_KEYS["virustotal"] = vt_key
    
    save_api_keys(API_KEYS)
    
    console.print()
    console.print(Panel("[bold green]✓ API CONFIGURATION SAVED[/bold green]", border_style="green"))
    console.input("\n[dim]>> Press Enter to continue...[/dim]")

def show_help():
    show_header()
    
    help_panel = Panel(
        "[bold cyan]HELP & FEATURES[/bold cyan]",
        border_style="cyan",
        box=box.DOUBLE_EDGE
    )
    console.print(Align.center(help_panel))
    console.print()
    
    features_table = Table(border_style="blue", box=box.ROUNDED, show_header=False)
    features_table.add_column("Feature", style="green", width=25)
    features_table.add_column("Description", style="white")
    
    features_table.add_row("🔍 Single URL Scan", "Analyze individual URLs with full visual feedback")
    features_table.add_row("📊 Batch Analysis", "Scan multiple URLs from a text file")
    features_table.add_row("📜 Scan History", "View all previous scan results")
    features_table.add_row("📈 Statistics Dashboard", "View threat trends and distribution")
    features_table.add_row("🔑 API Configuration", "Add VirusTotal API for enhanced detection")
    
    console.print(features_table)
    console.print()
    
    howto_panel = Panel(
        "[bold yellow]>> HOW TO USE BATCH SCAN:[/bold yellow]\n\n"
        "[dim]• Create a file called 'urls.txt'[/dim]\n"
        "[dim]• Put one URL per line[/dim]\n"
        "[dim]• Lines starting with # are ignored[/dim]",
        border_style="yellow",
        box=box.ROUNDED
    )
    console.print(howto_panel)
    
    console.input("\n[dim]>> Press Enter to continue...[/dim]")

def main():
    init_database()
    
    while True:
        show_header()
        
        # Create menu table
        menu_table = Table(border_style="cyan", box=box.ROUNDED, title="MAIN TERMINAL", title_style="bold magenta")
        menu_table.add_column("Option", style="green", width=8, justify="center")
        menu_table.add_column("Action", style="white", width=40)
        
        menu_table.add_row("[1]", "🔍 SINGLE URL SCAN")
        menu_table.add_row("[2]", "📊 BATCH ANALYSIS")
        menu_table.add_row("[3]", "📜 SCAN HISTORY")
        menu_table.add_row("[4]", "📈 STATISTICS DASHBOARD")
        menu_table.add_row("[5]", "🔑 API CONFIGURATION")
        menu_table.add_row("[6]", "🎨 HELP & FEATURES")
        menu_table.add_row("[7]", "🚪 EXIT TERMINAL")
        
        console.print(Align.center(menu_table))
        console.print()
        
        choice = console.input("[bold yellow]>> SELECT OPTION [1-7]: [/bold yellow]")
        
        if choice == '1':
            analyze_single()
        elif choice == '2':
            batch_scan()
        elif choice == '3':
            show_history()
        elif choice == '4':
            show_statistics()
        elif choice == '5':
            setup_api()
        elif choice == '6':
            show_help()
        elif choice == '7':
            show_header()
            console.print(Panel("[bold red]TERMINATING CONNECTION[/bold red]", border_style="red", box=box.HEAVY))
            console.print()
            console.print("[green]Thank you for using Cyber Threat Detector[/green]")
            console.print("[purple]Stay vigilant. Stay secure. - BAGAS RAMANDANI[/purple]")
            console.print()
            sys.exit(0)
        else:
            console.print(Panel("[red]INVALID COMMAND[/red]", border_style="red"))
            time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print(f"\n[red]\n>> EMERGENCY SHUTDOWN[/red]")
        sys.exit(0)
