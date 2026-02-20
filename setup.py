from setuptools import setup, find_packages

setup(
    name="aion-bot",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "websockets>=12.0",
        "httpx>=0.27.0",
        "python-dotenv>=1.0.0",
        "scipy>=1.11.0",
        "numpy>=1.24.0",
        "loguru>=0.7.0",
        "python-dateutil>=2.8.2",
        "py-clob-client>=0.15.0",
    ],
    entry_points={
        "console_scripts": [
            "aion-bot=trading_bot.main:main",
        ],
    },
    python_requires=">=3.11",
)
