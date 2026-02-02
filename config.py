"""Configuration: read/write sources for migration strategy."""

import os

# MongoDB (default)
MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/")
MONGODB_DB = os.environ.get("MONGODB_DB", "blog")

# Cassandra (for migration)
CASSANDRA_HOSTS = os.environ.get("CASSANDRA_HOSTS", "127.0.0.1").split(",")
CASSANDRA_KEYSPACE = os.environ.get("CASSANDRA_KEYSPACE", "blog")

# Migration strategy:
# - "mongodb_only"     : read from MongoDB, write to MongoDB only
# - "double_write"     : read from MongoDB, write to BOTH MongoDB and Cassandra
# - "read_migration"   : read from Cassandra, write to BOTH
# - "cassandra_only"   : read from Cassandra, write to Cassandra only (cleanup)
READ_SOURCE = os.environ.get("READ_SOURCE", "mongodb_only")  # mongodb_only | double_write | read_migration | cassandra_only
WRITE_BOTH = os.environ.get("WRITE_BOTH", "false").lower() == "true"

def read_from_mongodb() -> bool:
    return READ_SOURCE in ("mongodb_only", "double_write")

def read_from_cassandra() -> bool:
    return READ_SOURCE in ("read_migration", "cassandra_only")

def write_to_mongodb() -> bool:
    return READ_SOURCE in ("mongodb_only", "double_write", "read_migration")

def write_to_cassandra() -> bool:
    return WRITE_BOTH or READ_SOURCE in ("double_write", "read_migration", "cassandra_only")
