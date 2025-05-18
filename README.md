# Application Services

This repository contains a collection of microservices for managing tenant users and related services.

## Services

- **Tenant User Service**: A FastAPI-based service for managing tenant users
- **Keycloak Integration**: Authentication and authorization service
- **PostgreSQL Database**: Data persistence for tenant information

## Prerequisites

- Docker and Docker Compose
- Python 3.8+
- Kubernetes (for production deployment)
- Jenkins (for CI/CD)

## Quick Start

1. Copy the environment template:

   ```bash
   cp env.example .env
   ```

2. Start the services:

   ```bash
   docker-compose up -d
   ```

3. Run database migrations:

   ```bash
   docker-compose run migrate
   ```

4. Access the services:
   - Tenant User Service: http://localhost:8009
   - Keycloak Admin Console: http://localhost:8084
   - PostgreSQL: localhost:5434

## Development

The project uses:

- FastAPI for the REST API
- SQLAlchemy for database ORM
- Alembic for database migrations
- Python-Keycloak for Keycloak integration

## Deployment

The project supports multiple deployment environments:

- Development: `docker-compose up`
- Production: Kubernetes deployment via Jenkins pipeline

### Kubernetes Deployment

```bash
kubectl apply -k k8s/overlays/prod
```

## Project Structure

```
├── services/              # Microservices
│   └── tenant_user-service/   # Tenant management service
├── k8s/                   # Kubernetes configurations
├── docker/               # Docker related files
├── infrastructure/       # Infrastructure as code
├── monitoring/          # Monitoring configurations
├── docs/                # Documentation
└── tools/               # Development tools
```

## License

See [LICENSE](LICENSE) file for details.
