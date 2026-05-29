-- O45: owner admin pageview counters (path × day)
CREATE TABLE IF NOT EXISTS admin_pageviews (
    path TEXT NOT NULL,
    day  DATE NOT NULL DEFAULT CURRENT_DATE,
    views INT NOT NULL DEFAULT 0,
    PRIMARY KEY (path, day)
);
