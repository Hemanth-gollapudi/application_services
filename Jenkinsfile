pipeline {
    agent any

    parameters {
        string(name: 'ENVIRONMENT', defaultValue: 'dev', description: 'Kustomize overlay to deploy (dev or prod)')
    }

    stages {
        stage('Clone Git repo') {
            steps {
                git branch: 'main', 
                url: 'https://github.com/Hemanth-gollapudi/application_services.git'
            }
        }
        stage('Build with Docker Compose') {
            steps {
                script {
                    sh 'docker-compose down || true'
                    sh 'docker-compose up --build -d'
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
                    // Get all deployments in the platform namespace and check rollout status
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