#!/usr/bin/env python3
"""
Streamlit başlatma scripti - Python path sorunlarını çözer
"""
import sys
import os

# venv site-packages'i path'e ekle
venv_site_packages = '/Users/berhankiyanus/Desktop/Finance/venv/lib/python3.14/site-packages'
if os.path.exists(venv_site_packages):
    sys.path.insert(0, venv_site_packages)

# Streamlit'i import et ve çalıştır
from streamlit.web.cli import main

if __name__ == '__main__':
    # Çalışma dizinini proje kök dizinine ayarla
    os.chdir('/Users/berhankiyanus/Desktop/Finance')
    
    # Streamlit'i başlat
    sys.argv = ['streamlit', 'run', 'app.py']
    main()

