package ibidem.gradle.python

import java.util.stream.Collectors

import org.slf4j.Logger
import org.slf4j.LoggerFactory

class DependencyCollection {
    private static final Logger LOG = LoggerFactory.getLogger(DependencyCollection.class)

    File file
    List<PythonDependency> dependencies

    DependencyCollection(File file) {
        this.file = file
        dependencies = parse()
    }

    def parse() {
        file.readLines().stream()
            .map({ it.trim() })
            .filter({ !it.isEmpty() })
            .filter({ !it.startsWith('-f') })
            .map({
                LOG.debug("Parsing: ${it}")
                if (it.startsWith('-e')) {
                    def eggName = it.replaceFirst(/\s*-e\s+.*#egg=(.*)$/, '$1')
                    LOG.debug("Extracted egg-name: ${eggName}")
                    new PythonDependency(eggName)
                } else if (it.contains('==')) {
                    def strings = it.split('==')
                    LOG.debug("Extracted name: ${strings[0]} and version: ${strings[1]}")
                    new PythonDependency(strings[0], strings[1])
                } else {
                    LOG.debug("Just a plain name: ${it}")
                    new PythonDependency(it)
                }
            }).collect(Collectors.toList())
    }

    def requirements() {
        def all = dependencies.collect {
            "'${it.pythonReq}'"
        }
        def joined = all.join(', ')
        "[$joined]"
    }

    enum Type {
        INSTALL(''),
        SETUP('setup_'),
        TEST('test_');

        String prefix

        Type(String prefix) {
            this.prefix = prefix
        }
    }
}
