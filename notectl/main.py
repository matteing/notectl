import typer

from .topic_notes import create_topic_file
from .daily_notes import create_daily_file
from .attachments import run_collector
from .editor import open_in_editor
from .config import (
    get_config_file,
    init_config_file,
    does_config_exist,
    get_config_value,
    get_vault_folder_path,
    get_vault_path
)
from rich import print
from rich.prompt import Confirm
from typing_extensions import Annotated
from .autoindex import run_autoindex

app = typer.Typer()
config_app = typer.Typer()
app.add_typer(config_app, name="config")
daily_app = typer.Typer()
app.add_typer(daily_app, name="daily")
topics_app = typer.Typer()
app.add_typer(topics_app, name="topics")
attachments_app = typer.Typer()
app.add_typer(attachments_app, name="attachments")
autoindex_app = typer.Typer()
app.add_typer(autoindex_app, name="autoindex")


@app.callback(invoke_without_command=True)
def callback(ctx: typer.Context):
    """
    A simple note management tool.
    """
    config_file = get_config_file()
    if config_file is None and ctx.invoked_subcommand != "init":
        print(
            "No configuration found. Please run [bold cyan]notectl config init[/bold cyan]."
        )
        raise typer.Exit(code=1)


@config_app.callback()
def config_callback():
    """
    Manages the configuration file.
    """
    pass


@daily_app.callback()
def daily_callback():
    """
    Manages daily notes.
    """
    pass


@topics_app.callback()
def topics_callback():
    """
    Manages topics.
    """
    pass

@attachments_app.callback()
def attachments_callback():
    """
    Manages attachments.
    """
    pass

@autoindex_app.callback()
def autoindex_callback():
    """
    Manages the autoindexer.
    """
    pass

@config_app.command("init")
def config_init(
    preset_file: Annotated[
        str, "Uses a preset file in /conf for the config generation."
    ] = "default.toml"
):
    """
    Initializes the configuration file.
    """
    if does_config_exist():
        should_overwrite = Confirm.ask(
            "[yellow]Configuration file already exists, are you sure you want to overwrite it?[/yellow]",
            default=False,
        )
        if not should_overwrite:
            print("Aborting.")
            raise typer.Exit(code=0)
    config_file = init_config_file(preset_file)
    print(f"[bold green]Configuration file created at {config_file}[/bold green]")
    should_edit = Confirm.ask(
        "Do you want to edit the configuration file?", default=True
    )
    if should_edit:
        typer.edit(None, filename=config_file)


@config_app.command("open")
def config_open():
    """
    Opens the configuration file in the default text editor.
    """
    config_file = get_config_file()
    if config_file is None:
        print("No configuration file found.")
        raise typer.Exit(code=1)
    typer.edit(None, filename=config_file)


@daily_app.command("today")
def daily_today(
    date_format: Annotated[
        str, "The format for the date in the filename."
    ] = "%B %-d, %Y",
    with_autoindex: Annotated[bool, "Whether to include an autoindex section."] = False,
):
    """
    Opens today's note. The note is created if it doesn't exist.

    The note is created in the directory specified by the "daily_notes" configuration option.
    """
    should_autoindex = get_config_value(
        "daily_notes", "with_autoindex", assert_value=False
    )
    daily_notes_path = get_vault_folder_path("daily_notes_folder")
    note_path = create_daily_file(
        daily_notes_path,
        date_format,
        with_autoindex=with_autoindex if with_autoindex else should_autoindex,
    )
    open_in_editor(note_path)


@daily_app.command("tomorrow")
def daily_tomorrow(
    date_format: Annotated[
        str, "The format for the date in the filename."
    ] = "%B %-d, %Y",
    with_autoindex: Annotated[bool, "Whether to include an autoindex section."] = False,
):
    """
    Opens tomorrow's note. The note is created if it doesn't exist.

    The note is created in the directory specified by the "daily_notes" configuration option.
    """
    should_autoindex = get_config_value(
        "daily_notes", "with_autoindex", assert_value=False
    )
    daily_notes_path = get_vault_folder_path("daily_notes_folder")
    note_path = create_daily_file(
        daily_notes_path,
        date_format,
        with_autoindex=with_autoindex if with_autoindex else should_autoindex,
        is_tomorrow=True,
    )
    open_in_editor(note_path)


@topics_app.command("new")
def topics_new(
    name: str,
    with_autoindex: Annotated[bool, "Whether to include an autoindex section."] = False,
):
    """
    Creates a new topic note. The note is created in the directory specified by the "topics" configuration option.
    """
    should_autoindex = get_config_value(
        "topic_notes", "with_autoindex", assert_value=False
    )
    topics_path = get_vault_folder_path("topic_notes_folder")
    note_path = create_topic_file(
        topics_path,
        name,
        with_autoindex=with_autoindex if with_autoindex else should_autoindex,
    )
    open_in_editor(note_path)

@attachments_app.command("tidy")
def attachments_tidy(
    dry_run: Annotated[bool, "Whether to perform a dry run."] = False
):
    """
    Collects all attachments and moves them to the attachments folder.
    """
    vault_root = get_vault_path()
    folders_to_tidy = get_config_value("attachments", "folders_to_tidy", assert_value=True)
    resolved_paths = [(vault_root / folder).resolve(strict=True) for folder in folders_to_tidy]
    attachments_folder = get_vault_folder_path("attachments_folder")
    run_collector(attachments_folder, resolved_paths, dry_run=dry_run)

@autoindex_app.command("run")
def autoindex_run():
    """
    Runs the autoindexer.
    """
    vault_root = get_vault_path()
    run_autoindex(input_path=vault_root)
    

if __name__ == "__main__":
    app()
