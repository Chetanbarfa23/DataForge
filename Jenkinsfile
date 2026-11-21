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
            }
        }

        stage('Docker Environment Check') {
            steps {
                echo 'Checking Docker inside Jenkins...'
                sh 'docker --version'
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