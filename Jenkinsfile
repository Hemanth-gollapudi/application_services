pipeline {
    agent any

    environment {
        // Docker configuration
        DOCKER_REGISTRY = 'hemanthkumar21'  
        IMAGE_NAME = 'application_services_app'
        IMAGE_TAG = "${BUILD_NUMBER}"
        
        // Git repository
        GIT_REPO = 'https://github.com/Hemanth-gollapudi/application_services.git'
        
        // AWS credentials and configuration
        AWS_ACCESS_KEY_ID = credentials('aws-access-key-id')
        AWS_SECRET_ACCESS_KEY = credentials('aws-secret-access-key')
        AWS_DEFAULT_REGION = 'us-east-1'
        
        // Terraform variables
        TF_VAR_key_name = 'application-services-key'
        TF_VAR_git_repo_url = "${GIT_REPO}"
        
        // Kubernetes configuration
        KUBECONFIG = credentials('kubeconfig')
        K8S_NAMESPACE = 'application-services'
        
        // Application configuration
        APP_PORT = '8009'                                          // Application port
        KEYCLOAK_PORT = '8084'                                     // Keycloak port
        
        // Database configuration (if needed)
        POSTGRES_DB = credentials('postgres-db-name')              // Jenkins credentials ID for DB name
        POSTGRES_USER = credentials('postgres-username')           // Jenkins credentials ID for DB username
        POSTGRES_PASSWORD = credentials('postgres-password')       // Jenkins credentials ID for DB password
    }

    stages {
        stage('Clone Repository') {
            steps {
                script {
                    // Clean workspace before cloning
                    cleanWs()
                    echo "Cloning repository..."
                    git branch: 'main',
                        url: "${env.GIT_REPO}"
                }
            }
        }

        stage('Setup Python Environment') {
            steps {
                script {
                    echo "Setting up Python environment..."
                    // Create and activate virtual environment
                    sh '''
                        python -m venv venv
                        . venv/bin/activate
                        pip install -r services/tenant_user-service/requirements.txt
                    '''
                }
            }
        }

        stage('Run Tests') {
            steps {
                script {
                    echo "Running tests..."
                    sh '''
                        . venv/bin/activate
                        cd services/tenant_user-service
                        python -m pytest tests/
                    '''
                }
            }
        }

        stage('Build Docker Images') {
            steps {
                script {
                    echo "Building Docker images..."
                    // Build the main application image
                    sh """
                        docker build -t ${DOCKER_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG} \
                            -f services/tenant_user-service/Dockerfile .
                    """
                }
            }
        }

        stage('Push Docker Images') {
            steps {
                script {
                    echo "Pushing Docker images..."
                    withDockerRegistry([credentialsId: 'docker-registry-credentials', url: "https://${DOCKER_REGISTRY}"]) {
                        sh """
                            docker push ${DOCKER_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}
                        """
                    }
                }
            }
        }

        stage('Initialize Terraform') {
            steps {
                script {
                    echo "Initializing Terraform..."
                    withCredentials([
                        string(credentialsId: 'aws-access-key-id', variable: 'AWS_ACCESS_KEY_ID'),
                        string(credentialsId: 'aws-secret-access-key', variable: 'AWS_SECRET_ACCESS_KEY')
                    ]) {
                        dir('infrastructure/terraform') {
                            sh '''
                                terraform init -input=false
                            '''
                        }
                    }
                }
            }
        }

        stage('Terraform Plan') {
            steps {
                script {
                    echo "Planning Terraform changes..."
                    withCredentials([
                        string(credentialsId: 'aws-access-key-id', variable: 'AWS_ACCESS_KEY_ID'),
                        string(credentialsId: 'aws-secret-access-key', variable: 'AWS_SECRET_ACCESS_KEY')
                    ]) {
                        dir('infrastructure/terraform') {
                            sh '''
                                terraform plan -out=tfplan -input=false
                            '''
                        }
                    }
                }
            }
        }

        stage('Terraform Apply') {
            steps {
                script {
                    echo "Applying Terraform changes..."
                    withCredentials([
                        string(credentialsId: 'aws-access-key-id', variable: 'AWS_ACCESS_KEY_ID'),
                        string(credentialsId: 'aws-secret-access-key', variable: 'AWS_SECRET_ACCESS_KEY')
                    ]) {
                        dir('infrastructure/terraform') {
                            sh '''
                                terraform apply -auto-approve tfplan
                            '''
                        }
                    }
                }
            }
        }

        stage('Get Infrastructure Outputs') {
            steps {
                script {
                    echo "Retrieving infrastructure details..."
                    dir('infrastructure/terraform') {
                        def tfOutput = sh(
                            script: 'terraform output -json',
                            returnStdout: true
                        ).trim()
                        
                        def outputs = readJSON text: tfOutput
                        env.EC2_PUBLIC_IP = outputs.instance_public_ip.value
                        env.APPLICATION_URL = outputs.application_url.value
                    }
                }
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                script {
                    echo "Deploying to Kubernetes..."
                    // Update Kubernetes manifests with new image tag
                    sh """
                        sed -i 's|image: ${DOCKER_REGISTRY}/${IMAGE_NAME}:.*|image: ${DOCKER_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}|' k8s/overlays/prod/deployment.yaml
                    """
                    
                    // Apply Kubernetes configurations
                    sh """
                        kubectl apply -k k8s/overlays/prod
                        kubectl rollout status deployment/tenant-user-service -n application-services
                    """
                }
            }
        }

        stage('Health Check') {
            steps {
                script {
                    echo "Performing health check..."
                    // Wait for the service to be ready
                    sh """
                        kubectl wait --for=condition=available --timeout=300s \
                            deployment/tenant-user-service -n application-services
                    """
                }
            }
        }
    }

    post {
        success {
            echo """
                Pipeline completed successfully!
                Application is available at: ${env.APPLICATION_URL}
                EC2 Instance IP: ${env.EC2_PUBLIC_IP}
            """
        }
        failure {
            script {
                echo "Pipeline failed! Destroying Terraform infrastructure..."
                withCredentials([
                    string(credentialsId: 'aws-access-key-id', variable: 'AWS_ACCESS_KEY_ID'),
                    string(credentialsId: 'aws-secret-access-key', variable: 'AWS_SECRET_ACCESS_KEY')
                ]) {
                    dir('infrastructure/terraform') {
                        sh 'terraform destroy -auto-approve'
                    }
                }
            }
        }
        always {
            // Clean up resources
            sh "docker system prune -f"
            cleanWs()
        }
    }
} 