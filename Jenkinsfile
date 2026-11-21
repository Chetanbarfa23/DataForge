stages {

    // Stage 1: Checkout source code from GitHub
    stage('Checkout') {
        steps {
            echo 'Checking out DataForge source code...'
            checkout scm
        }
    }

    // Stage 2: Check Jenkins environment
    stage('Environment Check') {
        steps {
            echo 'Checking Jenkins environment...'

            sh 'python3 --version'
            sh 'git --version'
        }
    }

    // Stage 3: Verify Docker access
    stage('Docker Environment Check') {
        steps {
            echo 'Checking Docker inside Jenkins...'

            sh 'docker --version'
            sh 'docker ps'
        }
    }

    // Stage 4: Pipeline success
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