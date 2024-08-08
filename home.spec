# home.spec
# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_all

# Defina o caminho do diretório base diretamente
BASE_DIR = Path("C:/Users/Guilherme/Documents/Nova pasta/projeto_licitacao360/licitacao360")
DATABASE_DIR = BASE_DIR / "database"
RESOURCES_DIR = BASE_DIR / "resources"
ICON_PATH = RESOURCES_DIR / "brasil.ico"

# Adicione o caminho do diretório base ao sys.path
sys.path.insert(0, str(BASE_DIR))

block_cipher = None

a = Analysis(
    ['home.py'],
    pathex=[str(BASE_DIR)],
    binaries=[],
    datas=[],  # Removido datas individuais
    hiddenimports=['psutil', 'fitz'],
    hookspath=['.'],  # Adicione o caminho atual para procurar hooks personalizados
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

# Inclua os diretórios database e resources inteiros
a.datas += Tree(str(DATABASE_DIR), prefix='database/')
a.datas += Tree(str(RESOURCES_DIR), prefix='resources/')

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='licitacao360',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    icon=str(ICON_PATH) 
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='licitacao360',
)