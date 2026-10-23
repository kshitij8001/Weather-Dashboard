pipeline {
    agent any

    environment {
        // Change this to your Docker Hub username (e.g., 'yourusername/weather-dashboard')
        // Or your AWS ECR Registry URI (e.g., '<account-id>.dkr.ecr.<region>.amazonaws.com/weather-dashboard')
        DOCKER_HUB_REPO    = 'kshitij8001/weather-dashboard'
        
        // Jenkins Credentials ID configured under Manage Jenkins -> Credentials
        DOCKER_CREDS_ID    = 'dockerhub-credentials'
        
        // Dynamic build tag matching Jenkins execution number
        IMAGE_TAG          = "${BUILD_NUMBER}"
        APP_VERSION        = '1.0.0'
    }

    stages {
        // -------------------------------------------------------------
        // Step 1 & 2: Jenkins Checkout
        // -------------------------------------------------------------
        stage('Checkout') {
            steps {
                echo "=========================================================="
                echo "Step 2: Checking out latest source code from GitHub"
                echo "Build Number: ${BUILD_NUMBER}"
                echo "=========================================================="
                checkout scm
            }
        }

        // -------------------------------------------------------------
        // Step 3: Build and Test
        // -------------------------------------------------------------
        stage('Build and Test') {
            steps {
                echo "=========================================================="
                echo "Step 3: Building Python environment & Running Unit Tests"
                echo "=========================================================="
                sh '''
                    # Setup clean python virtual environment
                    python3 -m venv venv || virtualenv venv
                    . venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                    
                    # Run automated pytest test suite and export JUnit report
                    pytest -v --junitxml=test-results.xml tests/
                '''
            }
            post {
                always {
                    junit allowEmptyResults: true, testResults: 'test-results.xml'
                }
            }
        }

        // -------------------------------------------------------------
        // Step 4: Docker Build
        // -------------------------------------------------------------
        stage('Docker Build') {
            steps {
                echo "=========================================================="
                echo "Step 4: Building Docker Container Image"
                echo "Tagging: ${DOCKER_HUB_REPO}:${IMAGE_TAG} and latest"
                echo "=========================================================="
                sh """
                    docker build --build-arg APP_VERSION=${APP_VERSION} \
                                 -t ${DOCKER_HUB_REPO}:${IMAGE_TAG} \
                                 -t ${DOCKER_HUB_REPO}:latest .
                """
            }
        }

        // -------------------------------------------------------------
        // Step 5: Push Image to Registry (Docker Hub / AWS ECR)
        // -------------------------------------------------------------
        stage('Push Image') {
            steps {
                echo "=========================================================="
                echo "Step 5: Publishing Image to Container Registry"
                echo "=========================================================="
                withCredentials([usernamePassword(credentialsId: "${DOCKER_CREDS_ID}", usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                    sh """
                        echo "\$DOCKER_PASS" | docker login -u "\$DOCKER_USER" --password-stdin
                        docker push ${DOCKER_HUB_REPO}:${IMAGE_TAG}
                        docker push ${DOCKER_HUB_REPO}:latest
                        docker logout
                    """
                }
            }
        }

        // -------------------------------------------------------------
        // Step 6: Minikube Deployment
        // -------------------------------------------------------------
        stage('Minikube Deployment') {
            steps {
                echo "=========================================================="
                echo "Step 6: Applying Kubernetes Manifests on Minikube"
                echo "=========================================================="
                sh """
                    # Ensure kubectl can talk to minikube cluster
                    export KUBECONFIG=\${KUBECONFIG:-\$HOME/.kube/config}

                    # Apply Service and Deployment manifests
                    kubectl apply -f k8s/service.yaml
                    kubectl apply -f k8s/deployment.yaml

                    # Update deployment image to newly built version
                    kubectl set image deployment/weather-dashboard weather-dashboard=${DOCKER_HUB_REPO}:${IMAGE_TAG}

                    # Wait for rollout to complete
                    kubectl rollout status deployment/weather-dashboard --timeout=120s
                """
            }
        }

        // -------------------------------------------------------------
        // Step 7: Verification
        // -------------------------------------------------------------
        stage('Verification') {
            steps {
                echo "=========================================================="
                echo "Step 7: Verifying Pods, Deployment, and Application"
                echo "=========================================================="
                sh """
                    export KUBECONFIG=\${KUBECONFIG:-\$HOME/.kube/config}

                    echo ">>> 1. Kubernetes Pods Status:"
                    kubectl get pods -l app=weather-dashboard -o wide

                    echo ">>> 2. Kubernetes Deployment Status:"
                    kubectl get deployment weather-dashboard

                    echo ">>> 3. Kubernetes Service Status:"
                    kubectl get svc weather-dashboard-service

                    echo ">>> 4. Testing Application Health Endpoint:"
                    CLUSTER_IP=\$(minikube ip 2>/dev/null || echo "127.0.0.1")
                    echo "Cluster node IP: \${CLUSTER_IP}"
                    echo "Service port: 30080"

                    # Verify application health endpoint
                    for i in 1 2 3 4 5; do
                        STATUS_CODE=\$(curl -s -o /dev/null -w "%{http_code}" http://\${CLUSTER_IP}:30080/health || echo "000")
                        if [ "\$STATUS_CODE" = "200" ]; then
                            echo "SUCCESS: Weather Dashboard responded with HTTP 200 OK!"
                            curl -s http://\${CLUSTER_IP}:30080/health
                            echo ""
                            break
                        fi
                        echo "Waiting for app readiness (attempt \$i/5)... status: \$STATUS_CODE"
                        sleep 4
                    done
                """
            }
        }
    }

    post {
        success {
            echo "=========================================================="
            echo " CI/CD Pipeline Executed Successfully!"
            echo " Image: ${DOCKER_HUB_REPO}:${IMAGE_TAG}"
            echo " Application is running on Minikube."
            echo "=========================================================="
        }
        failure {
            echo "=========================================================="
            echo " Pipeline Execution FAILED. Inspect console output."
            echo "=========================================================="
        }
    }
}
