#!groovy

def PYTHON_VERSION = '3.8'
pipeline {
  options {
    buildDiscarder logRotator(artifactDaysToKeepStr: '', artifactNumToKeepStr: '3', daysToKeepStr: '', numToKeepStr: '')
    gitLabConnection('gitlab@cr.imson.co')
    gitlabBuilds(builds: ['jenkins'])
    disableConcurrentBuilds()
    timestamps()
  }
  post {
    failure {
      mattermostSend color: 'danger', message: "Build failed: [${env.JOB_NAME}${env.BUILD_DISPLAY_NAME}](${env.BUILD_URL}) - @channel"
      updateGitlabCommitStatus name: 'jenkins', state: 'failed'
    }
    unstable {
      mattermostSend color: 'warning', message: "Build unstable: [${env.JOB_NAME}${env.BUILD_DISPLAY_NAME}](${env.BUILD_URL}) - @channel"
      updateGitlabCommitStatus name: 'jenkins', state: 'failed'
    }
    aborted {
      updateGitlabCommitStatus name: 'jenkins', state: 'canceled'
    }
    success {
      mattermostSend color: 'good', message: "Build completed: [${env.JOB_NAME}${env.BUILD_DISPLAY_NAME}](${env.BUILD_URL})"
      updateGitlabCommitStatus name: 'jenkins', state: 'success'
    }
    always {
      cleanWs()
    }
  }
  agent {
    docker {
      image "docker.cr.imson.co/python-lambda-layer-builder:${PYTHON_VERSION}"
    }
  }
  environment {
    CI = 'true'
    AWS_REGION = 'us-east-2'
    AWS_BUCKET_NAME = 'codebite-lambda-layers'
    LAYER_NAME = 'crimsoncore'
    LAYER_DESCRIPTION = "CrimsonCore Lambda Layer for Python ${PYTHON_VERSION}"
    LICENSE_IDENTIFIER = 'MIT'
  }
  stages {
    stage('Prepare') {
      steps {
        updateGitlabCommitStatus name: 'jenkins', state: 'running'
        sh 'python --version && pip --version'
      }
    }

    stage('QA') {
      environment {
        HOME = "${env.WORKSPACE}"
      }
      steps {
        sh """
          pip install \
            --user \
            --no-cache \
            -r ${env.WORKSPACE}/deps/boto3layer/requirements.txt
        """.stripIndent()

        sh """
          find ${env.WORKSPACE}/lib/${env.LAYER_NAME} \
            -type f \
            -iname '*.py' \
            -print0 \
            | xargs -0 python -m pylint
        """.stripIndent()

        sh """
          pip install \
            --user \
            --no-cache \
            -e ${env.WORKSPACE}/lib
        """.stripIndent()

        sh 'python -m unittest discover'
      }
    }

    stage('Build crimsoncore layer') {
      steps {
        sh """
          mkdir -p \
            ${env.WORKSPACE}/build/python/lib/python${PYTHON_VERSION}/site-packages/${env.LAYER_NAME}/
        """.stripIndent()

        sh """
          cp \
            ${env.WORKSPACE}/lib/${env.LAYER_NAME}/*.py \
            ${env.WORKSPACE}/build/python/lib/python${PYTHON_VERSION}/site-packages/${env.LAYER_NAME}/
        """.stripIndent()

        dir("${env.WORKSPACE}/build/") {
          sh "zip -r ${env.LAYER_NAME}-lambda-layer.zip *"
        }
      }
    }

    stage('Archive artifacts') {
      when {
        branch 'master'
      }
      steps {
        archiveArtifacts "build/${env.LAYER_NAME}-lambda-layer.zip"

        withCredentials([file(credentialsId: '69902ef6-1a24-4740-81fa-7b856248987d', variable: 'AWS_SHARED_CREDENTIALS_FILE')]) {
          sh """
            aws s3 cp \
              ${env.WORKSPACE}/build/${env.LAYER_NAME}-lambda-layer.zip \
              s3://${env.AWS_BUCKET_NAME}/
          """.stripIndent()

          sh """
            aws lambda publish-layer-version \
              --region ${env.AWS_REGION} \
              --layer-name ${env.LAYER_NAME}-lambda-layer \
              --description "${env.LAYER_DESCRIPTION}" \
              --compatible-runtimes python${PYTHON_VERSION} \
              --license-info "${env.LICENSE_IDENTIFIER}" \
              --content S3Bucket=${env.AWS_BUCKET_NAME},S3Key=${env.LAYER_NAME}-lambda-layer.zip
          """.stripIndent()

          withCredentials([string(credentialsId: '92c99606-a8c6-44cc-9f67-718f3dfea120', variable: 'LAYER_UPDATER_ARN')]) {
            // note: we're ignoring the response.json contents deliberately
            script {
              def payload = [
                runtime: 'python' + PYTHON_VERSION,
                layer_name: env.LAYER_NAME + '-lambda-layer'
              ]
              writeJSON file: './payload.json', json: payload
              sh """
                aws lambda invoke \
                  --region ${env.AWS_REGION} \
                  --function-name "${env.LAYER_UPDATER_ARN}" \
                  --invocation-type Event \
                  --payload fileb://./payload.json \
                  response.json
              """.stripIndent()
            }
          }
        }
      }
    }
  }
}
