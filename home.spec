# home.spec
# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

# Defina o caminho do diretório base diretamente
BASE_DIR = Path("C:/Users/Guilherme/Documents/Nova pasta/projeto_licitacao360/licitacao360")

# Adicione o caminho do diretório base ao sys.path
sys.path.insert(0, str(BASE_DIR))

# Importa o módulo diretorios
from diretorios import (
    DATABASE_DIR,
    ICONS_DIR,
    IMAGE_PATH,
    PLANEJAMENTO_DIR,
    TEMPLATE_PLANEJAMENTO_DIR,
    PASTA_TEMPLATE,
    RELATORIO_PATH,
    WEBDRIVER_DIR,
    TEMPLATE_DIR
)

block_cipher = None

a = Analysis(
    ['home.py'],
    pathex=[],
    binaries=[],
    datas=[
        (str(DATABASE_DIR), 'database'),
        (str(ICONS_DIR), 'icons'),
        (str(IMAGE_PATH), 'image'),
        (str(PLANEJAMENTO_DIR), 'planejamento'),
        (str(TEMPLATE_PLANEJAMENTO_DIR), 'planejamento/template'),
        (str(PASTA_TEMPLATE), 'template'),
        (str(RELATORIO_PATH), 'relatorio'),
        (str(WEBDRIVER_DIR), 'selenium'),
        (str(TEMPLATE_DIR), 'template'),
    ],
    hiddenimports=['psutil'],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='home',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='home',
)
