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