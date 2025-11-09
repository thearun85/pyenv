import logging
import sys
import os
import types
import shutil
import subprocess
import venv

# Set the log level to Info
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

# This is the function where all the actions are performed.
def launch():
    env_dir = os.getcwd()
    if len(sys.argv) <= 1:
        env_dir = os.path.join(env_dir, 'venv')
        log.info("virtual environment directory defaulting to current working directory")
    else:
        env_dir = os.path.abspath(sys.argv[1])

    # Virtual environment is created either in teh directory specified by the user. If this is empty, then the a folder "venv" will be created in the current working directory.

    env_details = types.SimpleNamespace()
    
    # Python execution environment for the host system
    executable = sys._base_executable

    # Python installation directory and the executable for the host system
    env_details.pydir, env_details.pyexec =     os.path.split(sys._base_executable)

    env_details.cwd = os.getcwd()

    # Virtual environment directory
    env_details.env_dir = env_dir

    env_details.env_name = os.path.split(env_details.env_dir)[1]
    env_details.prompt = env_details.env_name

    # various folders created for the virtual environment.
    # bin will hold the executable, the activation and deactivation scripts.
    env_details.bin_name = 'bin'
    env_details.bin_path = os.path.join(env_dir, env_details.bin_name)

    # include folders will hold all the custome packages for the installation
    env_details.incl_path = os.path.join(env_dir, 'include')

    # lib folder will have the python setup files
    env_details.lib_path = os.path.join(env_dir, 'lib')
    env_details.envexec = os.path.join(env_details.bin_path, env_details.pyexec)
   
    if not os.path.exists(env_details.env_dir):
        os.makedirs(env_details.env_dir)
        os.makedirs(env_details.bin_path)
        os.makedirs(env_details.incl_path)
        os.makedirs(env_details.lib_path)

    # the python confoguration file. The presence of this file tells the python interpreter that this is a virtual environment.
    env_details.cfg_path = os.path.join(env_details.env_dir, 'pyvenv.cfg')
    
    with open(env_details.cfg_path, 'w') as f:
        f.write(f"home = {env_details.cfg_path}\n")
        f.write("include-system-site-packages = False\n")
        f.write(f"version = {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}\n")
    log.info(f"env exec is {env_details.envexec}")

    # copy the python executable from the host system to the virtual environment
    shutil.copyfile(sys._base_executable, env_details.envexec)
    os.chmod(env_details.envexec, 0o755)
    
    # setup pip in the virtual environment
    try:
        cmd = [env_details.envexec, '-Im', 'ensurepip', '--upgrade', '--default-pip']
        subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
    except subprocess.CalledProcessError as e:
        log.error(f"pip installation failed with {e}")

    
    # copy the activation shell script from python core module. Reusing the script instead of a new file. Set all the environment variables before copying the activation script.
    srcfile = os.path.join(os.path.dirname(venv.__file__), 'scripts', 'common', 'activate')
    dstfile = os.path.join(env_details.bin_path, "activate")
    
    with open(srcfile, 'rb') as f:
        data = f.read()

    try:
        data = data.decode('utf-8')
        data = data.replace('__VENV_DIR__', env_details.env_dir)
        data = data.replace('__VENV_NAME__', env_details.env_name)
        data = data.replace('__VENV_PROMPT__', env_details.prompt)
        data = data.replace('__VENV_BIN_NAME__', env_details.bin_name)
        data = data.replace('__VENV_PYTHON__', env_details.envexec)
        data = data.encode('utf-8')
    except UnicodeError as e:
        log.exception("unable to copy activation script")
        data = None

    # change the file mode for the activation script
    if data is not None:
        with open(dstfile, 'wb') as f:
            f.write(data)
        shutil.copymode(srcfile, dstfile)


if __name__ == '__main__':
    rc = 1
    if sys.platform != 'darwin':
        log.error("This virtual environment supports only mac os!")
    else:
    
        try:
            launch()
            rc=0
        except Exception as e:
            log.exception("virtual environment creation failed")

    sys.exit(rc)
    
