package ibidem.gradle.python

import javax.inject.Inject

import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.api.artifacts.Dependency
import org.gradle.api.internal.DefaultDomainObjectSet
import org.gradle.api.internal.artifacts.DefaultDependencySet
import org.gradle.api.internal.file.FileResolver

/*
TODO:
    - Connect test to build task?
    - If java-plugin is not applied, create necessary build and install tasks
    - Remove dependencies in build.gradle, they should be in requirements, test_requirements and setup_requirements
    - Set more properties in generated setup.py:
        - project name
        - metadata? (Does gradle have standard metadata support?)
*/

class PythonPlugin implements Plugin<Project> {
    private final FileResolver fileResolver
    private File pythonBuildRoot

    @Inject
    PythonPlugin(FileResolver fileResolver) {
        this.fileResolver = fileResolver
    }

    private static Map<String, File> definePaths(File buildDir) {
        File root = new File(buildDir, 'python')
        [
                root: root,
                collectedSources: new File(root, 'collect'),
                buildTarget: new File(root, 'target'),
                eggInfo: root,
                distTemp: new File(root, 'distTemp'),
                distFinal: new File(root, 'dist')
        ]
    }

    void apply(Project project) {
        def myPaths = definePaths(project.buildDir)
        project.configure(project) {
            project.configurations.create('python')
            CollectPython collect = project.tasks.create(CollectPython.NAME, CollectPython.class) {
                paths = myPaths
            }
            GenerateSetup setup = project.tasks.create(GenerateSetup.NAME, GenerateSetup.class) {
                paths = myPaths
            }
            BuildPython build = project.tasks.create(BuildPython.NAME, BuildPython.class) {
                paths = myPaths
                dependsOn GenerateSetup.NAME
            }
            TestPython test = project.tasks.create(TestPython.NAME, TestPython.class) {
                dependsOn BuildPython.NAME
            }
            InstallPython install = project.tasks.create(InstallPython.NAME, InstallPython.class) {
                paths = myPaths
                dependsOn BuildPython.NAME
            }

            afterEvaluate {
                def pythonDependencies = project.configurations.getByName('python')
                        .dependencies.collect { dep -> new PythonDependency(dep.name, dep.version) }
                def domainObjectSet = new DefaultDomainObjectSet<Dependency>(PythonDependency.class, pythonDependencies)
                setup.dependencies = new DefaultDependencySet("python dependencies", domainObjectSet)

                project.tasks.getByName('assemble').dependsOn(BuildPython.NAME)
                project.tasks.getByName('test').dependsOn(TestPython.NAME)
                project.tasks.getByName('install').dependsOn(InstallPython.NAME)
            }
        }
    }
}
