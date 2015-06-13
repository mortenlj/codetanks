package ibidem.gradle.python

import javax.inject.Inject

import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.api.artifacts.Dependency
import org.gradle.api.internal.DefaultDomainObjectSet
import org.gradle.api.internal.artifacts.DefaultDependencySet
import org.gradle.api.internal.file.FileResolver

class PythonPlugin implements Plugin<Project> {
    private final FileResolver fileResolver
    private File pythonBuildRoot

    @Inject
    PythonPlugin(FileResolver fileResolver) {
        this.fileResolver = fileResolver
    }

    void apply(Project project) {
        pythonBuildRoot = new File(project.buildDir, 'python')
        project.configure(project) {
            project.configurations.create('python')
            CollectPython collect = project.tasks.create(CollectPython.NAME, CollectPython.class) {
                targetDir = new File(pythonBuildRoot, 'collect')
                inputs.source('src/main/python')
                outputs.dir(targetDir)
            }
            GenerateSetup setup = project.tasks.create(GenerateSetup.NAME, GenerateSetup.class) {
                sourceDir = collect.targetDir
                dependsOn CollectPython.NAME
            }
            BuildPython build = project.tasks.create(BuildPython.NAME, BuildPython.class) {
                outputDir = pythonBuildRoot
                dependsOn GenerateSetup.NAME
                inputs.source(collect.targetDir)
                outputs.dir(outputDir)
            }
            TestPython test = project.tasks.create(TestPython.NAME, TestPython.class) {
                dependsOn BuildPython.NAME
                testDir 'src/test/python'
            }

            afterEvaluate {
                def pythonDependencies = project.configurations.getByName('python')
                        .dependencies.collect { dep -> new PythonDependency(dep.name, dep.version) }
                def domainObjectSet = new DefaultDomainObjectSet<Dependency>(PythonDependency.class, pythonDependencies)
                setup.dependencies = new DefaultDependencySet("python dependencies", domainObjectSet)

                project.tasks.getByName('assemble').dependsOn(BuildPython.NAME)
                project.tasks.getByName('test').dependsOn(TestPython.NAME)
            }
        }

        //developPythonTask(project)
    }
/*
    private static developPythonTask(Project project) {
        def options = [
            (Task.TASK_TYPE): DevelopPythonTask.class,
            (Task.TASK_DEPENDS_ON): ['generateSetup', 'buildPython'],
            (Task.TASK_DESCRIPTION): 'Install python-package in "development mode"'
        ]
        project.task(options, 'develop')
    }
*/
}
