#!/usr/bin/env python3
"""
Streamlit başlatıcı - Heredoc ile çalışır
"""
import sys
import os

# venv site-packages'i path'e ekle
venv_site_packages = '/Users/berhankiyanus/Desktop/Finance/venv/lib/python3.14/site-packages'
if os.path.exists(venv_site_packages):
    sys.path.insert(0, venv_site_packages)

# Çalışma dizinini ayarla
os.chdir('/Users/berhankiyanus/Desktop/Finance')

# Streamlit'i import et ve çalıştır
try:
    from streamlit.web.cli import main
    sys.argv = ['streamlit', 'run', 'app.py']
    main()
except ImportError as e:
    print(f"❌ Streamlit import hatası: {e}")
    print(f"Python path: {sys.path[:3]}")
    sys.exit(1)

