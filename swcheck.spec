# linkcheck.spec
a = Analysis(
    ['swcheck.py'],  # Entry point: GUI script
    pathex=['.'],
    datas=[
        ('main.py', '.'),
        ('Icon1.ico', '.'),
        ('classes', 'classes'),
        ('com_table_sample.xlsx', '.'),
    ],
    binaries=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='swcheck',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Hides terminal window
    icon='Icon1.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    console=False,
    name='swcheck'
)