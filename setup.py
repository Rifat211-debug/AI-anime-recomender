
from pathlib import Path
from setuptools import setup, find_packages

ROOT = Path(__file__).parent

with open(ROOT / "requirements.txt", encoding="utf-8-sig") as f:
    requirements = [
        line.strip()
        for line in f
        if line.strip() and not line.strip().startswith("#")
    ]

setup(
    name="anime-recommender",
    version="0.1.0",
    packages=find_packages(),
    install_requires=requirements,
)
