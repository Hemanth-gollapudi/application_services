from setuptools import setup, find_packages

setup(
    name="tenant_user_service",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "fastapi>=0.100,<0.101",
        "uvicorn[standard]>=0.23,<0.24",
        "psycopg2-binary>=2.9,<3.0",
        "python-keycloak>=2.0,<3.0",
        "SQLAlchemy>=2.0,<2.1",
        "alembic>=1.11,<1.12",
        "python-dotenv",
        "hvac>=2.3.0",
        "pydantic>=1.10,<2.0",
        "PyYAML>=6.0"
    ],
    python_requires=">=3.8",
) 