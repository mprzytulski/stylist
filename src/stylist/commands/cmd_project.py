from stylist.cli import stylist_context
from stylist.commands import cli_prototype

cli = cli_prototype
cli.short_help = "Stylist project helper"


@cli.command(help="Initialise new project")
@stylist_context
def init(ctx):
    pass


@cli.command(name="update-templates", help="Update project templates")
@stylist_context
def update_templates(ctx):
    pass
