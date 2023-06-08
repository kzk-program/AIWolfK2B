import setuptools
import pathlib


with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="aiwolfk2b",
    version="0.0.2",
    install_requires=pathlib.Path('requirements.txt').read_text(encoding="utf-8").splitlines(),
    author="Takuya Okubo",
    description="python agents that can play Werewolf, following the specifications of the AIWolf Project",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kzk-program/AIWolfK2B",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)