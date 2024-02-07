#!/usr/bin/env python3

import os
import re
import glob
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import List
import subprocess
from .git import take_git_snapshot as take_snapshot
from rich import print


@dataclass
class AttachmentRef:
    id: str
    kind: str
    line_num: int
    found_string: str
    # Resolved paths.
    file_path: Path
    attachment_path: Path


def resolve_attachment_path(document_origin, attachment_path) -> Path:
    if document_origin.is_file():
        document_origin = document_origin.parent
    # Combine document origin and attachment path to get an absolute path
    absolute_path = (Path(document_origin) / attachment_path).resolve()
    return absolute_path


def find_attachment_references(file_path) -> List[AttachmentRef]:
    attachments = []
    with open(file_path, "r", encoding="utf-8") as f:
        markdown_pattern = r'!\[([^\]]*)\]\(([^)]+)(?: "([^"]+)")?\)'
        ia_path_pattern = r"^\s*(?:\./|/|\.\./)[^\n]+\.\S+\s*$"

        for line_number, line in enumerate(f, start=1):
            matches = []

            path_matches = re.findall(ia_path_pattern, line, re.MULTILINE)
            matches.extend(path_matches)

            # Use re.findall to find all matches in the input text
            markdown_matches = re.findall(markdown_pattern, line)
            markdown_matches = [
                match[1]
                for match in markdown_matches
                if not match[1].startswith("http")
            ]
            matches.extend(markdown_matches)

            # Return a list of tuples containing (alt text, image URL, optional title)
            for match in matches:
                origin_path = Path(file_path)
                attachment_string = match.strip()  # .replace("\u202f", " ")
                resolved_path = resolve_attachment_path(
                    origin_path.parent, attachment_string
                )
                if not resolved_path.is_file():
                    print(
                        "[bold yellow]Not found: %s in %s:%s[/bold yellow]"
                        % (resolved_path, file_path, line_number)
                    )
                    continue
                attachments.append(
                    AttachmentRef(
                        id=str(uuid.uuid4()),
                        kind="markdown",
                        line_num=line_number,
                        found_string=attachment_string,
                        file_path=Path(file_path).resolve(),
                        attachment_path=resolved_path,
                    )
                )
    return attachments


def is_path_in_attachments_folder(attachments_folder: Path, attachment_string) -> bool:
    # Resolve the path.
    attachment_path = attachment_string.attachment_path
    return attachment_path.parent == attachments_folder


def move_to_attachments_folder(attachment: AttachmentRef, attachments_folder: Path, dry_run=False):
    new_path = attachments_folder / attachment.attachment_path.name
    if not attachment.attachment_path.is_file():
        print(f"Error: {attachment.attachment_path} does not exist.")
        return

    if new_path.is_file():
        # If the new path already exists, increment a number in the file name
        base_name = new_path.stem
        suffix = new_path.suffix
        counter = 1

        while new_path.exists():
            new_path = new_path.with_name(f"{base_name} {counter}{suffix}")
            counter += 1

    try:
        if not dry_run:
            attachment.attachment_path.rename(new_path)
        attachment.attachment_path = new_path
        # print("Moving %s to attachments" % (attachment.attachment_path.name))
    except Exception as e:
        print(f"Error while renaming: {e}")


def run_collector(attachments_folder: Path, folders_to_tidy, dry_run=False):
    attachment_references = []
    for folder in folders_to_tidy:
        markdown_files = glob.glob(f"{folder}/**/*.md", recursive=True)
        for file_path in markdown_files:
            images = find_attachment_references(file_path)
            attachment_references.extend(images)
    # Find all paths not in the desired attachments folder.
    attachment_references = [
        attachment
        for attachment in attachment_references
        if not is_path_in_attachments_folder(attachments_folder, attachment)
    ]

    print("Relocating %s attachments" % len(attachment_references))

    if len(attachment_references) == 0:
        print("No attachments to relocate.")
        exit(0)
    else:
        # Take a snapshot of the directory
        take_snapshot()

    for attachment in attachment_references:
        move_to_attachments_folder(attachment, attachments_folder, dry_run=dry_run)

    # Now, write step.
    for attachment in attachment_references:
        with open(attachment.file_path, encoding="utf-8") as file:
            lines = file.readlines()

        # Modify the desired line
        line_num = attachment.line_num
        old_line = lines[line_num - 1]
        relative_path = os.path.relpath(
            attachment.attachment_path, attachment.file_path.parent
        )
        new_line = old_line.replace(attachment.found_string, relative_path)
        print(f"[green]{old_line.strip()} -> {new_line.strip()}[/green]")
        if 1 <= attachment.line_num <= len(lines):
            lines[line_num - 1] = new_line
        else:
            print(f"Line number {line_num} is out of range.")

        if not dry_run:
            with open(attachment.file_path, "w", encoding="utf-8") as file:
                file.writelines(lines)

