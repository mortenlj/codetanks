package ibidem.gradle.python

import groovy.text.SimpleTemplateEngine
import org.gradle.api.DefaultTask
import org.gradle.api.Task
import org.gradle.api.tasks.TaskAction
import org.slf4j.Logger
import org.slf4j.LoggerFactory

class GenerateSetup extends DefaultTask {
    private static final Logger LOG = LoggerFactory.getLogger(GenerateSetup.class)
    public static final String NAME = 'generateSetup'

    Map<String, File> paths
    Map<DependencyCollection.Type, DependencyCollection> deps
    File setupTemplate
    File setup
    File config

    GenerateSetup() {
        description = 'Generate the setup.py used be later tasks'
        setupTemplate = project.file('setup.py.in')
        inputs.file(setupTemplate)
        deps = [:]
        DependencyCollection.Type.values().each {
            def name = "${it.prefix}requirements.txt"
            def file = project.file(name)
            if (file.exists()) {
                inputs.file(file)
                deps[it] = new DependencyCollection(file)
            }
        }
    }

    @Override
    Task configure(Closure closure) {
        def task = super.configure(closure)
        setup = new File(paths.root, 'setup.py')
        paths.setup = setup
        outputs.file(setup)
        config = new File(paths.root, 'setup.cfg')
        outputs.file(config)
        return task
    }

    @TaskAction
    def generate() {
        if (!paths.root.exists()) {
            paths.root.mkdirs()
        }
        generateSetup()
        generateConfig()
    }

    private generateConfig() {
        def cfg = [
                bdist_egg  : [bdist_dir: paths.distTemp, dist_dir: paths.distFinal, skip_build: 1],
                build      : [build_base: paths.buildTarget],
                build_py   : [build_lib: paths.buildTarget, optimize: 2],
                egg_info   : [egg_base: paths.eggInfo],
                install    : [optimize: 2, skip_build: 1],
                install_lib: [build_dir: paths.buildTarget, optimize: 2, skip_build: 1],

        ]
        LOG.info("Generating ${config}")
        config.withWriter { writer ->
            cfg.each { command, options ->
                writer.write("[$command]\n")
                options.each { k, v ->
                    writer.write("$k=$v\n")
                }
                writer.write('\n')
            }
        }
    }

    private generateSetup() {
        def engine = new SimpleTemplateEngine()
        def template = engine.createTemplate(setupTemplate)
        def binding = [
            version     : pythonicVersion(),
            package_dir : paths.collectedSources
        ]
        deps.each { k, v ->
            binding["${k.prefix}requirements"] = v.requirements()
        }
        LOG.info("Generating ${setup}")
        setup.withWriter {
            template.make(binding).writeTo(it)
        }
    }

    def pythonicVersion() {
        def version = project.version.toString()
        version.replace("-SNAPSHOT", "-dev")
    }
}
