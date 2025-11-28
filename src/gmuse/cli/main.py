import typer
from gmuse import __version__

app = typer.Typer()


def version_callback(value: bool):
    if value:
        print(__version__)
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        help="Show the version and exit.",
        is_eager=True,
        callback=version_callback,
    ),
):
    """
    gmuse: AI generated commit messages.
    Run with --help for more info.
    """
    pass


app.command()
