from setuptools import setup, find_packages

setup(
    name="shipay-backend",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.115.0",
        "uvicorn>=0.34.0",
        "sqlalchemy>=2.0.40",
        "httpx>=0.28.0",
        "requests>=2.32.0",
        "redis>=5.2.0",
        "kafka-python>=2.1.5",
        "prometheus-client>=0.21.0",
    ],
    extras_require={
        "dev": [
            "pytest>=8.3.0",
            "pytest-asyncio>=0.26.0",
            "pytest-cov>=6.1.0",
        ]
    }
) 