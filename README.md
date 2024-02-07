# notectl

A simple note management tool. 

## Description

`notectl` provides a portable suite of tools you can use to organize and backlink your plain-text notes. It isn't tied to any specific text editor.

It isn't concerned with note *taking*, that's up to you. However, its opinionated nature means it contains tools useful for building a second-brain, such as quick "daily note" creation. 

Simply put, it kicks some plaintext *ass*. 

## Why?
I don't want to be tied to a particular text editor for my notes. I'd like to use Obsidian features, such as attachment management and automatic backlink indexing, but prefer using iA Writer.

There's also some principle to it: my notes should be fully usable from any editor, using a suite of single-purpose, portable tools (think UNIX philosophy).

## Sample commands
In lieu of documentation, here's some sample usage:

```bash
# Install notectl
poetry install
notectl --install-completion

# Configure it (check the `conf` folder for examples)
notectl config init

# Create daily notes
notectl daily today
notectl daily tomorrow

# Collect all your attachments into a single folder
notectl attachments tidy

# Fill all <autoindex /> tags with any backlinks
notectl autoindex run

# Create a topical note (with autoindexing support)
notectl topic new "Programming"
```

## Disclaimer
This project is a WIP. It's messy and likely will be forever (as long as it meets my needs). 

There are safeguards in place to ensure that it doesn't wreck your notes. Configure the Git snapshot feature to ensure nothing goes wrong.