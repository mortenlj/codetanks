package ibidem.gradle.python

import groovy.text.SimpleTemplateEngine
import org.gradle.api.DefaultTask
import org.gradle.api.artifacts.DependencySet
import org.gradle.api.tasks.TaskAction
import org.slf4j.Logger
import org.slf4j.LoggerFactory

class GenerateSetup extends DefaultTask {
    private static final Logger LOG = LoggerFactory.getLogger(GenerateSetup.class)
    public static final String NAME = 'generateSetup'

    DependencySet dependencies
    String sourceDir
    File setupTemplate
    File setup

    GenerateSetup() {
        description = 'Generate the setup.py used be later tasks'
        setupTemplate = project.file('setup.py.in')
        inputs.file(setupTemplate)
        setup = project.file('setup.py')
        outputs.file(setup)
    }

    @TaskAction
    def generate() {
        def engine = new SimpleTemplateEngine()
        def template = engine.createTemplate(setupTemplate)
        def binding = [
                version     : pythonicVersion(),
                package_dir : sourceDir,
                requirements: requirements()
        ]
        LOG.info("Generating ${setup}")
        setup.withWriter {
            template.make(binding).writeTo(it)
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
