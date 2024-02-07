import os
import datetime
import argparse
from pathlib import Path

AUTOINDEX_SECTION = """
## Notes
<autoindex mode="all" filterByDate="{date_only}">
</autoindex>
""".strip(
    "\n"
)

TEMPLATE = """
# {date_humanized}
#daily

- 

## Tasks
- [ ] 

{autoindex_section}
""".strip(
    "\n"
)


def create_daily_file(path, date_format, with_autoindex=False, is_tomorrow=False):
    today = datetime.datetime.today()
    if is_tomorrow:
        today += datetime.timedelta(days=1)
    date = today.strftime(date_format)
    file_name = f"{date}.md"
    file_path = Path(path) / file_name

    if not file_path.exists():
        with file_path.open("w") as f:
            f.write(
                TEMPLATE.format(
                    date_humanized=date,
                    autoindex_section=AUTOINDEX_SECTION.format(date_only=today.date()) if with_autoindex else "",
                )
            )

    return file_path
