#!/usr/bin/env python3
"""Builds the two lab database replicas. Feature columns exist in database `default` and, as the underlying
storage, in `r0`. system_columns only shows databases the featuregen user has a grant on."""
import sqlite3

KINDS = ["ua", "ip", "tls", "hdr", "path", "asn", "rate", "geo"]
FEATURES = [(f"{k}_{i:02d}", "Float32") for k in KINDS for i in range(1, 16)]   # 8 x 15 = 120

for replica in ("replica-a", "replica-b"):
    db = sqlite3.connect(f"/data/{replica}.db")
    db.executescript("""
        CREATE TABLE all_columns (database TEXT, tbl TEXT, name TEXT, type TEXT);
        CREATE TABLE grants (user TEXT, database TEXT);
        INSERT INTO grants VALUES ('featuregen', 'default');
        CREATE VIEW system_columns AS SELECT * FROM all_columns
            WHERE database IN (SELECT database FROM grants WHERE user = 'featuregen');
    """)
    for database in ("default", "r0"):
        db.executemany("INSERT INTO all_columns VALUES (?, 'http_requests_features', ?, ?)",
                       [(database, n, t) for n, t in FEATURES])
    db.commit()
    db.close()
