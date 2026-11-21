pipeline {
    agent any

    stages {

        // Stage 1: Checkout source code from GitHub
        stage('Checkout') {
            steps {
                echo 'Checking out DataForge source code...'
                checkout scm
            }
        }

        // Stage 2: Check installed tools
        stage('Environment Check') {
            steps {
                echo 'Checking Jenkins environment...'

                sh 'python3 --version'
                sh 'git --version'
                sh 'docker --version'
            }
        }

        // Stage 3: Create Python virtual environment and install dependencies
        stage('Install Dependencies') {
            steps {
                echo 'Creating Python virtual environment...'

                sh '''
                    python3 -m venv .venv

                    .venv/bin/python -m pip install --upgrade pip

                    .venv/bin/python -m pip install -e ".[dev]"
                '''
            }
        }

        // Stage 4: Run automated tests
        stage('Run Tests') {
            steps {
                echo 'Running DataForge automated tests...'

                sh '''
                    .venv/bin/python -m pytest -v
                '''
            }
        }

        // Stage 5: Verify Docker access
        stage('Docker Environment Check') {
            steps {
                echo 'Checking Docker access...'

                sh 'docker ps'
            }
        }

        // Stage 6: Pipeline success
        stage('Success') {
            steps {
                echo 'DataForge CI pipeline executed successfully!'
            }
        }
    }

    // Post-build actions
    post {

        success {
            echo 'BUILD SUCCESSFUL!'
        }

        failure {
            echo 'BUILD FAILED! Check console logs.'
        }
    }
}