import click

from stylist.core.click import GroupPrototype

cli = GroupPrototype.create('Manage stylist features')


@cli.command('add-feature', help="Add new feature to current project")
@click.argument('feature')
@click.argument('init_args', nargs=-1, type=click.UNPROCESSED)
@click.pass_obj
def add_feature(ctx, feature, init_args):
    pass
    # @todo: implement
    # try:
    #     f = get_feature(feature, ctx)
    #     f.setup(init_args)
    #
    #     click.secho('Feature "{}" has been added to your project'.format(feature), fg='green')
    # except FeatureException as e:
    #     click.secho(e.message, fg='red')
    #     sys.exit(1)


@cli.command('list-features', help="List all available features")
@click.pass_obj
def list_features(stylist):
    pass
    # @todo: implement
    # features = []
    # for feature, inst in list_features().items():
    #     features.append([
    #         feature,
    #         str(inst.__doc__ or '').strip(),
    #         click.style('true', fg='green') if feature in stylist.features else 'false'
    #     ])
    #
    # click.secho(
    #     table("STYLIST FEATURES", features, ["FEATURE", "DESCRIPTION", "INSTALLED"]).table
    # )
