import os
import glob
import argparse
import uuid
import re
from dataclasses import dataclass
from typing import List, Dict, Optional
import datetime
from .git import take_git_snapshot as take_snapshot
from pathlib import Path


@dataclass
class AutoindexConfig:
    id: str
    filters: Dict[str, str] = None
    line_start: int = None
    line_end: int = None


@dataclass
class MarkdownFile:
    path: str
    title: str
    tags: list
    links: List[str] = None
    autoindexes: List[AutoindexConfig] = None
    created_at: datetime.datetime = None
    modified_at: datetime.datetime = None


def get_file_timestamps(file_path):
    # Get the creation time in seconds since the epoch
    creation_time_seconds = os.path.getctime(file_path)

    # Get the last modified time in seconds since the epoch
    modified_time_seconds = os.path.getmtime(file_path)

    # Convert times to datetime objects
    creation_time = datetime.datetime.fromtimestamp(creation_time_seconds)
    modified_time = datetime.datetime.fromtimestamp(modified_time_seconds)

    return creation_time, modified_time


def replace_or_insert_between_lines(file_path, start_line, end_line, new_content):
    with open(file_path, "r") as file:
        old_lines = file.readlines()

    # Replace or insert content between the specified lines
    new_lines = new_content.split("\n")

    if old_lines[start_line - 1 : end_line] == new_lines:
        # Content is the same, do not print anything
        pass
    else:
        # Content is changed
        old_lines[start_line - 1 : end_line] = new_lines
        with open(file_path, "w") as file:
            file.write("".join(old_lines))
        print(f"Reindexed {file_path}")

        if len(old_lines) == 0:
            # File was empty before, so this is the first time indexing
            print(f"Indexed {file_path} for the first time")


def find_links(text):
    # Pattern to match Wikilinks, both standard and with aliases
    wikilink_pattern = r"\[\[([^|\]]+)(?:\|([^\]]+))?\]\]"

    # Pattern to match <autoindex>...</autoindex> blocks with possible attributes
    autoindex_pattern = r"<autoindex(?:\s+[^>]*)?>[\s\S]*?</autoindex>"

    # Find all matches in the text for both Wikilinks and <autoindex> blocks
    wikilinks = re.finditer(wikilink_pattern, text)
    autoindex_blocks = re.finditer(autoindex_pattern, text)

    # Convert match objects to tuples (start, end) for easier comparison
    autoindex_ranges = [(match.start(), match.end()) for match in autoindex_blocks]

    # Initialize a list to store extracted titles
    titles = []

    # Iterate through Wikilinks
    for match in wikilinks:
        wikilink_start = match.start()
        wikilink_end = match.end()

        # Check if the Wikilink is within an <autoindex> block
        if any(
            start <= wikilink_start <= end or start <= wikilink_end <= end
            for start, end in autoindex_ranges
        ):
            continue

        # Extract actual links from Wikilinks
        titles.append(match.group(1))

    return titles


def find_autoindexes(input_string) -> Optional[List[AutoindexConfig]]:
    """
    Parsing HTML-like tags using regex? Heresy!
    """
    # Define the regular expression pattern for <autoindex> tags with arbitrary attributes
    pattern = r"<autoindex(?:\s+([^<>]*))?\s*>([\s\S]*?)\s*</autoindex>"

    # Use re.finditer to find all non-overlapping matches in the entire input string
    matches = re.finditer(pattern, input_string)

    result = []
    for match in matches:
        # Extract the attributes and content
        attributes_str = match.group(1) if match.group(1) else ""
        content = match.group(2) if match.group(2) else ""

        # Parse attributes into a dictionary
        attributes = dict(re.findall(r'(\S+?)="([^"]*)"', attributes_str))

        # Get the line numbers
        line_start = input_string.count("\n", 0, match.start())
        line_end = input_string.count("\n", 0, match.end())

        # Generate random UUID for internal representation.
        id = str(uuid.uuid4())

        # Create a Python object with line numbers and attributes
        autoindex_config = AutoindexConfig(
            id, attributes, line_start=line_start, line_end=line_end
        )
        result.append(autoindex_config)

    if len(result) == 0:
        return None

    return result


def find_hashtags(text):
    hashtags = re.findall(r"\B#\w*[a-zA-Z]+\w*", text)
    return hashtags


def build_path_index(path) -> Dict[str, MarkdownFile]:
    """
    Build a dictionary of MarkdownFile objects, indexed by path.
    """
    # Get all Markdown files in the specified path
    files = glob.glob(f"{path}/**/*.md", recursive=True)
    files = [os.path.abspath(file) for file in files]

    # Create an empty dictionary
    index = {}

    # Iterate over the files
    for file in files:
        # Read the file contents
        with open(file, "r") as f:
            content = f.read()
            title = os.path.basename(file).replace(".md", "")
            autoindexes = find_autoindexes(content)
            links = find_links(content)
            tags = [tag.replace("#", "") for tag in find_hashtags(content)]
            created_at, modified_at = get_file_timestamps(file)
            markdown_file = MarkdownFile(
                file, title, tags, links, autoindexes, created_at, modified_at
            )
            index[title] = markdown_file

    return index


def get_backlinks_to_file(
    file: MarkdownFile, path_index: Dict[str, MarkdownFile]
) -> List[MarkdownFile]:
    with open(file.path, "r") as f:
        return [
            path_index[title]
            for title in path_index
            if file.title in path_index[title].links
        ]


def get_links_by_autoindex_config(
    file: MarkdownFile, path_index: Dict[str, MarkdownFile], autoindex: AutoindexConfig
) -> List[MarkdownFile]:
    if (
        "mode" in autoindex.filters.keys()
        and autoindex.filters["mode"] == "all"
        and (
            "filterByTags" in autoindex.filters.keys()
            or "filterByDate" in autoindex.filters.keys()
        )
    ):
        references = path_index.values()
    else:
        references = get_backlinks_to_file(file, path_index)
    if "filterByTags" in autoindex.filters.keys():
        tags_string = autoindex.filters["filterByTags"]
        exploded = tags_string.split(" ")
        clean_tags = [tag.replace("#", "") for tag in exploded]
        references = [
            reference
            for reference in references
            if set(reference.tags).intersection(set(clean_tags))
        ]
    if "filterByDate" in autoindex.filters.keys():
        parsed_date = datetime.datetime.strptime(
            autoindex.filters["filterByDate"], "%Y-%m-%d"
        )
        references = [
            reference
            for reference in references
            if reference.modified_at.date() == parsed_date.date()
        ]
    # Don't include itself.
    references = [
        reference for reference in references if reference.title != file.title
    ]
    return references


def render_backlinks_to_markdown_list(backlinks: List[MarkdownFile]) -> List[str]:
    if len(backlinks) == 0:
        return ["- No entries yet.\n"]
    return [
        "- [[" + file.title + "]]\n"
        for file in sorted(backlinks, key=lambda x: x.modified_at)
    ]


def apply_ids_to_autoindexes(file_content_lines, autoindexes):
    for autoindex in autoindexes:
        file_content_lines[autoindex.line_start] = file_content_lines[
            autoindex.line_start
        ].replace("autoindex", f'autoindex id="{autoindex.id}"')
    return file_content_lines


def strip_ids_from_autoindexes(file_content_lines, autoindexes):
    for autoindex in autoindexes:
        # sucks but who cares
        for idx, line in enumerate(file_content_lines):
            file_content_lines[idx] = file_content_lines[idx].replace(
                f' id="{autoindex.id}"', ""
            )
    return file_content_lines


def insert_at_autoindex(file_content_lines, autoindex, rendered_list):
    for idx, line in enumerate(file_content_lines):
        if autoindex.id in line:
            # Find the next closing tag index.
            closing_idx = None
            for closing_idx, line2 in enumerate(file_content_lines[idx:]):
                if "</autoindex>" in line2:
                    break
            if closing_idx is None:
                print(
                    f"Missing closing tag at #{autoindex.path}, line #{autoindex.line_start}."
                )
                exit(1)
            # Insert the rendered list and erase whatever is in between the two indices.
            file_content_lines[idx + 1 : idx + closing_idx] = rendered_list
    return file_content_lines


def run_autoindex(input_path: Path):
    # Take a snapshot of the directory
    take_snapshot()

    # Call the function to process the path
    index = build_path_index(input_path)

    # Get all files with <autoindex /> tags.
    autoindex_files = [file for file in index.values() if file.autoindexes is not None]
    for file in autoindex_files:
        with open(file.path, "r") as f:
            file_content_lines = f.readlines()
        # Fix indices.
        prev_content = "".join(file_content_lines)
        file_content_lines = apply_ids_to_autoindexes(
            file_content_lines, file.autoindexes
        )
        for autoindex in file.autoindexes:
            links_to_display = get_links_by_autoindex_config(file, index, autoindex)
            rendered_index = render_backlinks_to_markdown_list(links_to_display)
            file_content_lines = insert_at_autoindex(
                file_content_lines, autoindex, rendered_index
            )
        file_content_lines = strip_ids_from_autoindexes(
            file_content_lines, file.autoindexes
        )
        new_content = "".join(file_content_lines)
        if prev_content != new_content:
            print(f"Reindexed {file.path}")
        # Write!
        with open(file.path, "w") as f:
            f.write(new_content)


if __name__ == "__main__":
    run_autoindex()
