from setuptools import setup

setup(
    name='gcpy',
    version='0.1.0',
    description='A python package for glow curve analysis',
    author='Florian Mentzel',
    author_email='florian.mentzel@tu-dortmund.com',
    license='LICENSE.txt',
    packages=['gcpy'],  #same as name
    install_requires=[
        "tinydb >= 3.13.0",
        "scipy >= 1.2.1",
        "numba >= 0.43",
        "peakutils"
    ], #external packages as dependencies
    test_suite='nose.collector',
    tests_require=['nose']  
)
