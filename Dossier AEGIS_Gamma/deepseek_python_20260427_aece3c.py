from setuptools import setup, find_packages

setup(
    name="aegis-gamma",
    version="4.0.0",
    author="Votre Nom",
    author_email="votre.email@example.com",
    description="Système de contrôle narratif pour la détection de brouillage informationnel",
    long_description=open("README.md", "r", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/votrecompte/aegis-gamma",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.11",
    install_requires=[
        "numpy>=1.24.0",
        "matplotlib>=3.7.0",
    ],
    extras_require={
        "ml": ["torch>=2.0.0", "transformers>=4.30.0"],
        "dev": ["pytest>=7.4.0", "pytest-cov>=4.1.0", "black>=23.0.0"],
        "all": ["torch>=2.0.0", "transformers>=4.30.0", "pytest>=7.4.0"],
    },
    entry_points={
        "console_scripts": [
            "aegis=aegis_gamma.cli.main:main",
        ],
    },
)