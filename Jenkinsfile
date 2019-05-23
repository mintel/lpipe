@Library('everest-shared') _
node('docker&&virtualenv') {
    properties([
        buildDiscarder(
            logRotator(
                artifactDaysToKeepStr: '14',
                artifactNumToKeepStr: '30',
                daysToKeepStr: '14',
                numToKeepStr: '30'
            )
        ),
        [$class: 'JobRestrictionProperty']
    ])
    gitlabCommitStatus("jenkins-pipeline"){
        com.mintel.jenkins.EverestPipeline.builder(this)
            .withFlowdockNotification("bac6aea4efa3cbee8a7e7169a8a800ab")
            .withPythonPackage()
            .build()
            .execute()
    }
}
