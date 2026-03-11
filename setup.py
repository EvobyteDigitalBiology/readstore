from setuptools import setup, find_packages
from readstore_basic.__version__ import __version__

setup(
    name="readstore-basic",
    version=__version__,
    author="Jonathan Alles",
    author_email="Jonathan.Alles@evo-byte.com",
    description="ReadStore Basic Is A Python Package For Managing FASTQ Files and NGS Projects",
    long_description=open("docs/readme.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/EvobyteDigitalBiology/readstore",
    packages=find_packages(exclude=["readstore_basic.backend.app.migrations"]),
    license="Apache Software License 2.0",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.12',
    install_requires=[
        'Django>=5.2.11',
        'djangorestframework>=3.16.1',
        'djangorestframework_simplejwt>=5.5.1',
        'requests>=2.32.4',
        'gunicorn>=23.0.0',
        'pysam>=0.23.3',
        'pyyaml>=6.0.2',
        'streamlit==1.54.0',
        'pydantic>=2.11.7',
        'pandas>=2.3.1',
        'openpyxl>=3.1.5',
        'st-styled>=0.3.0'
    ],
    entry_points={
        'console_scripts': [
            'readstore-server = readstore_basic.readstore_server:main'
        ]
    },
    exclude_package_data={
        "": ["*.pyc", "*.pyo", "*~"],
    },
    include_package_data=True
)