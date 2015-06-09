package ibidem.gradle.python

import groovy.text.SimpleTemplateEngine
import org.gradle.api.DefaultTask
import org.gradle.api.artifacts.DependencySet
import org.gradle.api.file.FileVisitDetails
import org.gradle.api.tasks.TaskAction
import org.slf4j.Logger
import org.slf4j.LoggerFactory

/**
 * Assemble sourceSets into a directory under buildDir, pointed to by setup.py
 *
 * TODO: Optionally apply closure to each file copied (to enable namespace fixing)
 */
class BuildPythonTask extends DefaultTask {
    private static final Logger LOG = LoggerFactory.getLogger(BuildPythonTask.class)
    public static final NAME = 'buildPython'

    DependencySet dependencies
    String targetDir
    File setupTemplate
    File setup
    Closure collector

    BuildPythonTask() {
        description = 'Builds the python source'
        setupTemplate = project.file('setup.py.in')
        inputs.source('src/main/python').file(setupTemplate)

        targetDir = "${project.buildDir}/python"
        setup = project.file('setup.py')
        outputs.dir(targetDir).file(setup)

        collector = { FileVisitDetails details, File target ->
            details.copyTo(target)
        }
    }

    @TaskAction
    def build() {
        generate()
        collectFiles()
        project.exec {
            executable = 'python'
            args = ['setup.py', 'build']
        }
    }

    def generate() {
        def engine = new SimpleTemplateEngine()
        def template = engine.createTemplate(setupTemplate)
        def binding = [
                version     : pythonicVersion(),
                package_dir : targetDir,
                requirements: requirements()
        ]
        LOG.info("Generating ${setup}")
        setup.withWriter {
            template.make(binding).writeTo(it)
        }
    }

    def collectFiles() {
        inputs.sourceFiles.asFileTree.visit { FileVisitDetails details ->
            def target = new File(targetDir, details.relativePath.toString())
            if (details.isDirectory() && !target.exists()) {
                target.mkdirs()
            } else if (details.name == 'setup.py') {
                // skip
            } else {
                LOG.info("Collecting ${details.relativePath} => ${target}")
                collector(details, target)
            }
        }
    }

    def requirements() {
        def all = dependencies.collect {
            "'${it.pythonReq}'"
        }
        def joined = all.join(', ')
        "($joined)"
    }

    def pythonicVersion() {
        def version = project.version.toString()
        version.replace("-SNAPSHOT", "-dev")
    }
}
