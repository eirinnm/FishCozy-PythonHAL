from setuptools import setup

setup(
    name='FishCozyHAL',
    version='1.0',
    description='Hardware abstraction layer for the FishCozy',
    author='Eirinn Mackay',
    author_email='e.mackay@ucl.ac.uk',
    packages=['FishCozyHAL'],  # same as name
    install_requires=['pyserial'],  # external packages as dependencies
)
