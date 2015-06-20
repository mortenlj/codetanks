package ibidem.gradle.python

import javax.inject.Inject

import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.api.internal.file.FileResolver
import org.gradle.language.base.plugins.LifecycleBasePlugin

class PythonPlugin implements Plugin<Project> {
    private final FileResolver fileResolver

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
                distTemp: new File(root, 'distTemp'),
                distFinal: new File(root, 'dist')
        ]
    }

    void apply(Project project) {
        project.getPluginManager().apply(LifecycleBasePlugin.class);
        def myPaths = definePaths(project.buildDir)
        project.configure(project) {
            CollectPython collect = project.tasks.create(CollectPython.NAME, CollectPython.class) {
                paths = myPaths
            }
            GenerateSetup setup = project.tasks.create(GenerateSetup.NAME, GenerateSetup.class) {
                paths = myPaths
            }
            BuildPython build = project.tasks.create(BuildPython.NAME, BuildPython.class) {
                paths = myPaths
                dependsOn GenerateSetup.NAME, CollectPython.NAME
            }
            TestPython test = project.tasks.create(TestPython.NAME, TestPython.class) {
                dependsOn BuildPython.NAME
            }
            InstallPython install = project.tasks.create(InstallPython.NAME, InstallPython.class) {
                paths = myPaths
                dependsOn BuildPython.NAME
            }

            afterEvaluate {
                attachTask(project, TestPython.NAME, LifecycleBasePlugin.CHECK_TASK_NAME, LifecycleBasePlugin.VERIFICATION_GROUP)
                attachTask(project, BuildPython.NAME, LifecycleBasePlugin.ASSEMBLE_TASK_NAME, LifecycleBasePlugin.BUILD_GROUP)
                attachTask(project, InstallPython.NAME, 'install', null)
            }
        }
    }

    static def attachTask(Project project, String taskName, String parentName, String group) {
        def parent = project.tasks.findByName(parentName)
        if (parent == null) {
            parent = project.tasks.create(parentName)
            parent.group = group
        }
        parent.dependsOn(taskName)
    }
}
