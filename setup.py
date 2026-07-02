from setuptools import setup, find_packages

setup(
    name="moon_core",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "openai>=1.0.0",
        "python-dotenv",
    ],
    author="iMoon",
    description="Core backend library for the MoonAI Toolkit ecosystem",
)
