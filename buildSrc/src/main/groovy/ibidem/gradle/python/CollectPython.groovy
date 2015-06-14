package ibidem.gradle.python

import org.gradle.api.DefaultTask
import org.gradle.api.Task
import org.gradle.api.file.FileVisitDetails
import org.gradle.api.tasks.TaskAction
import org.slf4j.Logger
import org.slf4j.LoggerFactory

/**
 * Collect sources from all inputs into single location
 */
class CollectPython extends DefaultTask {
    private static final Logger LOG = LoggerFactory.getLogger(CollectPython.class)
    public static final NAME = 'collectPython'

    Map<String, File> paths
    Closure collector

    CollectPython() {
        description = 'Builds the python source'
        collector = { FileVisitDetails details, File target ->
            details.copyTo(target)
        }
    }

    @Override
    Task configure(Closure closure) {
        def task = super.configure(closure)
        inputs.source('src/main/python')
        outputs.dir(paths.collectedSources)
        return task
    }

    @TaskAction
    def collect() {
        inputs.sourceFiles.asFileTree.visit { FileVisitDetails details ->
            def target = new File(paths.collectedSources, details.relativePath.toString())
            if (details.isDirectory() && !target.exists()) {
                target.mkdirs()
            } else {
                LOG.info("Collecting ${details.relativePath} => ${target}")
                collector(details, target)
            }
        }
    }

}
