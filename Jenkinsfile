pipeline {
    agent any

    environment {
        DOCKER_REGISTRY = 'hemanthkumar21'  
        IMAGE_NAME = 'application_services_app'
        
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
        
        // Helm installation path
        HELM_HOME = "${WORKSPACE}\\helm"
        PATH = "${env.PATH};${WORKSPACE}\\helm"
    }

    stages {
        stage('Clone Repository') {
            steps {
                script {
                    // cleanWs()
                    echo "Cloning repository..."
                    git branch: 'main',
                        url: "${env.GIT_REPO}"
                }
            }
        }

        stage('Install Helm') {
            steps {
                script {
                    echo "Installing Helm..."
                    bat '''
                        if not exist helm mkdir helm
                        cd helm
                        
                        REM Check if helm is already installed in workspace
                        if exist helm.exe (
                            echo "Helm found in workspace"
                            helm.exe version
                        ) else (
                            echo "Downloading and installing Helm v3.12.0..."
                            
                            REM Download with retry logic
                            for /L %%i in (1,1,3) do (
                                curl -LO https://get.helm.sh/helm-v3.12.0-windows-amd64.zip && goto :extract || (
                                    echo "Download attempt %%i failed, retrying..."
                                    timeout /t 5 /nobreak >nul
                                )
                            )
                            echo "Failed to download Helm after 3 attempts" && exit 1
                            
                            :extract
                            echo "Extracting Helm..."
                            tar -xf helm-v3.12.0-windows-amd64.zip
                            move windows-amd64\\helm.exe .\\
                            del helm-v3.12.0-windows-amd64.zip
                            rmdir /s /q windows-amd64
                            
                            echo "Helm installed successfully"
                            helm.exe version
                        )
                    '''
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
                            for /f "tokens=*" %%i in ('aws ec2 describe-vpcs --filters "Name=tag:Name,Values=application-services-vpc" --query "Vpcs[].VpcId" --output text 2^>nul') do (
                                if not "%%i"=="" (
                                    aws ec2 delete-vpc --vpc-id %%i
                                    echo Deleted VPC: %%i
                                )
                            )
                            
                            aws ec2 describe-security-groups --group-names application-services-sg >nul 2>&1 && (
                                aws ec2 delete-security-group --group-name application-services-sg
                                echo Security group deleted successfully
                            ) || echo Security group doesn't exist
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

        stage('Build Docker Image') {
            steps {
                script {
                    echo "Building Docker image with tag '${BUILD_NUMBER}'..."
                    retry(2) {
                        bat """
                            docker-compose build --no-cache app
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
                            
                            echo Pushing image: ${DOCKER_REGISTRY}/${IMAGE_NAME}:${BUILD_NUMBER}
                            docker push ${DOCKER_REGISTRY}/${IMAGE_NAME}:${BUILD_NUMBER} || exit 1
                            
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
                        docker pull ${DOCKER_REGISTRY}/${IMAGE_NAME}:${BUILD_NUMBER} || exit 1
                        
                        docker run -d -p 8009:8000 --name test-${IMAGE_NAME} ${DOCKER_REGISTRY}/${IMAGE_NAME}:${BUILD_NUMBER} || exit 1
                        ping -n 11 127.0.0.1 >nul
                        docker ps | findstr "test-${IMAGE_NAME}" || exit 1
                        docker logs test-${IMAGE_NAME}
                        
                        docker rm -f test-${IMAGE_NAME}
                    """
                }
            }
        }

        stage('Create AWS Key Pair') {
            steps {
                dir('infrastructure/terraform') {
                    bat 'terraform init -input=false'
                    bat 'terraform apply -auto-approve -var="key_name=%KEY_NAME%" -target=tls_private_key.app_private_key -target=local_file.private_key -target=aws_key_pair.app_key_pair'
                    bat 'copy %KEY_NAME%.pem ..\\..\\%KEY_NAME%.pem /Y'
                    bat 'echo "Key file saved to workspace: %WORKSPACE%\\%KEY_NAME%.pem"'
                    
                    bat """
                        if not exist ..\\..\\%KEY_NAME%.pem (
                            echo "Error: Key file %KEY_NAME%.pem was not copied to workspace"
                            exit 1
                        )
                        
                        icacls ..\\..\\%KEY_NAME%.pem /inheritance:r
                        icacls ..\\..\\%KEY_NAME%.pem /grant:r "NT AUTHORITY\\SYSTEM":F
                        icacls ..\\..\\%KEY_NAME%.pem /grant:r "BUILTIN\\Administrators":F
                    """
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

        stage('Wait for EC2 Instance') {
            steps {
                script {
                    echo "Waiting for EC2 instance to be ready..."
                    sleep(time: 60, unit: "SECONDS")
                }
            }
        }

        stage('Verify SSH Connectivity') {
            steps {
                script {
                    echo "Verifying SSH connectivity to EC2 instance..."
                    retry(5) {
                        bat """
                            ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=nul -o ConnectTimeout=30 -i %KEY_NAME%.pem ubuntu@%EC2_PUBLIC_IP% "echo 'SSH connection successful'" || (
                                echo "SSH connection failed, waiting 30 seconds before retry..."
                                ping -n 31 127.0.0.1 >nul
                                exit 1
                            )
                        """
                    }
                }
            }
        }

        stage('Deploy to EC2') {
            steps {
                script {
                    echo "Deploying Docker container on EC2 instance..."
                    // Create a temporary script file to avoid quoting issues
                    writeFile file: 'deploy_script.sh', text: '''#!/bin/bash
set -e
echo "Starting deployment script..."

# Wait for cloud-init to complete
while [ ! -f /var/lib/cloud/instance/boot-finished ]; do
    echo "Waiting for cloud-init to complete..."
    sleep 10
done

# Update package list with retries
for i in $(seq 1 12); do 
    if sudo apt-get update -qq; then
        break
    else
        echo "apt-get update failed, retrying in 10 seconds..."
        sleep 10
    fi
done

# Install Docker
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    sudo apt-get install -y docker.io
    sudo systemctl start docker
    sudo systemctl enable docker
    sudo usermod -aG docker ubuntu
else
    echo "Docker already installed"
    sudo systemctl start docker
fi

# Pull and run the application
echo "Pulling Docker image..."
sudo docker pull ''' + "${DOCKER_REGISTRY}/${IMAGE_NAME}:${BUILD_NUMBER}" + '''

# Stop existing container if running
sudo docker stop app-container || true
sudo docker rm app-container || true

# Run new container - FIXED PORT MAPPING
echo "Starting application container..."
sudo docker run -d --name app-container -p 3000:8000 ''' + "${DOCKER_REGISTRY}/${IMAGE_NAME}:${BUILD_NUMBER}" + '''

# Verify container is running
sleep 10
if sudo docker ps | grep app-container; then
    echo "Application deployed successfully!"
else
    echo "Deployment failed - container not running"
    sudo docker logs app-container
    exit 1
fi
'''
                    
                    bat """
                        scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=nul -i %KEY_NAME%.pem deploy_script.sh ubuntu@%EC2_PUBLIC_IP%:~/deploy_script.sh
                        ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=nul -i %KEY_NAME%.pem ubuntu@%EC2_PUBLIC_IP% "chmod +x ~/deploy_script.sh && ~/deploy_script.sh"
                    """
                    
                    // Clean up the temporary script
                    bat "del deploy_script.sh"
                }
            }
        }

        stage('Verify Application Deployment') {
            steps {
                script {
                    echo "Verifying application is running..."
                    retry(3) {
                        bat """
                            ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=nul -i %KEY_NAME%.pem ubuntu@%EC2_PUBLIC_IP% "sudo docker ps | grep app-container && sleep 10 && curl -s http://localhost:3000/ > /dev/null && echo 'Application is healthy' || (echo 'Health check failed' && sudo docker logs app-container && exit 1)"
                        """
                    }
                }
            }
        }

        stage('Get AWS Account ID') {
            steps {
                script {
                    echo "Getting AWS Account ID..."
                    def awsAccountId = bat(
                        script: 'aws sts get-caller-identity --query Account --output text',
                        returnStdout: true
                    ).trim()
                    env.AWS_ACCOUNT_ID = awsAccountId
                    echo "AWS Account ID: ${env.AWS_ACCOUNT_ID}"
                }
            }
        }

        stage('Create EKS Cluster') {
            steps {
                script {
                    echo "Creating EKS cluster..."
                    try {
                        bat """
                            eksctl create cluster --name ${EKS_CLUSTER_NAME} --region ${AWS_DEFAULT_REGION} --nodegroup-name ${EKS_NODE_GROUP_NAME} --node-type ${EKS_NODE_TYPE} --nodes-min ${EKS_NODE_MIN} --nodes-max ${EKS_NODE_MAX} --nodes ${EKS_NODE_DESIRED} --managed --with-oidc --ssh-access --ssh-public-key %KEY_NAME% --timeout=25m
                        """
                        echo "Cluster created successfully"
                        
                        bat """
                            aws eks update-kubeconfig --name ${EKS_CLUSTER_NAME} --region ${AWS_DEFAULT_REGION}
                        """
                        
                        bat """
                            kubectl create namespace application-services --dry-run=client -o yaml | kubectl apply -f -
                        """
                        
                        // Create service account for AWS Load Balancer Controller
                        bat """
                            eksctl create iamserviceaccount --cluster=${EKS_CLUSTER_NAME} --namespace=kube-system --name=aws-load-balancer-controller --role-name AmazonEKSLoadBalancerControllerRole --attach-policy-arn=arn:aws:iam::aws:policy/ElasticLoadBalancingFullAccess --approve --region=${AWS_DEFAULT_REGION}
                        """
                        
                        // Install AWS Load Balancer Controller using Helm
                        bat """
                            helm repo add eks https://aws.github.io/eks-charts
                            helm repo update
                            helm install aws-load-balancer-controller eks/aws-load-balancer-controller -n kube-system --set clusterName=${EKS_CLUSTER_NAME} --set serviceAccount.create=false --set serviceAccount.name=aws-load-balancer-controller
                        """
                    } catch (Exception e) {
                        echo "Warning: Failed to install AWS Load Balancer Controller with Helm: ${e.message}"
                        echo "Proceeding without Load Balancer Controller - you can install it manually later"
                    }
                }
            }
        }

        stage('Deploy to EKS') {
            steps {
                script {
                    echo "Deploying to EKS cluster..."
                    try {
                        // Create configmap using secure method
                        withCredentials([
                            string(credentialsId: 'postgres-db-name', variable: 'DB_NAME'),
                            string(credentialsId: 'postgres-username', variable: 'DB_USER'),
                            string(credentialsId: 'postgres-password', variable: 'DB_PASS')
                        ]) {
                            bat '''
                                kubectl create configmap app-config --from-literal=POSTGRES_DB=%DB_NAME% --from-literal=POSTGRES_USER=%DB_USER% --from-literal=POSTGRES_PASSWORD=%DB_PASS% --namespace application-services --dry-run=client -o yaml | kubectl apply -f -
                            '''
                        }
                        
                        withCredentials([usernamePassword(credentialsId: 'dockerhub-credentials', usernameVariable: 'DOCKER_USERNAME', passwordVariable: 'DOCKER_PASSWORD')]) {
                            bat '''
                                kubectl create secret docker-registry dockerhub-credentials --docker-server=https://index.docker.io/v1/ --docker-username=%DOCKER_USERNAME% --docker-password=%DOCKER_PASSWORD% --namespace application-services --dry-run=client -o yaml | kubectl apply -f -
                            '''
                        }
                        
                        // Update the image tag in your existing deployment files
                        // Assuming your k8s files are in the 'k8s' or 'kubernetes' directory in your Git repo
                        bat """
                            echo "Updating image tag in deployment files..."
                            
                            REM Check if k8s directory exists in the repo
                            if exist k8s\\deployment.yaml (
                                echo "Found k8s/deployment.yaml, updating image tag..."
                                powershell -Command "(Get-Content k8s\\deployment.yaml) -replace 'hemanthkumar21/application_services_app:.*', 'hemanthkumar21/application_services_app:${BUILD_NUMBER}' | Set-Content k8s\\deployment.yaml"
                            ) else if exist kubernetes\\deployment.yaml (
                                echo "Found kubernetes/deployment.yaml, updating image tag..."
                                powershell -Command "(Get-Content kubernetes\\deployment.yaml) -replace 'hemanthkumar21/application_services_app:.*', 'hemanthkumar21/application_services_app:${BUILD_NUMBER}' | Set-Content kubernetes\\deployment.yaml"
                            ) else if exist k8s\\base\\deployment.yaml (
                                echo "Found k8s/base/deployment.yaml, updating image tag..."
                                powershell -Command "(Get-Content k8s\\base\\deployment.yaml) -replace 'hemanthkumar21/application_services_app:.*', 'hemanthkumar21/application_services_app:${BUILD_NUMBER}' | Set-Content k8s\\base\\deployment.yaml"
                            ) else (
                                echo "No deployment.yaml found in expected locations (k8s/, kubernetes/, k8s/base/)"
                                echo "Please ensure your k8s manifests are in one of these directories in your Git repo"
                                exit 1
                            )
                        """
                        
                        // Apply the manifests from your Git repository
                        bat '''
                            echo "Applying Kubernetes manifests from Git repository..."
                            
                            REM Apply manifests based on directory structure
                            if exist k8s\\deployment.yaml (
                                echo "Applying from k8s/ directory..."
                                kubectl apply -f k8s/ -n application-services --recursive
                            ) else if exist kubernetes\\deployment.yaml (
                                echo "Applying from kubernetes/ directory..."
                                kubectl apply -f kubernetes/ -n application-services --recursive
                            ) else if exist k8s\\base\\deployment.yaml (
                                echo "Applying from k8s/base/ directory..."
                                kubectl apply -f k8s/base/ -n application-services --recursive
                            ) else (
                                echo "ERROR: No Kubernetes manifests found!"
                                echo "Expected locations:"
                                echo "  - k8s/"
                                echo "  - kubernetes/"
                                echo "  - k8s/base/"
                                dir /b
                                exit 1
                            )
                        '''
                        
                        // Wait for deployment rollout
                        bat '''
                            echo "Waiting for deployment rollout..."
                            kubectl rollout status deployment/tenant-user-service -n application-services --timeout=600s
                        '''
                        
                        // Verify deployment
                        bat '''
                            echo "Verifying deployment..."
                            kubectl get pods -n application-services -l app=tenant-user-service
                            kubectl get services -n application-services
                            kubectl describe deployment tenant-user-service -n application-services
                        '''
                        
                    } catch (Exception e) {
                        // Debug information
                        bat '''
                            echo "=== KUBERNETES DEBUG INFORMATION ==="
                            kubectl get pods -n application-services -o wide || echo "No pods found"
                            kubectl logs -l app=tenant-user-service -n application-services --tail=50 || echo "No logs available"
                            kubectl describe pods -l app=tenant-user-service -n application-services || echo "No pods found"
                        '''
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
                        // First try to get ingress hostname
                        def lbHostname = ""
                        try {
                            lbHostname = bat(
                                script: 'kubectl get ingress -n application-services -o jsonpath="{.items[0].status.loadBalancer.ingress[0].hostname}" 2>nul',
                                returnStdout: true
                            ).trim()
                        } catch (Exception e) {
                            echo "No ingress found, trying to get service LoadBalancer..."
                        }
                        
                        // If no ingress, try to get service LoadBalancer
                        if (!lbHostname) {
                            try {
                                lbHostname = bat(
                                    script: 'kubectl get service -n application-services -o jsonpath="{.items[0].status.loadBalancer.ingress[0].hostname}" 2>nul',
                                    returnStdout: true
                                ).trim()
                            } catch (Exception e) {
                                echo "No LoadBalancer service found"
                            }
                        }
                        
                        if (lbHostname && lbHostname != "") {
                            env.EKS_APPLICATION_URL = "http://${lbHostname}"
                            echo "EKS Application is available at: ${env.EKS_APPLICATION_URL}"
                        } else {
                            echo "LoadBalancer URL not available yet. You can check later with: kubectl get ingress -n application-services"
                        }
                    } catch (Exception e) {
                        echo "Could not retrieve Load Balancer URL: ${e.message}"
                    }
                }
            }
        }
    }

    post {
        success {
            echo """
                🎉 Pipeline completed successfully!
                
                📍 Deployment Information:
                ========================
                EC2 Application URL: ${env.APPLICATION_URL}
                EKS Cluster Name: ${EKS_CLUSTER_NAME}
                Docker Image: ${DOCKER_REGISTRY}/${IMAGE_NAME}:${BUILD_NUMBER}
                
                📝 Next Steps:
                =============
                1. Access your application at: ${env.APPLICATION_URL}
                2. Monitor EKS deployment: kubectl get pods -n application-services
                3. Check EKS services: kubectl get svc -n application-services
                4. View logs: kubectl logs -l app=tenant-user-service -n application-services
            """
        }

        failure {
            script {
                echo "❌ Pipeline failed! Cleaning up resources..."
                try {
                    // Cleanup EKS cluster
                    bat """
                        eksctl get cluster --name ${EKS_CLUSTER_NAME} --region ${AWS_DEFAULT_REGION} >nul 2>&1 && (
                            echo "Deleting EKS cluster..."
                            eksctl delete cluster --name ${EKS_CLUSTER_NAME} --region ${AWS_DEFAULT_REGION} --wait
                        ) || echo "EKS cluster does not exist, skipping deletion"
                    """

                    // Cleanup Terraform resources
                    dir('infrastructure/terraform') {
                        if (fileExists('terraform.tfstate')) {
                            bat 'terraform destroy -auto-approve -var="key_name=%KEY_NAME%"'
                        }
                    }
                } catch (Exception e) {
                    echo "⚠️ Warning: Cleanup during failure encountered issues: ${e.message}"
                }
            }
        }

        always {
            script {
                try {
                    // Clean up key files
                    bat """
                        if exist %KEY_NAME%.pem (
                            echo Deleting key file: %KEY_NAME%.pem
                            del /f %KEY_NAME%.pem
                        )
                    """

                    // Clean up Docker resources
                    bat "docker system prune -f || echo 'Docker cleanup completed'"

                    // Clean up workspace with retries
                    retry(3) {
                        cleanWs(cleanWhenFailure: true, deleteDirs: true)
                    }
                } catch (Exception e) {
                    echo "⚠️ Warning: Final cleanup failed: ${e.message}"
                }
            }
        }
    }
}