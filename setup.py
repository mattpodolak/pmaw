import setuptools
import re

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

VERSION_FILE = "pmaw/__init__.py"
with open(VERSION_FILE) as version_file:
    match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                      version_file.read(), re.MULTILINE)

if match:
    version = match.group(1)
else:
    raise RuntimeError(f"Unable to find version string in {VERSION_FILE}.")

setuptools.setup(
    name="pmaw",
    version=version,
    author="Matthew Podolak",
    author_email="mpodola2@gmail.com",
    description="A multithread Pushshift.io API Wrapper for reddit.com comment and submission searches.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mattpodolak/pmaw",
    packages=setuptools.find_packages(),
    license='MIT License',
    install_requires=['requests'],
    keywords='reddit api wrapper pushshift multithread data collection cache',
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3 :: Only",
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        "Intended Audience :: Developers",
        "Topic :: Utilities",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.5',
)
