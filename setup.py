from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()

# Get the long description from the README file
long_description = (here / "README.rst").read_text(encoding="utf-8")


setup(
    name='tbgclient',
    version='0.6.0-alpha',
    description='Provides a way to get, post, and modify posts on the TBGs.',
    long_description=long_description,
    author='Gilbert189',
    author_email='gilbertdannellelo@gmail.com',
    packages=find_packages(),  # same as name
    install_requires=['requests', 'beautifulsoup4'],
)
