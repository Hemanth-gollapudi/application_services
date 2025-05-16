pipeline {
    agent any

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
                    // Apply k8s manifests using kustomize for the dev environment
                    sh 'kubectl apply -k k8s/overlays/dev'
                }
            }
        }
        stage('Verify Kubernetes Deployment') {
            steps {
                script {
                    // Get all deployments in the default namespace and check rollout status
                    sh '''
                    for dep in $(kubectl get deployments -o jsonpath="{.items[*].metadata.name}" -n default); do
                        kubectl rollout status deployment/$dep -n default
                    done
                    kubectl get all -n default
                    '''
                }
            }
        }
    }
}