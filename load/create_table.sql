-- create_tables.sql
-- PostgreSQL schema for riksdagsdata
-- Run this once to initialize the database before loading data


-- Parties
-- Populated manually — party_name from 'parti' column in source data
-- color_hex is optional, used for frontend visualization
CREATE TABLE IF NOT EXISTS parties (
    party_id    VARCHAR(10)  PRIMARY KEY,
    party_name  VARCHAR(100),
    color_hex   VARCHAR(7)   -- nullable, populated manually e.g. '#E8112d'
);


-- Members
-- Source: ledamoter.csv
-- start_date/end_date excluded — embedded in JSON blob in source data
-- image_url maps to bild_url_192
CREATE TABLE IF NOT EXISTS members (
    member_id   VARCHAR(20)  PRIMARY KEY,  -- intressent_id
    first_name  VARCHAR(100),              -- tilltalsnamn
    last_name   VARCHAR(100),              -- efternamn
    party_id    VARCHAR(10)  REFERENCES parties(party_id),
    district    VARCHAR(100),              -- valkrets
    status      VARCHAR(50),               -- status
    gender      VARCHAR(10),               -- kon: 'kvinna' / 'man'
    birth_year  SMALLINT,                  -- fodd_ar
    image_url   TEXT                       -- bild_url_192
);


-- Documents
-- Source: dokument.csv
-- PK is dok_id from source data
CREATE TABLE IF NOT EXISTS documents (
    document_id     VARCHAR(20)  PRIMARY KEY,  -- dok_id
    title           TEXT,                       -- titel
    document_type   VARCHAR(50),               -- doktyp
    date            DATE,                       -- datum
    riksmote        VARCHAR(10),               -- rm
    organ           VARCHAR(50),               -- organ
    status          VARCHAR(20),               -- status
    html_url        TEXT,                       -- url
    pdf_url         TEXT                        -- from filbilaga if available
);


-- Votes
-- Source: voteringar.csv, aggregated from VoteResults
-- yes_votes, no_votes, abstain_votes, absent_votes, result are nullable
-- — calculated from vote_results after insert, not available in raw data
CREATE TABLE IF NOT EXISTS votes (
    vote_id         VARCHAR(36)  PRIMARY KEY,  -- votering_id
    document_id     VARCHAR(20)  REFERENCES documents(document_id),
    topic           VARCHAR(200),              -- beteckning
    result          VARCHAR(20),               -- calculated: 'ja'/'nej'
    yes_votes       SMALLINT,                  -- calculated from vote_results
    no_votes        SMALLINT,                  -- calculated from vote_results
    abstain_votes   SMALLINT,                  -- calculated from vote_results
    absent_votes    SMALLINT,                  -- calculated from vote_results
    riksmote        VARCHAR(10),               -- rm
    date            DATE                        -- systemdatum
);


-- VoteResults
-- Source: voteringar.csv
-- One row per member per vote
CREATE TABLE IF NOT EXISTS vote_results (
    vote_result_id  SERIAL       PRIMARY KEY,
    vote_id         VARCHAR(36)  REFERENCES votes(vote_id),
    member_id       VARCHAR(20)  REFERENCES members(member_id),
    party_id        VARCHAR(10)  REFERENCES parties(party_id),
    vote            VARCHAR(15)  -- rost: 'ja'/'nej'/'frånvarande'/'avstår'
);


-- Speeches
-- Source: anforanden.csv
-- body_text maps to anforandetext — verify this is populated in extract step
CREATE TABLE IF NOT EXISTS speeches (
    speech_id       VARCHAR(36)  PRIMARY KEY,  -- anforande_id
    member_id       VARCHAR(20)  REFERENCES members(member_id),
    party_id        VARCHAR(10)  REFERENCES parties(party_id),
    riksmote        VARCHAR(10),               -- dok_rm
    date            DATE,                       -- dok_datum
    debate_title    TEXT,                       -- avsnittsrubrik
    speech_type     VARCHAR(50),               -- kammaraktivitet
    body_text       TEXT,                       -- anforandetext
    document_id     VARCHAR(20)  REFERENCES documents(document_id)  -- rel_dok_id
);


-- DocumentsAuthor
-- Junction table linking documents to their authors (members)
-- Source: derived from dokument.csv dokintressent field
CREATE TABLE IF NOT EXISTS documents_author (
    document_author_id  SERIAL       PRIMARY KEY,
    document_id         VARCHAR(20)  REFERENCES documents(document_id),
    member_id           VARCHAR(20)  REFERENCES members(member_id),
    party_id            VARCHAR(10)  REFERENCES parties(party_id),
    author_order        SMALLINT
);


-- PipelineLogs
-- Populated by the pipeline on each run, not from source CSV data
CREATE TABLE IF NOT EXISTS pipeline_logs (
    event_id            SERIAL        PRIMARY KEY,
    source              VARCHAR(20),
    riksmote            VARCHAR(10),
    kafka_topic         VARCHAR(100),
    kafka_partition     SMALLINT,
    kafka_offset_start  BIGINT,
    kafka_offset_end    BIGINT,
    consumer_group      VARCHAR(100),
    records_fetched     INTEGER,
    records_inserted    INTEGER,
    records_updated     INTEGER,
    records_failed      INTEGER,
    started_at          TIMESTAMP,
    finished_at         TIMESTAMP,
    duration_ms         INTEGER,
    status              VARCHAR(20),
    error_message       TEXT,
    triggered_by        VARCHAR(20),
    service_version     VARCHAR(50)
);