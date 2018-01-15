from invoke import task


@task
def lint(ctx):
    ctx.run('flake8 --max-line-length=120 --import-order-style=pep8 stylist')

@task
def test(ctx):
    ctx.run('nosetests tests/')
