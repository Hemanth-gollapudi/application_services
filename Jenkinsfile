pipeline {
    agent any

    stages {
        stage('clone Git repo') {
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
    }
}