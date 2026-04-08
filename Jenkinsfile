// ===========================================================================
// Jenkins CI/CD Pipeline — Flask PDF to Word Converter
//
// Prerequisites:
//   • Jenkins must use the custom image built from ./jenkins/Dockerfile
//     (has Docker CLI pre-installed).
//   • /var/run/docker.sock must be mounted into the Jenkins container
//     (configured in deploy/registry-stack.yml).
//   • TRUENAS_REGISTRY_HOST and WATCHTOWER_URL are injected as container
//     environment variables in deploy/registry-stack.yml — no manual
//     Global Properties step needed.
//
// Jenkins Credentials required (Manage Jenkins → Credentials):
//   • truenas-registry-creds  — Username/Password for your TrueNAS registry
//   • watchtower-api-token    — Secret Text: the WATCHTOWER_HTTP_API_TOKEN
//                               value you set in registry-stack.yml
//   • github-creds            — Username/Password (GitHub PAT)
//
// Visual pipeline UI:
//   Install the "Blue Ocean" plugin → open http://TRUENAS_IP:30017/blue
// ===========================================================================

pipeline {
    agent any

    parameters {
        choice(
            name: 'BRANCH',
            choices: ['main', 'develop', 'feature/security_fixes'],
            description: 'Git branch to build and deploy'
        )
    }

    environment {
        REPO_URL     = 'https://github.com/kingtvarshin/pdf-to-word-converter.git'
        IMAGE_NAME   = 'flask-pdf-to-word-app'
        // TRUENAS_REGISTRY_HOST and WATCHTOWER_URL are injected by the
        // Jenkins container in deploy/registry-stack.yml
        VERSIONED    = "${env.TRUENAS_REGISTRY_HOST}/${IMAGE_NAME}:${BUILD_NUMBER}"
        LATEST       = "${env.TRUENAS_REGISTRY_HOST}/${IMAGE_NAME}:latest"
    }

    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timeout(time: 30, unit: 'MINUTES')
        timestamps()
    }

    stages {

        // ---------------------------------------------------------------
        stage('Validate Config') {
        // ---------------------------------------------------------------
            steps {
                script {
                    if (!env.TRUENAS_REGISTRY_HOST || env.TRUENAS_REGISTRY_HOST == 'null') {
                        error("TRUENAS_REGISTRY_HOST is not set. " +
                              "Add it as an environment variable in the Jenkins " +
                              "container definition in deploy/registry-stack.yml and redeploy Jenkins.")
                    }
                    if (!env.WATCHTOWER_URL || env.WATCHTOWER_URL == 'null') {
                        error("WATCHTOWER_URL is not set. " +
                              "Add it as an environment variable in the Jenkins " +
                              "container definition in deploy/registry-stack.yml and redeploy Jenkins.")
                    }
                    echo "Registry : ${env.TRUENAS_REGISTRY_HOST}"
                    echo "Watchtower: ${env.WATCHTOWER_URL}"
                }
            }
        }

        // ---------------------------------------------------------------
        stage('Checkout') {
        // ---------------------------------------------------------------
            steps {
                checkout([
                    $class: 'GitSCM',
                    branches: [[name: "*/${params.BRANCH}"]],
                    userRemoteConfigs: [[
                        url: "${REPO_URL}",
                        credentialsId: 'github-creds'
                    ]]
                ])
                script {
                    env.GIT_SHORT = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
                    echo "Building branch=${params.BRANCH}  commit=${env.GIT_SHORT}"
                }
            }
        }

        // ---------------------------------------------------------------
        stage('Build') {
        // ---------------------------------------------------------------
            steps {
                sh """
                    docker build \
                        --label "git.branch=${params.BRANCH}" \
                        --label "git.commit=${GIT_SHORT}" \
                        --label "build.number=${BUILD_NUMBER}" \
                        -t ${VERSIONED} \
                        -t ${LATEST} \
                        .
                """
            }
        }

        // ---------------------------------------------------------------
        stage('Push to TrueNAS Registry') {
        // ---------------------------------------------------------------
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'truenas-registry-creds',
                    usernameVariable: 'REG_USER',
                    passwordVariable: 'REG_PASS'
                )]) {
                    sh """
                        echo "\$REG_PASS" | docker login ${env.TRUENAS_REGISTRY_HOST} \\
                            -u "\$REG_USER" --password-stdin
                        docker push ${VERSIONED}
                        docker push ${LATEST}
                        docker logout ${env.TRUENAS_REGISTRY_HOST}
                    """
                }
            }
        }

        // ---------------------------------------------------------------
        stage('Deploy via Watchtower') {
        // ---------------------------------------------------------------
        // Calls the Watchtower HTTP API to immediately pull the updated
        // "latest" image and restart the app container on TrueNAS.
        // ---------------------------------------------------------------
            steps {
                withCredentials([string(
                    credentialsId: 'watchtower-api-token',
                    variable: 'WT_TOKEN'
                )]) {
                    sh """
                        curl -sf \
                            -X POST \
                            -H "Authorization: Bearer \$WT_TOKEN" \
                            "${env.WATCHTOWER_URL}/v1/update"
                    """
                }
            }
        }
    }

    post {
        always {
            // Remove local images to keep the Jenkins agent disk clean
            sh "docker rmi ${VERSIONED} ${LATEST} || true"
        }
        success {
            echo "Deployed build #${BUILD_NUMBER} (${GIT_SHORT}) from branch '${params.BRANCH}' to TrueNAS."
        }
        failure {
            echo "Pipeline FAILED at build #${BUILD_NUMBER}. Check the stage logs above."
        }
    }
}
