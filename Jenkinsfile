pipeline {
    agent any

    parameters {
        string(name: 'ENVIRONMENT', defaultValue: 'dev', description: 'Kustomize overlay to deploy (dev or prod)')
        string(name: 'IMAGE_TAG', defaultValue: 'latest', description: 'Docker image tag/version')
    }

    stages {
        stage('Clone Git repo') {
            steps {
                git branch: 'main', 
                url: 'https://github.com/Hemanth-gollapudi/application_services.git'
            }
        }
        stage('Build and Push Docker Image') {
            steps {
                script {
                    // Build the Docker image with the specified tag
                    sh "docker build -t application_services_app:${params.IMAGE_TAG} ./services/tenant_user-service"
                    // Optionally push to a registry (uncomment and set your registry)
                    // sh "docker tag application_services_app:${params.IMAGE_TAG} <your-registry>/application_services_app:${params.IMAGE_TAG}"
                    // sh "docker push <your-registry>/application_services_app:${params.IMAGE_TAG}"
                }
            }
        }
        stage('Build with Docker Compose') {
            steps {
                script {
                    sh 'docker-compose down || true'
                    // Use the tagged image for production, otherwise use local build
                    if (params.ENVIRONMENT == 'prod') {
                        sh "docker-compose -f docker-compose.yml up --build -d"
                    } else {
                        sh "docker-compose up --build -d"
                    }
                }
            }
        }
        stage('Deploy to Kubernetes') {
            steps {
                script {
                    sh "kubectl apply -k k8s/overlays/${params.ENVIRONMENT}"
                }
            }
        }
        stage('Verify Kubernetes Deployment') {
            steps {
                script {
                    sh '''
                    for dep in $(kubectl get deployments -n platform -o jsonpath="{.items[*].metadata.name}"); do
                        kubectl rollout status deployment/$dep -n platform
                    done
                    kubectl get all -n platform
                    '''
                }
            }
        }
    }
}