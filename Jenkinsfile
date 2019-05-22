#!/usr/bin/env groovy
def projectProperties = [
    gitLabConnection('Gitlab'),
]

properties(projectProperties)

@Library('everest-shared') _
node('docker&&virtualenv') {
    gitlabCommitStatus("jenkins-pipeline"){
        com.mintel.jenkins.EverestPipeline.builder(this)
            .withFlowdockNotification("bac6aea4efa3cbee8a7e7169a8a800ab")
            .withPythonPackage()
            .build()
            .execute()
    }
}
