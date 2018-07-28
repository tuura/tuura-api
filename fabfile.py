from fabric.api import run
from fabric.api import cd
from fabric.api import env
from fabric.api import put
from fabric.api import local
from fabric.operations import sudo


env.host_string    = "tuura"
env.use_ssh_config = True
TUURA_API_DIR      = "/var/www/tuura.org/tuura-api"


def virtenv(command):
    run("source env/bin/activate && %s" % command)


def deploy():

    with cd(TUURA_API_DIR):

        # Deploy files
        local("tar czf /tmp/tuura-api.tar.gz $(git ls-files)")
        put("/tmp/tuura-api.tar.gz", "/tmp/tuura-api.tar.gz")
        run("tar xzf /tmp/tuura-api.tar.gz")

        # Prepare virtual environment
        run("rm -rf env")
        run("virtualenv -p python3 env")
        virtenv("pip install -qr requirements.txt")
        virtenv("./manage.py collectstatic --no-input --verbosity 0")

        # Setup systemd service
        put("tuura-api.service", "/etc/systemd/system/multi-user.target.wants/tuura-api.service", use_sudo=True)
        sudo("systemctl daemon-reload")
        sudo("systemctl restart tuura-api")
        sudo("sudo systemctl --no-pager status tuura-api")

        sudo("chown -R :www-data .")
        # run("sudo service eqweb restart")

