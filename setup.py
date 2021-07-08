import os
from setuptools import setup, Extension

SRC_DIR = "src/"
CPP_DIR = "src/cpp/"
BUILD_DIR = "build/" # whatever is specified in the CLI


if __name__ == '__main__':
    setup(
        name='agentcraft',
        description='Settlement Generator + Agent Simulation',
        license='BSD',
        ext_modules=[Extension('movement', [CPP_DIR + 'movement.cpp'],
                               include_dirs=[CPP_DIR],  # For headers I believe
                               # library_dirs=[],
                               # libraries=[],
                               # runtime_library_dirs = [],
                               )],
    )



