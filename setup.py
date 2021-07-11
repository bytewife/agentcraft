from setuptools import setup

if __name__ == '__main__':
    setup(
        name='agentcraft',
        description='Settlement Generator + Agent Simulation in Minecraft',
        license='MIT',
        url="https://github.com/aith/agentcraft",
        python_requires=">=3.9",
        install_requires=["bitarray", "numpy", "names", "nbt", "requests", "scipy", "wonderwords"],
    )
