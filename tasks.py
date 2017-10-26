from invoke import task


@task
def test(ctx):
    ctx.run('flake8 --max-line-length=120 --import-order-style=pep8 stylist')
