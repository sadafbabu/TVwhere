from setuptools import setup, find_packages

setup(
    name="tvwhere",
    version="1.0.0",
    description="Minimalist IPTV Player",
    author="Sadaf",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "tvwhere=tvwhere.__main__:main",
        ],
    },
    python_requires=">=3.8",
)
