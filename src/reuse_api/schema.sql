DROP TABLE IF EXISTS projects;

CREATE TABLE projects (
    url TEXT PRIMARY KEY,
    hash TEXT,
    status INTEGER,
    lint_code INTEGER,
    lint_output TEXT,
    last_access INTEGER
);
