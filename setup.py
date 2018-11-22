import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="devstack",
    version="0.1.6",
    author="Sandesh Gade",
    author_email="sandeshgade@gmail.com",
    description="A Micro Framework for Development Stacks",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/cyberbeast/devstack",
    install_requires=["terminaltables", "pyinquirer"],
    packages=['devstack'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
    ],
)
