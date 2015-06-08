package ibidem.gradle.python

import javax.inject.Inject

import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.api.internal.file.FileResolver

class PythonPlugin implements Plugin<Project> {
    private final FileResolver fileResolver

    @Inject
    PythonPlugin(FileResolver fileResolver) {
        this.fileResolver = fileResolver
    }

    void apply(Project project) {
        project.configure(project) {
            project.configurations.create('main')
            project.configurations.create('develop')
            BuildPythonTask build = project.tasks.create(BuildPythonTask.NAME, BuildPythonTask.class)
            def python = project.extensions.create('python', Python.class, project, build)

            afterEvaluate {
                build.dependencies = project.configurations.getByName('main').dependencies

                project.tasks.getByName('assemble').dependsOn(BuildPythonTask.NAME)
            }
        }

        //developPythonTask(project)
        //testPythonTask(project)
    }
/*
    private static testPythonTask(Project project) {
        def options = [
            (Task.TASK_TYPE): TestPythonTask.class,
            (Task.TASK_DEPENDS_ON): ['generateSetup', 'buildPython'],
            (Task.TASK_GROUP): LifecycleBasePlugin.VERIFICATION_GROUP,
            (Task.TASK_DESCRIPTION): 'Test python code'
        ]
        def test = project.task(options, 'testPython')
        project.getTasks().getByName('test').dependsOn test
    }


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
