from pybuilder.core import task, use_plugin, init, Author, depends
from pybuilder.errors import BuildFailedException
from pip._internal import main as pipmain
import os
import shutil
import subprocess

use_plugin('copy_resources')
use_plugin('filter_resources')

use_plugin("python.core")
use_plugin("python.unittest")
use_plugin("python.install_dependencies")
use_plugin("python.flake8")
use_plugin("python.coverage")
use_plugin("python.distutils")
use_plugin('python.integrationtest')

name = "smart-reader-app"
summary = "SmartReader"
description = "SmartReader es una herramienta que utiliza técnicas de Procesamiento de Lenguaje Natural para " \
              "proporcionar una nueva perspectiva a tu investigación (pregunta de investigación y " \
              "literatura recopilada). Esto lo hace a través de consultar a Google y recuperar información actualizada" \
              " y relacionada con tu pregunta de investigación. SmartReader es una alternativa para hacerle frente " \
              "a la necesidad que tienen los trabajadores de conocimiento de mantener el ritmo a la cantidad " \
              "exponencial de información que se genera todos los días y que se comparte en el internet."
url = "https://dev-git.labs.gmv.com/idb-smartreader/smart-reader-app.git"
authors = [Author("GMV", "bda@gmv.com")]

version = '0.4.0'
default_task = ["clean", "install_dependencies", "analyze", "publish", "publish_distribution"]

mvn_group_id = "com.gmv.smart-reader-app"


@init
def initialize(project):
    project.depends_on_requirements("requirements.txt")

    project.build_depends_on("mockito")
    project.build_depends_on("mock")

    project.set_property("verbose", True)

    project.set_property('flake8_verbose_output', True)
    project.set_property('flake8_include_test_sources', True)
    project.set_property('flake8_break_build', False)

    project.set_property('distutils_console_scripts',
                         ['smart_reader_app = smart_reader_app.__main__:main'])

    project.set_property('distutils_upload_repository', 'dein')

    project.set_property("coverage_break_build", False)
    project.set_property("coverage_reset_modules", True)
    project.get_property("coverage_exceptions").append("pybuilder.cli")
    project.get_property("coverage_exceptions").append("pybuilder.plugins.core_plugin")

    project.include_file("smart_reader_app", "templates/*")
    project.include_file("smart_reader_app", "static/**/**/*")

    project.set_property("pdoc_module_name", "smart_reader_app")

    project.set_property('distutils_upload_repository', 'dein')


@task("publish_distribution", description="Publish distribution package.")
@depends("publish")
def publish_distribution(project, logger):
    # find project module
    dist_path = distpath(project)
    package_filepath, package_filename = find_package(project, '.whl', logger)

    # $dir_dist/lib
    distribution_path = distributionpath(project)
    download_dependencies(project, logger)

    # Copiar el distributable de {project.name} dentro de $dir_dist/distribution/lib
    module_wheel_destination = os.path.join(distribution_path, "lib", package_filename)
    shutil.copyfile(package_filepath, module_wheel_destination)

    # Crear paquete distribution {project.name}-{project.version}-{distribution}.zip dentro de $dir_dist/dist
    distribution_filename = os.path.join(dist_path, "-".join([os.path.splitext(package_filename)[0], "distribution"]))
    shutil.make_archive(base_name=distribution_filename, format='zip', root_dir=distribution_path, base_dir='.',
                        verbose=True, logger=logger)


@task("upload_distribution", description="Upload distribution package to maven repository.")
@depends("upload")
def upload_distribution(project, logger):
    # find project distribution
    package_filepath, distribution_filename = find_package(project, '.zip', logger)
    logger.info("Uploading distribution %s to repository 'nexus-labs' as version %s", distribution_filename,
                project.version)
    mvn_file = package_filepath.replace(os.getcwd().lower(), '.').replace("\\", "/")
    # create mvn command
    mvn = "mvn deploy:deploy-file -DgroupId={} -DartifactId={} -Dversion={} -DgeneratePom=true -Dpackaging={} -DrepositoryId={} -Durl={} -Dfile={}"
    mvn = mvn.format(mvn_group_id, project.name, project.version, "zip", "nexus-labs",
                     "\"\${gmvses.releases.repo.url}\"", mvn_file)
    # upload to maven repository
    logger.info("Maven deploy distribution start: %s", mvn)
    exitCode = run_command(mvn, logger)
    logger.info("Maven deploy distribution finish with code: %s", exitCode)
    if exitCode != 0:
        raise BuildFailedException("Error upload distribution")


def distpath(project):
    return os.path.join(project.expand_path("$dir_dist"), "dist")


def distributionpath(project):
    return os.path.join(project.expand_path("$dir_dist"), "distribution")


def find_package(project, extension, logger):
    # $dir_dist/dist
    dist_path = distpath(project)
    logger.info("Find project package in folder: %s" % dist_path)
    # return vars
    module_filepath = ""
    module_filename = ""
    # Calcular el nombre del fichero wheel
    for filename in os.listdir(dist_path):
        root, ext = os.path.splitext(filename)
        if ext == extension:
            module_filepath = os.path.join(dist_path, filename)
            module_filename = filename

    return module_filepath, module_filename


def download_dependencies(project, logger):
    # $dir_dist/lib
    distribution_lib_path = os.path.join(distributionpath(project), "lib")
    logger.info("Download dependencies in folder: %s" % distribution_lib_path)
    # Crear la tarpeta $dir_dist/lib recursivamente
    if not os.path.exists(distribution_lib_path):
        os.makedirs(distribution_lib_path)
    # Borra el contenido de la carpeta $dir_dist/lib
    else:
        for filename in os.listdir(distribution_lib_path):
            filepath = os.path.join(distribution_lib_path, filename)
            try:
                shutil.rmtree(filepath)
            except OSError:
                os.remove(filepath)
    # Generar los wheels de las dependencias
    pipmain(["wheel", "-r", "requirements.txt", "--wheel-dir", distribution_lib_path])


def run_command(command, logger):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    while True:
        output = process.stdout.readline()
        if output:
            logger.info(output.strip().decode())
        else:
            break
    return process.wait()
