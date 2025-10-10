"""
UX/UI Audit Script - Doktrin Project
Tüm template dosyalarını tarar ve UX sorunlarını tespit eder
"""

import os
import re
from pathlib import Path

# Renk kodları
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

issues = {
    'critical': [],
    'high': [],
    'medium': [],
    'low': []
}

def check_template(filepath):
    """Template dosyasını analiz et"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')

    relative_path = filepath.replace('/Users/ugurismail/Desktop/doktrin-project/', '')

    # 1. Inline style kontrolü
    inline_styles = re.findall(r'style="[^"]*"', content)
    if len(inline_styles) > 10:
        issues['high'].append(f"{relative_path}: {len(inline_styles)} inline style bulundu (CSS class kullan)")

    # 2. Mesaj gösterimi kontrolü
    if 'messages' in content and 'message-box' not in content and 'flash' not in content:
        issues['medium'].append(f"{relative_path}: Django messages var ama görsel gösterim eksik olabilir")

    # 3. Form kontrolü - label eksikliği
    input_tags = re.findall(r'<input[^>]*>', content)
    for inp in input_tags:
        if 'type="text"' in inp or 'type="email"' in inp or 'type="password"' in inp:
            # ID var mı kontrol et
            id_match = re.search(r'id="([^"]*)"', inp)
            if id_match:
                input_id = id_match.group(1)
                # Label var mı kontrol et
                if f'for="{input_id}"' not in content:
                    issues['medium'].append(f"{relative_path}: Input #{input_id} için label eksik")

    # 4. Buton stil tutarsızlığı
    buttons = re.findall(r'<(button|a)[^>]*class="[^"]*btn[^"]*"', content)
    if len(buttons) > 0:
        # btn-primary, btn-secondary kontrolü
        primary_count = content.count('btn-primary')
        secondary_count = content.count('btn-secondary')
        if primary_count > 3:
            issues['low'].append(f"{relative_path}: Çok fazla primary buton ({primary_count}) - öncelik karmaşası")

    # 5. Boş state kontrolü
    if ('{% for' in content or '{% if' in content) and 'Henüz' not in content and 'Bulunamadı' not in content and 'yok' not in content.lower():
        issues['low'].append(f"{relative_path}: Boş state mesajı eksik olabilir")

    # 6. Responsive tasarım
    if 'grid' in content and 'display: grid' in content and '@media' not in content:
        issues['medium'].append(f"{relative_path}: Grid kullanımı var ama responsive (@media) yok")

    # 7. Link hedefi (_blank güvenliği)
    blank_links = re.findall(r'<a[^>]*target="_blank"[^>]*>', content)
    for link in blank_links:
        if 'rel="noopener noreferrer"' not in link:
            issues['critical'].append(f"{relative_path}: target='_blank' güvenlik sorunu (rel eksik)")

    # 8. Accessibility - img alt kontrolü
    img_tags = re.findall(r'<img[^>]*>', content)
    for img in img_tags:
        if 'alt=' not in img:
            issues['medium'].append(f"{relative_path}: <img> tag'i alt attribute olmadan")

    # 9. Loading state
    if 'fetch(' in content or 'XMLHttpRequest' in content:
        if 'loading' not in content.lower() and 'spinner' not in content.lower():
            issues['medium'].append(f"{relative_path}: AJAX var ama loading göstergesi yok")

    # 10. Başlık hiyerarşisi
    h1_count = content.count('<h1')
    if h1_count > 1:
        issues['medium'].append(f"{relative_path}: Birden fazla <h1> ({h1_count}) - SEO ve erişilebilirlik sorunu")

    # 11. Tutarsız boşluklar
    if 'padding: 24px' in content and 'padding: 16px' in content and 'padding: 32px' in content:
        issues['low'].append(f"{relative_path}: Tutarsız padding değerleri (CSS değişkeni kullan)")

    # 12. Color tutarsızlığı
    hex_colors = re.findall(r'#[0-9A-Fa-f]{6}', content)
    if len(hex_colors) > 5:
        unique_colors = set(hex_colors)
        if len(unique_colors) > 8:
            issues['medium'].append(f"{relative_path}: {len(unique_colors)} farklı renk kodu (CSS değişkeni kullan)")

    # 13. Form submit düğmesi konumu
    if '<form' in content:
        if 'type="submit"' in content or '<button' in content:
            # Form'un sonunda mı kontrol et
            pass
        else:
            issues['medium'].append(f"{relative_path}: Form var ama submit butonu eksik")


def main():
    """Ana fonksiyon"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}")
    print("  🔍 DOKTRIN UX/UI AUDIT")
    print(f"{'='*70}{Colors.END}\n")

    # Template dosyalarını bul
    templates_dir = Path('/Users/ugurismail/Desktop/doktrin-project')
    template_files = []

    for pattern in ['*/templates/**/*.html', 'templates/**/*.html']:
        template_files.extend(templates_dir.glob(pattern))

    # venv hariç
    template_files = [f for f in template_files if 'venv' not in str(f)]

    print(f"{Colors.BLUE}📊 {len(template_files)} template dosyası bulundu{Colors.END}\n")

    # Her template'i kontrol et
    for template in sorted(template_files):
        check_template(str(template))

    # Sonuçları göster
    print(f"\n{Colors.BOLD}{'='*70}")
    print("  📋 AUDIT SONUÇLARI")
    print(f"{'='*70}{Colors.END}\n")

    total_issues = sum(len(v) for v in issues.values())

    if total_issues == 0:
        print(f"{Colors.GREEN}{Colors.BOLD}✅ Hiç sorun bulunamadı! Mükemmel!{Colors.END}\n")
        return

    # Kritik sorunlar
    if issues['critical']:
        print(f"{Colors.RED}{Colors.BOLD}🔴 KRİTİK SORUNLAR ({len(issues['critical'])}){Colors.END}")
        for issue in issues['critical'][:10]:  # İlk 10
            print(f"  • {issue}")
        if len(issues['critical']) > 10:
            print(f"  ... ve {len(issues['critical']) - 10} tane daha")
        print()

    # Yüksek öncelik
    if issues['high']:
        print(f"{Colors.YELLOW}{Colors.BOLD}🟠 YÜKSEK ÖNCELİK ({len(issues['high'])}){Colors.END}")
        for issue in issues['high'][:10]:
            print(f"  • {issue}")
        if len(issues['high']) > 10:
            print(f"  ... ve {len(issues['high']) - 10} tane daha")
        print()

    # Orta öncelik
    if issues['medium']:
        print(f"{Colors.CYAN}{Colors.BOLD}🟡 ORTA ÖNCELİK ({len(issues['medium'])}){Colors.END}")
        for issue in issues['medium'][:15]:
            print(f"  • {issue}")
        if len(issues['medium']) > 15:
            print(f"  ... ve {len(issues['medium']) - 15} tane daha")
        print()

    # Düşük öncelik
    if issues['low']:
        print(f"{Colors.WHITE}🔵 DÜŞÜK ÖNCELİK ({len(issues['low'])}){Colors.END}")
        for issue in issues['low'][:10]:
            print(f"  • {issue}")
        if len(issues['low']) > 10:
            print(f"  ... ve {len(issues['low']) - 10} tane daha")
        print()

    # Özet
    print(f"{Colors.BOLD}{'='*70}")
    print(f"  TOPLAM: {total_issues} sorun tespit edildi")
    print(f"{'='*70}{Colors.END}\n")

    # Öncelik sıralaması
    print(f"{Colors.BOLD}📊 ÖNCELİK DAĞILIMI:{Colors.END}")
    print(f"  🔴 Kritik: {len(issues['critical'])}")
    print(f"  🟠 Yüksek: {len(issues['high'])}")
    print(f"  🟡 Orta: {len(issues['medium'])}")
    print(f"  🔵 Düşük: {len(issues['low'])}")
    print()


if __name__ == '__main__':
    main()
