from setuptools import setup, find_packages
import os 

setup(
    name='gcpy',
    version='0.1.1',
    description='A python package for glow curve analysis',
    author='Florian Mentzel',
    author_email='florian.mentzel@tu-dortmund.com',
    license='LICENSE.txt',
    packages=['gcpy'],  
    package_data = {'gcpy': ['lib/*']},
    install_requires=[
        "resource", # should be preinstalled
        "numpy", "scipy", "matplotlib", "pandas", # mostly preinstalled
        "tinydb >= 3.13.0",
        "numba >= 0.43",
        "peakutils",
        "uncertainties"
    ], #external packages as dependencies
    test_suite='nose.collector',
    tests_require=['nose']  
)
