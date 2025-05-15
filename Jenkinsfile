pipeline {
    agent any

    // environment {
        // Load environment variables from .env if needed
        // Uncomment the next line if you want to export .env variables
        // ENV_FILE = '.env'
    // }

    stages {
        stage('Checkout') {
            steps {
                // Checkout the code from the current Git repository
                checkout scm
            }
        }

        stage('Build with Docker Compose') {
            steps {
                script {
                    // Optionally, clean up previous containers
                    sh 'docker-compose down || true'
                    // Build and start the services
                    sh 'docker-compose up --build -d'
                }
            }
        }
    }

    post {
        always {
            // Optionally, show running containers for debugging
            sh 'docker ps -a'
        }
    }
}