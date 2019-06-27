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
        [$class: 'JobRestrictionProperty'],
        gitLabConnection("Gitlab"),
    ])
    gitlabCommitStatus("jenkins-pipeline"){
        com.mintel.jenkins.EverestPipeline.builder(this)
            .withPythonPackage()
            .build()
            .execute()
    }
}
