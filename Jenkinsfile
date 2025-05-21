pipeline {
    agent any

    environment {
        DOCKER_REGISTRY = 'hemanthkumar21'  
        IMAGE_NAME = 'application_services_app'
        IMAGE_TAG = "${BUILD_NUMBER}"
        
        GIT_REPO = 'https://github.com/Hemanth-gollapudi/application_services.git'
        
        AWS_ACCESS_KEY_ID = credentials('aws-access-key-id')
        AWS_SECRET_ACCESS_KEY = credentials('aws-secret-access-key')
        AWS_DEFAULT_REGION = 'us-east-1'
        
        KEY_NAME = "application-services-key-${BUILD_NUMBER}"
        TF_VAR_git_repo_url = "${GIT_REPO}"
        TF_VAR_app_port = '3000'
        TF_VAR_keycloak_port = '8081'
        
        EKS_CLUSTER_NAME = "application-services-cluster"
        EKS_NODE_GROUP_NAME = "application-services-nodes"
        EKS_NODE_TYPE = "t3.medium"
        EKS_NODE_MIN = "2"
        EKS_NODE_MAX = "4"
        EKS_NODE_DESIRED = "2"
        
        APP_PORT = '3000'
        KEYCLOAK_PORT = '8081'
        
        POSTGRES_DB = credentials('postgres-db-name')
        POSTGRES_USER = credentials('postgres-username')
        POSTGRES_PASSWORD = credentials('postgres-password')

        PYTHONPATH = "${WORKSPACE}/services/tenant_user-service/src"
    }

    stages {
        stage('Clone Repository') {
            steps {
                script {
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
                        bat """
                            aws ec2 describe-vpcs --filters "Name=tag:Name,Values=application-services-vpc" --query 'Vpcs[*].VpcId' --output text | foreach-object {
                                $vpcId = $_
                                
                                aws ec2 describe-internet-gateways --filters "Name=attachment.vpc-id,Values=$vpcId" --query 'InternetGateways[*].InternetGatewayId' --output text | foreach-object {
                                    aws ec2 detach-internet-gateway --internet-gateway-id $_ --vpc-id $vpcId
                                    aws ec2 delete-internet-gateway --internet-gateway-id $_
                                }
                                
                                aws ec2 describe-subnets --filters "Name=vpc-id,Values=$vpcId" --query 'Subnets[*].SubnetId' --output text | foreach-object {
                                    aws ec2 delete-subnet --subnet-id $_
                                }
                                
                                aws ec2 describe-route-tables --filters "Name=vpc-id,Values=$vpcId" --query 'RouteTables[*].RouteTableId' --output text | foreach-object {
                                    aws ec2 delete-route-table --route-table-id $_
                                }
                                
                                aws ec2 describe-security-groups --filters "Name=vpc-id,Values=$vpcId" --query 'SecurityGroups[*].GroupId' --output text | foreach-object {
                                    aws ec2 delete-security-group --group-id $_
                                }
                                
                                aws ec2 describe-network-acls --filters "Name=vpc-id,Values=$vpcId" --query 'NetworkAcls[*].NetworkAclId' --output text | foreach-object {
                                    aws ec2 delete-network-acl --network-acl-id $_
                                }
                                
                                aws ec2 delete-vpc --vpc-id $vpcId
                            }
                            
                            timeout /t 60 /nobreak
                        """
                        
                        bat """
                            aws ec2 describe-security-groups --group-names application-services-sg 2>nul && (
                                aws ec2 delete-security-group --group-name application-services-sg
                                echo "Security group deleted successfully"
                                sleep 10
                            ) || echo "Security group doesn't exist"
                        """
                        
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

                        sleep 30
                    } catch (Exception e) {
                        echo "Warning: Cleanup encountered some issues: ${e.message}"
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
                            docker-compose down --rmi all || echo "No existing containers to clean up"
                            docker system prune -f || echo "No images to prune"
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
                            echo Building image: ${DOCKER_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}
                            docker-compose build --no-cache app
                            
                            docker image inspect ${DOCKER_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG} || exit 1
                            docker image inspect ${DOCKER_REGISTRY}/${IMAGE_NAME}:latest || exit 1
                            
                            docker tag ${DOCKER_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG} ${DOCKER_REGISTRY}/${IMAGE_NAME}:latest
                            
                            docker images | findstr "${DOCKER_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}" || exit 1
                            docker images | findstr "${DOCKER_REGISTRY}/${IMAGE_NAME}:latest" || exit 1
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
                            echo Logging in to Docker Hub...
                            docker login -u %DOCKER_USERNAME% -p %DOCKER_PASSWORD% || exit 1
                            
                            
                            echo Pushing latest tag: ${DOCKER_REGISTRY}/${IMAGE_NAME}:latest
                            docker push ${DOCKER_REGISTRY}/${IMAGE_NAME}:latest || exit 1
                            
                            docker logout
                        """
                    }
                }
            }
        }

        stage('Verify Docker Image') {
            steps {
                script {
                    echo "Verifying Docker image..."
                    bat """
                        docker pull ${DOCKER_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG} || exit 1
                        docker pull ${DOCKER_REGISTRY}/${IMAGE_NAME}:latest || exit 1
                        
                        docker run -d -p 8009:8000 --name test-${IMAGE_NAME}-version ${DOCKER_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG} || exit 1
                        timeout /t 10 /nobreak
                        docker ps | findstr "test-${IMAGE_NAME}-version" || exit 1
                        docker logs test-${IMAGE_NAME}-version
                        
                        docker run -d -p 8010:8000 --name test-${IMAGE_NAME}-latest ${DOCKER_REGISTRY}/${IMAGE_NAME}:latest || exit 1
                        timeout /t 10 /nobreak
                        docker ps | findstr "test-${IMAGE_NAME}-latest" || exit 1
                        docker logs test-${IMAGE_NAME}-latest
                        
                        docker rm -f test-${IMAGE_NAME}-version test-${IMAGE_NAME}-latest
                    """
                }
            }
        }

        stage('Create AWS Key Pair') {
            steps {
                script {
                    echo "Creating AWS key pair..."
                    try {
                        dir('infrastructure/terraform') {
                            bat 'terraform init -input=false'

                            bat """
                                terraform apply -auto-approve -var="key_name=%KEY_NAME%" -target=tls_private_key.app_private_key -target=local_file.private_key -target=aws_key_pair.app_key_pair
                                if errorlevel 1 (
                                    exit 1
                                )
                            """

                            bat """
                                if not exist %KEY_NAME%.pem (
                                    exit 1
                                )
                            """
                        }
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
                        bat 'terraform plan -out=tfplan -input=false -var="key_name=%KEY_NAME%"'
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
                        
                        def jsonText = tfOutput.substring(tfOutput.indexOf('{'), tfOutput.lastIndexOf('}') + 1)
                        def outputs = readJSON text: jsonText
                        env.EC2_PUBLIC_IP = outputs.instance_public_ip.value
                        env.APPLICATION_URL = outputs.application_url.value
                    }
                }
            }
        }

        stage('Deploy to EC2') {
            steps {
                script {
                    echo "Deploying Docker container on EC2 instance..."
                    bat """
                        ssh -o StrictHostKeyChecking=no -i infrastructure/terraform/%KEY_NAME%.pem ec2-user@%EC2_PUBLIC_IP% "docker run -d -p %APP_PORT%:%APP_PORT% %DOCKER_REGISTRY%/%IMAGE_NAME%:latest"
                    """
                }
            }
        }
        stage('Create EKS Cluster') {
            steps {
                script {
                    echo "Creating EKS cluster..."
                    try {
                        bat """
                            yes Y | eksctl create cluster --name ${EKS_CLUSTER_NAME} --region ${AWS_DEFAULT_REGION} --nodegroup-name ${EKS_NODE_GROUP_NAME} --node-type ${EKS_NODE_TYPE} --nodes-min ${EKS_NODE_MIN} --nodes-max ${EKS_NODE_MAX} --nodes ${EKS_NODE_DESIRED} --managed --with-oidc --ssh-access --ssh-public-key ${KEY_NAME}
                        """
                        echo "cluster created successfully"
                        
                        bat """
                            aws eks update-kubeconfig --name ${EKS_CLUSTER_NAME} --region ${AWS_DEFAULT_REGION}
                        """
                        
                        bat """
                            kubectl create namespace application-services --dry-run=client -o yaml | kubectl apply -f -
                        """
                        
                        bat """
                            helm repo add eks https://aws.github.io/eks-charts
                            helm repo update
                            helm install aws-load-balancer-controller eks/aws-load-balancer-controller \\
                                -n kube-system \\
                                --set clusterName=${EKS_CLUSTER_NAME} \\
                                --set serviceAccount.create=true \\
                                --set serviceAccount.annotations."eks\\.amazonaws\\.com/role-arn"=arn:aws:iam::${AWS_ACCOUNT_ID}:role/aws-load-balancer-controller
                        """
                    } catch (Exception e) {
                        error "Failed to create EKS cluster: ${e.message}"
                    }
                }
            }
        }

        stage('Deploy to EKS') {
            steps {
                script {
                    echo "Deploying to EKS cluster..."
                    try {
                        bat """
                            kubectl create configmap app-config \\
                                --from-literal=POSTGRES_DB=${POSTGRES_DB} \\
                                --from-literal=POSTGRES_USER=${POSTGRES_USER} \\
                                --from-literal=POSTGRES_PASSWORD=${POSTGRES_PASSWORD} \\
                                --namespace application-services \\
                                --dry-run=client -o yaml | kubectl apply -f -
                        """
                        
                        withCredentials([usernamePassword(credentialsId: 'dockerhub-credentials', usernameVariable: 'DOCKER_USERNAME', passwordVariable: 'DOCKER_PASSWORD')]) {
                            bat """
                                kubectl create secret docker-registry dockerhub-credentials \\
                                    --docker-server=https://index.docker.io/v1/ \\
                                    --docker-username=%DOCKER_USERNAME% \\
                                    --docker-password=%DOCKER_PASSWORD% \\
                                    --namespace application-services \\
                                    --dry-run=client -o yaml | kubectl apply -f -
                            """
                        }
                        
                        bat """
                            kubectl apply -f k8s/base/deployment.yaml -n application-services
                            kubectl apply -f k8s/base/service.yaml -n application-services
                            kubectl apply -f k8s/base/ingress.yaml -n application-services
                        """
                        
                        bat """
                            kubectl rollout status deployment/tenant-user-service -n application-services --timeout=300s
                        """
                    } catch (Exception e) {
                        error "Failed to deploy to EKS: ${e.message}"
                    }
                }
            }
        }

        stage('Get Load Balancer URL') {
            steps {
                script {
                    echo "Getting Load Balancer URL..."
                    try {
                        def lbHostname = bat(
                            script: 'kubectl get ingress -n application-services -o jsonpath="{.items[0].status.loadBalancer.ingress[0].hostname}"',
                            returnStdout: true
                        ).trim()
                        
                        env.APPLICATION_URL = "http://${lbHostname}"
                        echo "Application is available at: ${env.APPLICATION_URL}"
                    } catch (Exception e) {
                        error "Failed to get Load Balancer URL: ${e.message}"
                    }
                }
            }
        }
    }

    post {
        success {
            echo """
                Pipeline completed successfully!
                Application is available at: ${env.APPLICATION_URL}
                EKS Cluster Name: ${EKS_CLUSTER_NAME}
            """
        }
        failure {
            script {
                echo "Pipeline failed! Cleaning up resources..."
                try {
                    bat """
                        eksctl delete cluster --name ${EKS_CLUSTER_NAME} --region ${AWS_DEFAULT_REGION}
                    """
                    
                    dir('infrastructure/terraform') {
                        if (fileExists('.terraform')) {
                            bat 'terraform destroy -auto-approve'
                        }
                    }
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