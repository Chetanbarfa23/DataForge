pipeline {
    agent any

    stages {

        stage('Checkout') {
            steps {
                echo 'Checking out DataForge source code...'
                checkout scm
            }
        }

        stage('Environment Check') {
            steps {
                echo 'Checking Jenkins environment...'
                sh 'python3 --version'
                sh 'git --version'
                sh 'docker --version'
            }
        }

        stage('Install Dependencies') {
            steps {
                echo 'Installing DataForge dependencies...'
                sh 'python3 -m pip install -e ".[dev]"'
            }
        }

        stage('Run Tests') {
            steps {
                echo 'Running DataForge automated tests...'
                sh 'python3 -m pytest -v'
            }
        }

        stage('Docker Environment Check') {
            steps {
                echo 'Checking Docker access...'
                sh 'docker ps'
            }
        }

        stage('Success') {
            steps {
                echo 'DataForge CI pipeline executed successfully!'
            }
        }
    }

    post {
        success {
            echo 'BUILD SUCCESSFUL!'
        }

        failure {
            echo 'BUILD FAILED! Check console logs.'
        }
    }
}