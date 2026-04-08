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
        // Prepend the persistent Docker CLI location (installed by setup-docker-cli pipeline)
        // This survives Jenkins container restarts since /var/jenkins_home is a volume.
        PATH         = "/var/jenkins_home/bin:${env.PATH}"
        // REGISTRY_HOST is computed in the Validate Config stage by stripping
        // any http:// prefix and trailing slashes from TRUENAS_REGISTRY_HOST.
        // VERSIONED and LATEST are set dynamically in the Build stage.
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
                              "Set it in Manage Jenkins → System → Global properties. " +
                              "Value must be HOST:PORT only — no http:// prefix, no trailing slash.")
                    }
                    if (!env.WATCHTOWER_URL || env.WATCHTOWER_URL == 'null') {
                        error("WATCHTOWER_URL is not set. " +
                              "Set it in Manage Jenkins → System → Global properties.")
                    }
                    // Strip accidental http/https prefix and trailing slashes from registry host
                    env.REGISTRY_HOST = env.TRUENAS_REGISTRY_HOST
                        .replaceAll('^https?://', '')
                        .replaceAll('/+$', '')
                    env.VERSIONED = "${env.REGISTRY_HOST}/${env.IMAGE_NAME}:${env.BUILD_NUMBER}"
                    env.LATEST    = "${env.REGISTRY_HOST}/${env.IMAGE_NAME}:latest"
                    echo "Registry : ${env.REGISTRY_HOST}"
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
                        -t ${env.VERSIONED} \\
                        -t ${env.LATEST} \\
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
                        echo "\$REG_PASS" | docker login ${env.REGISTRY_HOST} \\
                            -u "\$REG_USER" --password-stdin
                        docker push ${env.VERSIONED}
                        docker push ${env.LATEST}
                        docker logout ${env.REGISTRY_HOST}
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
            sh "docker rmi ${env.VERSIONED} ${env.LATEST} || true"
        }
        success {
            echo "Deployed build #${BUILD_NUMBER} (${env.GIT_SHORT}) from branch '${params.BRANCH}' to TrueNAS."
        }
        failure {
            echo "Pipeline FAILED at build #${BUILD_NUMBER}. Check the stage logs above."
        }
    }
}
