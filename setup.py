"""
Setup script for Bright Data SDK

This file provides backward compatibility for tools that don't support pyproject.toml.
The main configuration is in pyproject.toml following modern Python packaging standards.
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read version from __init__.py
def read_version():
    with open(os.path.join("brightdata", "__init__.py"), "r", encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("__version__"):
                return line.split('"')[1]
    return "1.0.0"

setup(
    name="brightdata-sdk",
    version=read_version(),
    author="Bright Data",
    author_email="support@brightdata.com",
    description="Python SDK for Bright Data Web Scraping and SERP APIs",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/brightdata/brightdata-sdk-python",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8", 
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: Indexing/Search",
    ],
    python_requires=">=3.7",
    install_requires=[
        "requests>=2.25.0",
        "python-dotenv>=0.19.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0.0",
            "pytest-cov>=2.10.0",
            "black>=21.0.0",
            "isort>=5.0.0",
            "flake8>=3.8.0",
        ],
    },
    keywords="brightdata, web scraping, proxy, serp, api, data extraction",
    project_urls={
        "Bug Reports": "https://github.com/brightdata/brightdata-sdk-python/issues",
        "Documentation": "https://github.com/brightdata/brightdata-sdk-python#readme",
        "Source": "https://github.com/brightdata/brightdata-sdk-python",
    },
)