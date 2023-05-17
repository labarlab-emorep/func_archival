from setuptools import setup, find_packages

exec(open("func_archival/_version.py").read())

setup(
    name="func_archival",
    version=__version__,  # noqa: F821
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "func_archival=func_archival.cli:main",
        ]
    },
    install_requires=["setuptools>=65.6.3"],
)
