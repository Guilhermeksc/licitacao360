# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['home.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Users\\User\\OneDrive\\Área de Trabalho\\Programa PYQT6\\pyqt6\\database', 'database'), ('C:\\Users\\User\\OneDrive\\Área de Trabalho\\Programa PYQT6\\pyqt6\\database\\icons', 'database/icons'), ('C:\\Users\\User\\OneDrive\\Área de Trabalho\\Programa PYQT6\\pyqt6\\database\\image', 'database/image'), ('C:\\Users\\User\\OneDrive\\Área de Trabalho\\Programa PYQT6\\pyqt6\\planejamento', 'planejamento'), ('C:\\Users\\User\\OneDrive\\Área de Trabalho\\Programa PYQT6\\pyqt6\\planejamento\\template', 'planejamento/template'), ('C:\\Users\\User\\OneDrive\\Área de Trabalho\\Programa PYQT6\\pyqt6\\database\\template', 'database/template'), ('C:\\Users\\User\\OneDrive\\Área de Trabalho\\Programa PYQT6\\pyqt6\\database\\relatorio', 'database'), ('C:\\Users\\User\\OneDrive\\Área de Trabalho\\Programa PYQT6\\pyqt6\\database\\Nova pasta', 'database/Nova pasta'), ('C:\\Users\\User\\OneDrive\\Área de Trabalho\\Programa PYQT6\\pyqt6\\database\\Nova pasta', 'database/Nova pasta'), ('C:\\Users\\User\\OneDrive\\Área de Trabalho\\Programa PYQT6\\pyqt6\\database\\selenium', 'database/selenium'), ('C:\\Users\\User\\OneDrive\\Área de Trabalho\\Programa PYQT6\\pyqt6\\database\\template', 'database/template'), ('C:\\Users\\User\\OneDrive\\Área de Trabalho\\Programa PYQT6\\pyqt6\\database\\template\\comunicacao_padronizada', 'database/template/comunicacao_padronizada'), ('C:\\Users\\User\\OneDrive\\Área de Trabalho\\Programa PYQT6\\pyqt6\\database\\template\\relatorio_controle_pregao', 'database/template/relatorio_controle_pregao'), ('C:\\Users\\User\\OneDrive\\Área de Trabalho\\Programa PYQT6\\pyqt6\\controle_contratos', 'controle_contratos'), ('C:\\Users\\User\\OneDrive\\Área de Trabalho\\Programa PYQT6\\pyqt6\\controle_contratos\\data_contratos', 'controle_contratos/data_contratos'), ('C:\\Users\\User\\OneDrive\\Área de Trabalho\\Programa PYQT6\\pyqt6\\controle_contratos\\comunicacao_padronizada', 'controle_contratos/comunicacao_padronizada')],
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
    name='licitacao360',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['C:\\Users\\User\\OneDrive\\Área de Trabalho\\Programa PYQT6\\pyqt6\\database\\icons\\icone.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='licitacao360',
)