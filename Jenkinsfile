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

        // Python paths
        PYTHONPATH = "${WORKSPACE}/services/tenant_user-service/src"
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
                    bat '''
                        python -m venv venv
                        call venv\\Scripts\\activate.bat
                        python -m pip install --upgrade pip
                        pip install setuptools
                        cd services/tenant_user-service
                        pip install -r requirements.txt
                        pip install pytest pytest-cov
                        pip install -e .
                        cd ../..
                    '''
                }
            }
        }

        stage('Run Tests') {
            steps {
                script {
                    echo "Running tests..."
                    bat '''
                        call venv\\Scripts\\activate.bat
                        cd services/tenant_user-service
                        set PYTHONPATH=%PYTHONPATH%;%CD%\\src
                        python -m pytest tests/ -v --import-mode=append
                    '''
                }
            }
        }

        stage('Start Docker') {
            steps {
                script {
                    echo "Starting Docker service..."
                    bat '''
                        net start com.docker.service || exit 0
                        timeout /t 30
                    '''
                }
            }
        }

        stage('Build Docker Images') {
            steps {
                script {
                    echo "Building Docker images..."
                    bat """
                        docker build -t ${DOCKER_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG} -f services/tenant_user-service/Dockerfile .
                    """
                }
            }
        }

        stage('Push Docker Images') {
            steps {
                script {
                    echo "Pushing Docker images..."
                    withDockerRegistry([credentialsId: 'docker-registry-credentials', url: "https://index.docker.io/v1/"]) {
                        bat """
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
                    dir('infrastructure/terraform') {
                        bat 'terraform init -input=false'
                    }
                }
            }
        }

        stage('Terraform Plan') {
            steps {
                script {
                    echo "Planning Terraform changes..."
                    dir('infrastructure/terraform') {
                        bat 'terraform plan -out=tfplan -input=false'
                    }
                }
            }
        }

        stage('Terraform Apply') {
            steps {
                script {
                    echo "Applying Terraform changes..."
                    dir('infrastructure/terraform') {
                        bat 'terraform apply -auto-approve tfplan'
                    }
                }
            }
        }

        stage('Get Infrastructure Outputs') {
            steps {
                script {
                    echo "Retrieving infrastructure details..."
                    dir('infrastructure/terraform') {
                        def tfOutput = bat(
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
                dir('infrastructure/terraform') {
                    bat 'terraform destroy -auto-approve'
                }
            }
        }
        always {
            script {
                try {
                    bat "docker system prune -f"
                } catch (Exception e) {
                    echo "Warning: Docker cleanup failed, but continuing..."
                }
                cleanWs()
            }
        }
    }
} 