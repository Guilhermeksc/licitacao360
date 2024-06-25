# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\Users\\Guilherme\\Documents\\Nova pasta\\projeto_licitacao360\\licitacao360\\home.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Users\\Guilherme\\Documents\\Nova pasta\\projeto_licitacao360\\licitacao360\\database', 'database'), ('C:\\Users\\Guilherme\\Documents\\Nova pasta\\projeto_licitacao360\\licitacao360\\database\\icons', 'database/icons'), ('C:\\Users\\Guilherme\\Documents\\Nova pasta\\projeto_licitacao360\\licitacao360\\database\\image', 'database/image'), ('C:\\Users\\Guilherme\\Documents\\Nova pasta\\projeto_licitacao360\\licitacao360\\modules\\planejamento', 'planejamento'), ('C:\\Users\\Guilherme\\Documents\\Nova pasta\\projeto_licitacao360\\licitacao360\\modules\\planejamento\\template', 'planejamento/template'), ('C:\\Users\\Guilherme\\Documents\\Nova pasta\\projeto_licitacao360\\licitacao360\\database\\template', 'database/template'), ('C:\\Users\\Guilherme\\Documents\\Nova pasta\\projeto_licitacao360\\licitacao360\\database\\relatorio', 'database'), ('C:\\Users\\Guilherme\\Documents\\Nova pasta\\projeto_licitacao360\\licitacao360\\database\\selenium', 'database/selenium'), ('C:\\Users\\Guilherme\\Documents\\Nova pasta\\projeto_licitacao360\\licitacao360\\database\\template', 'database/template')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
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
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['C:\\Users\\Guilherme\\Documents\\Nova pasta\\projeto_licitacao360\\licitacao360\\database\\icons\\icone.ico'],
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
