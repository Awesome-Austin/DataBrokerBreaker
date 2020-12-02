class CollectorErrors(Exception):
    """Generic error for the Collectors."""
    pass


class NoRecords(CollectorErrors):
    """Site has no data on a given person."""
    pass


class NoSuchMethod(CollectorErrors):
    """Collector has no such method."""
    pass


class SiteSchemaChange(CollectorErrors):
    """Site has changed their Schema model."""
    pass
