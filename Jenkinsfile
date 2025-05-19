pipeline {
    agent any

    environment {
        // Docker configuration
        DOCKER_REGISTRY = 'hemanthkumar21'  
        IMAGE_NAME = 'application_services_app'
        IMAGE_TAG = "${BUILD_NUMBER}"
        
        // Git repository url
        GIT_REPO = 'https://github.com/Hemanth-gollapudi/application_services.git'
        
        // AWS credentials and configuration
        AWS_ACCESS_KEY_ID = credentials('aws-access-key-id')
        AWS_SECRET_ACCESS_KEY = credentials('aws-secret-access-key')
        AWS_DEFAULT_REGION = 'us-east-1'
        
        // Terraform variables
        TF_VAR_key_name = 'application-services-key'
        TF_VAR_git_repo_url = "${GIT_REPO}"
        TF_VAR_app_port = '3000'
        TF_VAR_keycloak_port = '8081'
        
        // Kubernetes configuration
        KUBECONFIG = credentials('kubeconfig')
        K8S_NAMESPACE = 'application-services'
        
        // Application configuration
        APP_PORT = '3000'                                          // Application port
        KEYCLOAK_PORT = '8081'                                     // Keycloak port
        
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

        stage('Verify AWS Configuration') {
            steps {
                script {
                    echo "Verifying AWS configuration..."
                    try {
                        bat """
                            aws configure list
                            aws sts get-caller-identity
                        """
                    } catch (Exception e) {
                        error "AWS configuration verification failed: ${e.message}"
                    }
                }
            }
        }

        stage('Cleanup Existing Resources') {
            steps {
                script {
                    echo "Cleaning up existing resources..."
                    try {
                        // Clean up existing key pair
                        bat """
                            aws ec2 describe-key-pairs --key-names ${TF_VAR_key_name} 2>nul && (
                                aws ec2 delete-key-pair --key-name ${TF_VAR_key_name}
                                echo "Key pair deleted successfully"
                                sleep 10
                            ) || echo "Key pair doesn't exist"
                        """
                        
                        // Clean up existing security group
                        bat """
                            aws ec2 describe-security-groups --group-names application-services-sg 2>nul && (
                                aws ec2 delete-security-group --group-name application-services-sg
                                echo "Security group deleted successfully"
                                sleep 10
                            ) || echo "Security group doesn't exist"
                        """
                        
                        // Clean up Terraform state and files
                        dir('infrastructure/terraform') {
                            bat '''
                                if exist .terraform rmdir /s /q .terraform
                                if exist .terraform.lock.hcl del /f .terraform.lock.hcl
                                if exist *.tfstate del /f *.tfstate
                                if exist *.tfstate.* del /f *.tfstate.*
                                if exist tfplan del /f tfplan
                                if exist application-services-key.pem del /f application-services-key.pem
                            '''
                        }

                        // Wait for AWS to process deletions
                        echo "Waiting for AWS to process resource deletions..."
                        sleep 30
                    } catch (Exception e) {
                        echo "Warning: Cleanup encountered some issues: ${e.message}"
                        // Continue pipeline execution despite cleanup issues
                    }
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
                    retry(3) {
                        bat '''
                            net start com.docker.service || echo "Docker service already running"
                            ping -n 31 127.0.0.1 > nul
                            docker info || exit 1
                        '''
                    }
                }
            }
        }

        stage('Build Docker Images') {
            steps {
                script {
                    echo "Building Docker images..."
                    retry(2) {
                        bat """
                            docker version
                            echo "Building image: ${DOCKER_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
                            cd services/tenant_user-service
                            docker build --no-cache -t ${DOCKER_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG} -f Dockerfile ../.. || exit 1
                            cd ../..
                        """
                    }
                }
            }
        }

        stage('Push Docker Images') {
            steps {
                script {
                    echo "Pushing Docker images..."
                    withCredentials([usernamePassword(credentialsId: 'dockerhub-credentials', usernameVariable: 'DOCKER_USERNAME', passwordVariable: 'DOCKER_PASSWORD')]) {
                        bat """
                            docker login -u %DOCKER_USERNAME% -p %DOCKER_PASSWORD%
                            docker push ${DOCKER_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}
                            docker logout
                        """
                    }
                }
            }
        }

        stage('Create AWS Key Pair') {
            steps {
                script {
                    echo "Creating AWS key pair..."
                    try {
                        // First ensure the key pair is deleted
                        bat """
                            aws ec2 describe-key-pairs --key-names ${TF_VAR_key_name} 2>nul && (
                                aws ec2 delete-key-pair --key-name ${TF_VAR_key_name}
                                echo "Existing key pair deleted"
                                sleep 10
                            ) || echo "No existing key pair found"
                        """
                        
                        // Then create the new key pair
                        bat """
                            aws ec2 create-key-pair --key-name ${TF_VAR_key_name} --query 'KeyMaterial' --output text > ${TF_VAR_key_name}.pem
                            echo "Key pair created successfully"
                            sleep 10
                        """
                    } catch (Exception e) {
                        error "Failed to create key pair: ${e.message}"
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
                        
                        // Extract only the JSON part from the output (handles Windows bat output)
                        def jsonText = tfOutput.substring(tfOutput.indexOf('{'), tfOutput.lastIndexOf('}') + 1)
                        def outputs = readJSON text: jsonText
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
                        kubectl rollout status deployment/tenant-user-service -n ${K8S_NAMESPACE}
                    """
                }
            }
        }

        stage('Health Check') {
            steps {
                script {
                    echo "Performing health check..."
                    // Wait for the service to be ready
                    bat """
                        kubectl wait --for=condition=available --timeout=300s deployment/tenant-user-service -n ${K8S_NAMESPACE}
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
                echo "Pipeline failed! Cleaning up resources..."
                try {
                    dir('infrastructure/terraform') {
                        if (fileExists('.terraform')) {
                            bat 'terraform destroy -auto-approve'
                        }
                    }
                    
                    bat """
                        aws ec2 describe-key-pairs --key-names ${TF_VAR_key_name} 2>nul && (
                            aws ec2 delete-key-pair --key-name ${TF_VAR_key_name}
                            echo "Key pair deleted successfully"
                        ) || echo "Key pair doesn't exist"
                    """
                } catch (Exception e) {
                    echo "Warning: Cleanup during failure encountered issues: ${e.message}"
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