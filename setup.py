from setuptools import setup

setup(
    name='pongo',
    version='1.1',
    description='Controller for the Pongo music server',
    author="Marc Culler",
    author_email="",
    url='http://marc-culler.info/pongo',
    install_requires=['spotipy >= 2.3.7', 'zeroconf >= 0.20.0'],
    entry_points = {'console_scripts': ['pongo = pongo.app:main']},
    license='GPL',
    packages=['pongo'])
