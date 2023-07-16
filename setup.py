import setuptools

setuptools.setup(
    name="oxenfree",
    version="0.0",
    packages=setuptools.find_packages(where='src'),
    package_dir={'': 'src'},
    python_requires=">=3.9",
    install_requires=[
        'deepl',
        'UnityPy'
    ],
    entry_points=dict(
        console_scripts=[
            'analyze_jsons = oxenfree.bin.analyze_jsons:_main',
            'autotranslate_jsons = oxenfree.bin.autotranslate_jsons:_main',
            'prepare_jsons = oxenfree.bin.prepare_jsons:_main',
            'repack_bundle = oxenfree.bin.repack_bundle:_main',
            'unpack_bundle = oxenfree.bin.unpack_bundle:_main',
        ]
    ),
    extras_require={
        'dev': [
            'mypy',
            'pip3-autoremove',
            # 'pyinstaller',
        ],
    }
)
