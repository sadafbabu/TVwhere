from setuptools import setup, find_packages

setup(
    name="tvwhere",
    version="2.1.0",
    description="Minimalist cross-platform IPTV player",
    author="Sadaf",
    license="MIT",
    packages=find_packages(),
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "tvwhere=tvwhere.__main__:main",
        ],
    },
    python_requires=">=3.8",
)
