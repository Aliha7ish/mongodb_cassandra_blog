"""
Cleanup: remove everything MongoDB-related (use after full migration to Cassandra).

This script:
1. Removes MongoDB imports and code from db.py, app.py
2. Keeps only Cassandra and the unified db layer that uses Cassandra

Run once after READ_SOURCE=cassandra_only is verified and you no longer need MongoDB.
Alternatively, use the cassandra_only code path (config) and delete MongoDB files manually.

This file documents what to remove:
- config: READ_SOURCE, write_to_mongodb, read_from_mongodb; keep only Cassandra
- db.py: remove db_mongo imports and branches; keep only db_cassandra
- db_mongo.py: delete file
- app.py: no MongoDB-specific code if db.py is updated
- requirements.txt: remove pymongo
"""

# To fully cleanup:
# 1. Set READ_SOURCE=cassandra_only and run the app; verify all works.
# 2. Delete db_mongo.py
# 3. In config.py: remove MONGODB_URI, MONGODB_DB, READ_SOURCE, WRITE_BOTH;
#    remove read_from_mongodb, read_from_cassandra, write_to_mongodb, write_to_cassandra;
#    or simplify to a single "use_cassandra = True".
# 4. In db.py: remove all db_mongo imports and branches; call only db_cassandra.*
# 5. In requirements.txt: remove pymongo
# 6. Delete this cleanup script.

print("Cleanup instructions: see docstring in cleanup_remove_mongodb.py")
print("After migration: set READ_SOURCE=cassandra_only, then remove db_mongo.py, pymongo, and MongoDB branches in config/db.")
