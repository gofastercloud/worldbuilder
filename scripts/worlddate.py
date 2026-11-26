"""WorldDate — in-world calendar date handling (era prefix + year, optional month/day)."""


class WorldDate:
    """Represents a date in the world's calendar. Comparable and sortable."""

    def __init__(self, data, calendar_config=None):
        """
        data can be:
          - dict: {year: 1247, month: 3, day: 15, era_prefix: "3A", display: "...", approximate: false}
          - None: represents "unknown date"
        """
        if data is None or data == "" or (isinstance(data, dict) and not data.get("year")):
            self.valid = False
            self.year = 0
            self.month = 0
            self.day = 0
            self.era_prefix = ""
            self.era_sort = 0
            self.display = ""
            self.approximate = False
            return

        self.valid = True
        if isinstance(data, (int, float)):
            # Shorthand: just a year number
            self.year = int(data)
            self.month = 0
            self.day = 0
            self.era_prefix = ""
            self.display = str(self.year)
            self.approximate = False
        elif isinstance(data, dict):
            self.year = int(data.get("year", 0))
            self.month = int(data.get("month", 0))
            self.day = int(data.get("day", 0))
            self.era_prefix = str(data.get("era_prefix", ""))
            self.display = data.get("display", "")
            self.approximate = bool(data.get("approximate", False))
        else:
            # Try to parse as string "year" or "era_prefix year"
            self.valid = False
            self.year = 0
            self.month = 0
            self.day = 0
            self.era_prefix = ""
            self.display = str(data)
            self.approximate = False
            return

        # Resolve era sort order from calendar config
        self.era_sort = 0
        if calendar_config and self.era_prefix:
            for era in calendar_config.get("eras", []):
                if era.get("prefix") == self.era_prefix:
                    self.era_sort = era.get("sort_order", 0)
                    break

        if not self.display:
            parts = []
            if self.era_prefix:
                parts.append(self.era_prefix)
            parts.append(str(self.year))
            if self.month:
                parts.append(f"m{self.month}")
            if self.day:
                parts.append(f"d{self.day}")
            self.display = " ".join(parts)

    def sort_key(self):
        """Return a tuple for chronological sorting."""
        return (self.era_sort, self.year, self.month, self.day)

    def __lt__(self, other):
        if not self.valid or not other.valid:
            return False
        return self.sort_key() < other.sort_key()

    def __le__(self, other):
        if not self.valid or not other.valid:
            return False
        return self.sort_key() <= other.sort_key()

    def __gt__(self, other):
        if not self.valid or not other.valid:
            return False
        return self.sort_key() > other.sort_key()

    def __ge__(self, other):
        if not self.valid or not other.valid:
            return False
        return self.sort_key() >= other.sort_key()

    def __eq__(self, other):
        if not isinstance(other, WorldDate):
            return False
        if not self.valid or not other.valid:
            return False
        return self.sort_key() == other.sort_key()

    def __repr__(self):
        if not self.valid:
            return "WorldDate(unknown)"
        return f"WorldDate({self.display})"


def parse_worlddate(data, calendar_config=None):
    """Parse a worlddate from YAML data."""
    return WorldDate(data, calendar_config)


def get_event_date(meta, calendar_config=None):
    """Extract the primary date from an event's metadata.
    Returns (start_date, end_date) as WorldDate objects.
    For instant events, end_date == start_date."""
    date = parse_worlddate(meta.get("date"), calendar_config)
    start = parse_worlddate(meta.get("start_date"), calendar_config)
    end = parse_worlddate(meta.get("end_date"), calendar_config)

    # Instant event: use 'date'
    if date.valid:
        return date, date
    # Duration event: use start/end
    if start.valid:
        return start, end if end.valid else start
    return WorldDate(None), WorldDate(None)
