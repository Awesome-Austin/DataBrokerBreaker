class CollectrErrors(Exception):
    """Generic error for the Collectrs."""
    pass


class NoRecords(CollectrErrors):
    """Site has no data on a given person."""
    pass


class NoSuchMethod(CollectrErrors):
    """Collectr has no such method"""
    pass


class SiteSchemaChange(CollectrErrors):
    """Site has changed their Schema model/"""
    pass