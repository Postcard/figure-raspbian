
from fabric.api import task, env
from fabric.operations import local

env.force = False

@task
def integration():
    env.remotes = ['resinintegration_raspi2', 'resinintegration_raspi3']

@task
def production():
    env.remotes = ['resinproduction_raspi2', 'resinproduction_raspi3']

@task
def force():
    env.force = True

@task
def deploy(branch="master"):
    for remote in env.remotes:
        cmd = ['git', 'push']
        if env.force:
            cmd.append('--force')
        cmd.append(remote)
        cmd.append('%s:master' % branch)
        cmd = ' '.join(cmd)
        local(cmd)
