"""Setup configuration for snakeclaw package."""

from setuptools import setup, find_packages

setup(
    name="snakeclaw",
    version="0.1.0",
    author="Your Name",
    description="A simple Snake game for the terminal",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "snakeclaw=snakeclaw.game:main",
        ],
    },
    python_requires=">=3.12",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Games/Entertainment :: Arcade",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)