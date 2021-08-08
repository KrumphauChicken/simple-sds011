import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="simple-sds011",
    author="Brian Frick",
    version="0.0.7",
    description="A minimal library for SDS011 particulate sensors.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url ="https://github.com/krumphauchicken/simple-sds011",
    license="LICENSE.txt",
    packages=["simple_sds011"],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Scientific/Engineering :: Atmospheric Science",
    ],
    install_requires=[
        "pyserial >= 3.0",
    ],
)
