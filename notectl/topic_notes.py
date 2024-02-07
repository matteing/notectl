#!/usr/bin/env python3

import os
import argparse
from pathlib import Path

AUTOINDEX_TEMPLATE = """
## Backlinks
<autoindex>
</autoindex>

## To-do
<autoindex filterByTags="#todo">
</autoindex>

## Clippings
<autoindex filterByTags="#reference">
</autoindex>
""".strip(
    "\n"
)

TEMPLATE = """
# {topic_name}

{autoindex_section}
""".strip(
    "\n"
)


def create_topic_file(path, topic_name, with_autoindex=True):
    file_name = f"{topic_name}.md"
    file_path = Path(path) / file_name

    if not file_path.exists():
        with file_path.open("w") as f:
            f.write(TEMPLATE.format(topic_name=topic_name, autoindex_section=AUTOINDEX_TEMPLATE if with_autoindex else ""))

    return file_path


def open_in_ia_writer(file_path):
    os.system(f"open -a 'iA Writer' '{file_path}'")


def main():
    default_path = Path.home() / "iCloud" / "Notes" / "Topics"

    parser = argparse.ArgumentParser(description="Create and open an index file.")
    parser.add_argument("topic_name", help="Name of the topic for the file")
    parser.add_argument(
        "--path",
        default=default_path,
        help="Path to the directory where notes will be stored.",
    )
    args = parser.parse_args()

    file_path = create_topic_file(args.path, args.topic_name)

    open_in_ia_writer(file_path)


if __name__ == "__main__":
    main()
