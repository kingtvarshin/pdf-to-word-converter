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
//   • github-creds            — Optional Username/Password (GitHub PAT)
//                               Only needed if the repo becomes private or
//                               your Jenkins instance cannot clone it anonymously.
//
// These default credential IDs are declared in the environment block below.
// If you rename them in Jenkins, update the values there to match.
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
        GITHUB_CREDS_ID = ''
        REGISTRY_CREDS_ID = 'truenas-registry-creds'
        WATCHTOWER_TOKEN_ID = 'watchtower-api-token'
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
        stage('Validate Jenkins Credentials') {
        // ---------------------------------------------------------------
            steps {
                script {
                    def missing = []

                    def requiredCredentials = [
                        [id: env.REGISTRY_CREDS_ID, type: 'usernamePassword'],
                        [id: env.WATCHTOWER_TOKEN_ID, type: 'string']
                    ]

                    if (env.GITHUB_CREDS_ID?.trim()) {
                        requiredCredentials.add(0, [id: env.GITHUB_CREDS_ID, type: 'usernamePassword'])
                    }

                    for (credential in requiredCredentials) {
                        try {
                            if (credential.type == 'usernamePassword') {
                                withCredentials([usernamePassword(
                                    credentialsId: credential.id,
                                    usernameVariable: 'TEST_USER',
                                    passwordVariable: 'TEST_PASS'
                                )]) {
                                    sh 'true'
                                }
                            } else {
                                withCredentials([string(
                                    credentialsId: credential.id,
                                    variable: 'TEST_TOKEN'
                                )]) {
                                    sh 'true'
                                }
                            }
                        } catch (Exception ignored) {
                            missing << credential.id
                        }
                    }

                    if (missing) {
                        error(
                            "Missing Jenkins credential(s): ${missing.join(', ')}. " +
                            "Create them in Manage Jenkins -> Credentials, or update " +
                            "GITHUB_CREDS_ID / REGISTRY_CREDS_ID / WATCHTOWER_TOKEN_ID in the Jenkinsfile " +
                            "to match your existing IDs."
                        )
                    }
                }
            }
        }

        // ---------------------------------------------------------------
        stage('Checkout') {
        // ---------------------------------------------------------------
            steps {
                script {
                    def remoteConfig = [url: env.REPO_URL]
                    if (env.GITHUB_CREDS_ID?.trim()) {
                        remoteConfig.credentialsId = env.GITHUB_CREDS_ID
                    }

                    checkout([
                        $class: 'GitSCM',
                        branches: [[name: "*/${params.BRANCH}"]],
                        userRemoteConfigs: [remoteConfig]
                    ])

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
                    credentialsId: env.REGISTRY_CREDS_ID,
                    usernameVariable: 'REG_USER',
                    passwordVariable: 'REG_PASS'
                )]) {
                    sh """
                        set +e
                        LOGIN_OUTPUT=\$(echo "\$REG_PASS" | docker login ${env.REGISTRY_HOST} \\
                            -u "\$REG_USER" --password-stdin 2>&1)
                        LOGIN_STATUS=\$?
                        set -e

                        echo "\$LOGIN_OUTPUT"

                        if [ \$LOGIN_STATUS -ne 0 ]; then
                            case "\$LOGIN_OUTPUT" in
                                *"server gave HTTP response to HTTPS client"*)
                                    echo "Registry ${env.REGISTRY_HOST} is serving HTTP, but the Docker daemon is attempting HTTPS." >&2
                                    echo "Add the exact host:port '${env.REGISTRY_HOST}' to the Docker daemon insecure-registries list on the machine behind /var/run/docker.sock, then restart Docker." >&2
                                    exit 1
                                    ;;
                            esac

                            exit \$LOGIN_STATUS
                        fi

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
                    credentialsId: env.WATCHTOWER_TOKEN_ID,
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
