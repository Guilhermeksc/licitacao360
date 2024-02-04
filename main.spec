# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Users\\User\\Desktop\\pyqt6\\database', 'database'), ('C:\\Users\\User\\Desktop\\pyqt6\\database\\icons', 'database/icons'), ('C:\\Users\\User\\Desktop\\pyqt6\\database\\image', 'database/image'), ('C:\\Users\\User\\Desktop\\pyqt6\\database\\pasta_pdf', 'database/pasta_pdf'), ('C:\\Users\\User\\Desktop\\pyqt6\\database\\pasta_sicaf', 'database/pasta_sicaf'), ('C:\\Users\\User\\Desktop\\pyqt6\\database\\template', 'database/template'), ('C:\\Users\\User\\Desktop\\pyqt6\\database\\pasta_sicaf\\sicaf_txt', 'database/pasta_sicaf/sicaf_txt'), ('C:\\Users\\User\\Desktop\\pyqt6\\database\\pasta_pdf\\homolog_txt', 'database/pasta_pdf/homolog_txt'), ('C:\\Users\\User\\Desktop\\pyqt6\\database\\relatorio', 'database/relatorio'), ('C:\\Users\\User\\Desktop\\pyqt6\\database\\Nova pasta', 'database/Nova pasta'), ('C:\\Users\\User\\Desktop\\pyqt6\\database\\Nova pasta', 'database/Nova pasta')],
    hiddenimports=['PyQt6', 'qdarkstyle', 'pdfplumber', 'openpyxl'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='main',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='main',
)
