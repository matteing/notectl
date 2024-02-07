from pathlib import Path
from platformdirs import user_config_dir
import tomllib
import typer
from rich import print

APP_NAME = "notectl"
APP_AUTHOR = "matteing"

CONFIG_DIR = user_config_dir(APP_NAME, APP_AUTHOR)
CONFIG_FILE_NAME = "config.toml"

def init_config_dir() -> Path:
  config_dir = Path(CONFIG_DIR)
  config_dir.mkdir(parents=True, exist_ok=True)
  return config_dir

def get_default_config(preset_file: str = CONFIG_FILE_NAME) -> str:
  script_dir = Path(__file__).resolve().parent
  default_config = script_dir / "conf" / preset_file
  with default_config.open() as f:
    return f.read()
    
def does_config_exist() -> bool:
  config_path = Path(CONFIG_DIR)
  config_file = config_path / CONFIG_FILE_NAME
  return config_file.exists()

def init_config_file(preset_file: str = CONFIG_FILE_NAME) -> Path:
  config_path = init_config_dir()
  config_file = config_path / CONFIG_FILE_NAME
  if not config_file.exists():
    config_file.touch()
  default_config = get_default_config(preset_file)
  # Write to config_file
  with config_file.open("w") as f:
    f.write(default_config)
  return config_file

def get_config_file(assert_exists=False) -> Path | None:
  """ 
  The app should exit on non-existing configuration.
  """
  config_path = Path(CONFIG_DIR)
  config_file = config_path / CONFIG_FILE_NAME
  if not config_file.exists():
    if assert_exists:
      print("[bold red]No configuration file found.[/bold red]")
      raise typer.Exit(code=1)
    return None
  return config_file

def get_config_value(section: str, key: str, assert_value=True) -> str | None:
  config_file = get_config_file(assert_exists=True)
  if config_file is None:
    return None
  with config_file.open("rb") as f:
    config = tomllib.load(f)
  try:
    val = config[section][key]
    if assert_value:
      val = assert_value_exists(f"{section}.{key}", val)
    return val
  except KeyError:
    print(f"[bold red]Error:[/bold red] Configuration file is missing the following key: {section}.{key}")
    raise typer.Exit(code=1)

def assert_config_exists(path: Path | None) -> None:
  if path is None:
    print("No configuration file found.")
    raise typer.Exit(code=1)

def assert_value_exists(key: str, value: str | None) -> str:
  if value is None:
    print(f"[bold red]Error:[/bold red] Configuration file returned None for value: {key}")
    raise typer.Exit(code=1)
  return value

def get_vault_path() -> Path:
  vault_path = get_config_value("paths", "root", assert_value=True)
  return Path(vault_path).resolve(strict=True)

def get_vault_folder_path(key: str) -> Path:
  root_path = get_vault_path()
  folder_path = get_config_value("paths", key, assert_value=True)
  return (root_path / folder_path).resolve(strict=True)