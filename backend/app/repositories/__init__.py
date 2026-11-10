"""Database queries, one repository per model.

Repositories only build and run SQLAlchemy queries. They never commit: the service
that owns the operation decides when the transaction ends.
"""
