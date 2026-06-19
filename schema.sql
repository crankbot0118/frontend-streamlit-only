-- ============================================================
--  VIGT — Clone Automation Schema
--  PostgreSQL DDL
-- ============================================================

-- Enable pgcrypto for bcrypt password hashing (char(60) output)
CREATE EXTENSION IF NOT EXISTS pgcrypto;


-- ============================================================
--  ENUM TYPES
-- ============================================================

CREATE TYPE clone_status AS ENUM (
    'PENDING',      -- job/step created, not yet started
    'RUNNING',      -- currently executing
    'COMPLETED',    -- finished successfully
    'FAILED',       -- execution error occurred
    'SKIPPED',      -- deliberately bypassed by operator
    'ABORTED'       -- forcefully terminated after max retries
);

CREATE TYPE vigt_role AS ENUM (
    'ADMIN',        -- full access: trigger jobs, manage users, view all
    'VIEWER'        -- read-only access: view runs and logs only
);


-- ============================================================
--  TABLE: clients
--  One row per customer/tenant using the platform
-- ============================================================

CREATE TABLE clients (
    client_id       SERIAL          PRIMARY KEY,                        -- auto-incrementing unique tenant identifier
    client_name     VARCHAR(100)    NOT NULL UNIQUE                     -- human-readable name of the client/tenant organisation
);


-- ============================================================
--  TABLE: users
--  One row per user account, scoped to a client
-- ============================================================

CREATE TABLE users (
    user_id         SERIAL          PRIMARY KEY,                        -- auto-incrementing unique user identifier
    user_name       VARCHAR(100)    NOT NULL UNIQUE,                    -- login username, must be unique across the platform
    client_id       INTEGER         NOT NULL                            -- which client/tenant this user belongs to
                        REFERENCES clients(client_id)
                        ON DELETE RESTRICT,
    user_password   CHAR(60)        NOT NULL                            -- bcrypt hash (via pgcrypto crypt()), always exactly 60 chars
);

-- To insert a user with hashed password:
-- INSERT INTO users (user_name, client_id, user_password)
-- VALUES ('tarun', 1, crypt('<your-password>', gen_salt('bf')));

-- To verify a password:
-- SELECT user_id FROM users WHERE user_name = 'tarun'
--   AND user_password = crypt('<your-password>', user_password);


-- ============================================================
--  TABLE: user_roles
--  Assigns a role to a user within a specific client context
-- ============================================================

CREATE TABLE user_roles (
    user_role_id    SERIAL          PRIMARY KEY,                        -- auto-incrementing unique role-assignment identifier
    user_id         INTEGER         NOT NULL                            -- which user is being assigned the role
                        REFERENCES users(user_id)
                        ON DELETE CASCADE,
    client_id       INTEGER         NOT NULL                            -- client scope for this role assignment (supports multi-tenancy)
                        REFERENCES clients(client_id)
                        ON DELETE CASCADE,
    role_name       vigt_role       NOT NULL                            -- the role granted: ADMIN (full access) or VIEWER (read-only)
);


-- ============================================================
--  TABLE: environments
--  One row per EBS environment (source or target for cloning)
-- ============================================================

CREATE TABLE environments (
    env_id          SERIAL          PRIMARY KEY,                        -- auto-incrementing unique environment identifier
    client_id       INTEGER         NOT NULL                            -- which client owns this environment
                        REFERENCES clients(client_id)
                        ON DELETE RESTRICT,
    env_name        VARCHAR(100)    NOT NULL UNIQUE,                    -- short label for the environment e.g. PROD, UAT, DEV
    env_ip          INET            NOT NULL UNIQUE                     -- IP address of the environment server, must be unique
);

-- ============================================================
--  TABLE: clone_functions
--  Master list of the 36 EBS clone steps (function_id in x10)
--  Populated once; never changes at runtime
-- ============================================================

CREATE TABLE clone_functions (
    function_id     INTEGER         PRIMARY KEY                         -- step sequence number in multiples of 10 (0, 10, 20 ... 350)
                        CHECK (function_id >= 0 AND function_id % 10 = 0),
    function_name   VARCHAR(100)    NOT NULL UNIQUE                     -- machine name of the shell function e.g. apps_shutdown, db_restore
);

-- Seed the 36 standard EBS clone steps:
INSERT INTO clone_functions (function_id, function_name) VALUES
    (0,   'apps_shutdown'),
    (10,  'db_shutdown'),
    (20,  'db_mount_restrict'),
    (30,  'db_drop'),
    (40,  'db_nomount'),
    (50,  'db_restore'),
    (60,  'db_startup'),
    (70,  'db_validate_temp'),
    (80,  'db_rename_cdb'),
    (90,  'db_rename_pdb'),
    (100, 'db_util_file'),
    (110, 'db_conc_clean'),
    (120, 'db_autoconfig'),
    (130, 'db_custom_users'),
    (140, 'db_custom_directories'),
    (150, 'ebs_binaries_cleanup'),
    (160, 'ebs_binaries_download'),
    (170, 'ebs_binaries_untar'),
    (180, 'ebs_adcfg_primary_node'),
    (190, 'ebs_adcfg_secondary_node'),
    (200, 'ebs_fndcpass'),
    (210, 'ebs_start_run_admin_server'),
    (220, 'ebs_context_updates'),
    (230, 'ebs_soft_link_updates'),
    (240, 'ebs_autoconfig'),
    (250, 'ebs_profile_resp_conc_updates'),
    (260, 'ebs_custom_updates'),
    (270, 'ebs_stop_run_admin_server'),
    (280, 'ebs_integrations'),
    (290, 'ebs_custom_patch_fs_updates'),
    (300, 'ebs_final_apps_shutdown'),
    (310, 'db_final_shutdown'),
    (320, 'db_final_startup'),
    (330, 'db_final_autoconfig'),
    (340, 'ebs_final_autoconfig'),
    (350, 'ebs_final_apps_startall');


-- ============================================================
--  TABLE: clone_run_status
--  One row per clone job triggered by an operator.
--  clone_run_id is assigned in multiples of 1000 (1000, 2000...)
--  to leave room for child step PKs in clone_function_run_status.
-- ============================================================

CREATE TABLE clone_run_status (
    clone_run_id    INTEGER         PRIMARY KEY                         -- job identifier in multiples of 1000; child step PKs live in the gap between consecutive run IDs
                        CHECK (clone_run_id > 0 AND clone_run_id % 1000 = 0),
    client_id       INTEGER         NOT NULL                            -- which client triggered this clone job
                        REFERENCES clients(client_id)
                        ON DELETE RESTRICT,
    user_id         INTEGER         NOT NULL                            -- which user triggered this clone job
                        REFERENCES users(user_id)
                        ON DELETE RESTRICT,
    user_name       VARCHAR(100)    NOT NULL,                           -- denormalised from users.user_name for fast display without a JOIN
    source_env_id   INTEGER         NOT NULL                            -- environment being cloned from (the source/production system)
                        REFERENCES environments(env_id)
                        ON DELETE RESTRICT,
    target_env_id   INTEGER         NOT NULL                            -- environment being cloned into (the target/refresh system)
                        REFERENCES environments(env_id)
                        ON DELETE RESTRICT,
    source_name     VARCHAR(100)    NOT NULL,                           -- denormalised from environments.env_name for the source, avoids JOIN on every status poll
    target_name     VARCHAR(100)    NOT NULL,                           -- denormalised from environments.env_name for the target, avoids JOIN on every status poll
    status          clone_status    NOT NULL DEFAULT 'PENDING',         -- overall job status; updated automatically by trg_sync_run_status
    env_lock        BOOLEAN         NOT NULL DEFAULT FALSE,             -- TRUE while this run holds the target lock; cleared on terminal status
    start_date      TIMESTAMP,                                          -- wall-clock time when the first step transitioned to RUNNING; NULL until job starts
    last_update     TIMESTAMP,                                          -- wall-clock time of the most recent status change anywhere in this job
    log_location    VARCHAR(100),                                       -- filesystem or S3 path to the master job log file; NULL until log is initialised

    -- Prevent cloning an environment onto itself
    CONSTRAINT chk_src_ne_tgt CHECK (source_env_id <> target_env_id)
);

-- Enforce at most one active lock per target across all runs.
-- A plain boolean on the row does NOT prevent two runs from locking the
-- same target — this partial unique index is what actually guarantees it.
CREATE UNIQUE INDEX uq_active_target_lock
    ON clone_run_status (target_env_id)
    WHERE env_lock = TRUE;

-- Sequence helper to auto-generate clone_run_id in multiples of 1000:
CREATE SEQUENCE clone_run_id_seq
    START WITH 1000
    INCREMENT BY 1000
    NO MAXVALUE;

-- Usage: INSERT INTO clone_run_status (clone_run_id, ...) VALUES (nextval('clone_run_id_seq'), ...);


-- ============================================================
--  TABLE: clone_function_run_status
--  One row per step execution attempt.
--  36 rows created atomically with each clone_run_status insert.
--
--  PK formula:  clone_function_run_id = clone_run_id + 1 + (function_id * 2)
--
--  Example for run 1000:
--    step fid=0   -> pk 1001   (1000 + 1 + 0*2)
--    step fid=10  -> pk 1021   (1000 + 1 + 10*2)
--    step fid=350 -> pk 1701   (1000 + 1 + 350*2)
--
--  On RETRY or SKIP, a new row is inserted with pk = base_pk + attempt_number
--  (up to 10 retries per step, which is why function_ids are spaced 10 apart).
-- ============================================================

CREATE TABLE clone_function_run_status (
    clone_function_run_id   INTEGER         PRIMARY KEY,                -- computed PK: clone_run_id + 1 + (function_id * 2) + attempt_offset
    clone_run_id            INTEGER         NOT NULL                    -- parent job this step belongs to
                                REFERENCES clone_run_status(clone_run_id)
                                ON DELETE CASCADE,
    function_id             INTEGER         NOT NULL                    -- which of the 36 steps this row represents
                                REFERENCES clone_functions(function_id)
                                ON DELETE RESTRICT,
    status                  clone_status    NOT NULL DEFAULT 'PENDING', -- execution status of this specific attempt
    start_time              TIMESTAMP       DEFAULT NULL,               -- when this attempt started executing; NULL until picked up by the agent
    end_time                TIMESTAMP       DEFAULT NULL,               -- when this attempt finished; NULL while running
    step_func_log_location  VARCHAR(100),                               -- path to the per-step log file written by master_clone.sh; NULL until step begins
    created_at              TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP, -- when row got created

    -- Ensure the PK falls within the valid attempt window for this step
    CONSTRAINT chk_pk_formula CHECK (
        clone_function_run_id >= clone_run_id + 1 + (function_id * 2)
        AND clone_function_run_id <  clone_run_id + 1 + (function_id * 2) + 10
    )
);

-- Index for fast per-job step lookups (used on every dashboard poll)
CREATE INDEX idx_cfrs_run_id     ON clone_function_run_status (clone_run_id);

-- Index for fast per-step cross-run queries (e.g. "how often does db_restore fail?")
CREATE INDEX idx_cfrs_function_id ON clone_function_run_status (function_id);

-- Index for filtering by status across all runs (e.g. find all FAILED steps)
CREATE INDEX idx_cfrs_status     ON clone_function_run_status (status);


-- ============================================================
--  TRIGGER FUNCTION: sync_clone_run_status()
--
--  Fires after INSERT or status UPDATE on clone_function_run_status.
--
--  Recalculates the overall status of a clone run by examining
--  the latest execution record for each function within the run.
--
--  Status precedence:
--      ABORTED > FAILED > RUNNING > COMPLETED > PENDING
--
--  Completion logic:
--      A clone run is marked COMPLETED when every function's
--      latest status is either COMPLETED or SKIPPED.
--
--  Additional behavior:
--      - Updates clone_run_status.status
--      - Updates clone_run_status.last_update
--      - Sets clone_run_status.start_date when the run first
--        enters RUNNING state (if not already set)
--
--  Uses only the most recent attempt per function_id
--  (highest clone_function_run_id) when determining the
--  aggregate run status.
-- ============================================================

CREATE OR REPLACE FUNCTION sync_clone_run_status()
RETURNS TRIGGER AS $$
DECLARE
    v_total      INTEGER;
    v_failed     INTEGER;
    v_aborted    INTEGER;
    v_running    INTEGER;
    v_skipped    INTEGER;
    v_completed  INTEGER;
    v_new_status clone_status;
BEGIN
    -- COUNT only the latest attempt per function_id (highest PK = most recent)
    SELECT
        COUNT(*),
        SUM(CASE WHEN status = 'FAILED'    THEN 1 ELSE 0 END),
        SUM(CASE WHEN status = 'ABORTED'   THEN 1 ELSE 0 END),
        SUM(CASE WHEN status = 'RUNNING'   THEN 1 ELSE 0 END),
        SUM(CASE WHEN status = 'SKIPPED'   THEN 1 ELSE 0 END),
        SUM(CASE WHEN status = 'COMPLETED' THEN 1 ELSE 0 END)
    INTO
        v_total, v_failed, v_aborted, v_running, v_skipped, v_completed
    FROM (
        SELECT DISTINCT ON (function_id)
            status
        FROM clone_function_run_status
        WHERE clone_run_id = NEW.clone_run_id
        ORDER BY function_id, clone_function_run_id DESC
    ) latest;

    IF v_aborted > 0 THEN
        v_new_status := 'ABORTED';
    ELSIF v_failed > 0 THEN
        v_new_status := 'FAILED';
    ELSIF v_running > 0 THEN
        v_new_status := 'RUNNING';
    ELSIF v_completed + v_skipped = v_total THEN
        v_new_status := 'COMPLETED';
    ELSE
        v_new_status := 'PENDING';
    END IF;

    UPDATE clone_run_status
    SET
        status      = v_new_status,
        last_update = NOW(),
        start_date  = CASE
                        WHEN v_new_status = 'RUNNING' AND start_date IS NULL
                        THEN NOW()
                        ELSE start_date
                      END
    WHERE clone_run_id = NEW.clone_run_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_sync_run_status
AFTER INSERT OR UPDATE OF status
ON clone_function_run_status
FOR EACH ROW
EXECUTE PROCEDURE sync_clone_run_status();


-- ============================================================
--  TRIGGER FUNCTION: sync_env_lock()
--  Sets clone_run_status.env_lock from run status.
--
--  env_lock = TRUE while status is PENDING, RUNNING, or FAILED
--  (target is reserved for this job). Cleared on COMPLETED,
--  SKIPPED, or ABORTED.
--
--  Enforcement: uq_active_target_lock (partial unique index on
--  target_env_id WHERE env_lock = TRUE) prevents two concurrent
--  locks on the same target. environments no longer carries locked.
-- ============================================================

CREATE OR REPLACE FUNCTION sync_env_lock()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;

    NEW.env_lock := NEW.status IN ('PENDING', 'RUNNING', 'FAILED');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


CREATE TRIGGER trg_sync_env_lock
BEFORE INSERT OR UPDATE OF status, target_env_id
ON clone_run_status
FOR EACH ROW
EXECUTE PROCEDURE sync_env_lock();


-- ============================================================
--  HELPER FUNCTION: create_clone_run()
--  Atomically inserts 1 clone_run_status row + 36 step rows.
--  Locks the target environment only (source remains available).
--  Call this instead of raw INSERTs to guarantee consistency.
-- ============================================================

CREATE OR REPLACE FUNCTION create_clone_run(
    p_client_id     INTEGER,
    p_user_id       INTEGER,
    p_source_env_id INTEGER,
    p_target_env_id INTEGER
) RETURNS INTEGER AS $$
DECLARE
    v_run_id      INTEGER;
    v_user_name   VARCHAR(100);
    v_source_name VARCHAR(100);
    v_target_name VARCHAR(100);
    v_fid         INTEGER;
BEGIN
    -- Guard: reject if target already has an active lock on another run
    IF EXISTS (
        SELECT 1 FROM clone_run_status
        WHERE target_env_id = p_target_env_id
          AND env_lock = TRUE
    ) THEN
        RAISE EXCEPTION 'Target environment is locked by an active clone run.';
    END IF;

    -- Fetch denormalised values up front
    SELECT user_name INTO v_user_name FROM users        WHERE user_id = p_user_id;
    SELECT env_name  INTO v_source_name FROM environments WHERE env_id = p_source_env_id;
    SELECT env_name  INTO v_target_name FROM environments WHERE env_id = p_target_env_id;

    -- Get next run ID (multiple of 1000)
    v_run_id := nextval('clone_run_id_seq');

    -- Insert parent job row (trg_sync_env_lock locks the target on INSERT)
    INSERT INTO clone_run_status (
        clone_run_id, client_id, user_id, user_name,
        source_env_id, target_env_id, source_name, target_name,
        status, start_date, last_update, log_location
    ) VALUES (
        v_run_id, p_client_id, p_user_id, v_user_name,
        p_source_env_id, p_target_env_id, v_source_name, v_target_name,
        'PENDING', NULL, NOW(), NULL
    );

    -- Insert one PENDING row for each of the 36 steps
    FOR v_fid IN SELECT function_id FROM clone_functions ORDER BY function_id LOOP
        INSERT INTO clone_function_run_status (
            clone_function_run_id, clone_run_id, function_id,
            status, start_time, end_time, step_func_log_location
        ) VALUES (
            v_run_id + 1 + (v_fid * 2),
            v_run_id,
            v_fid,
            'PENDING',
            NULL,
            NULL,
            NULL
        );
    END LOOP;

    RETURN v_run_id;
END;
$$ LANGUAGE plpgsql;

-- Usage:
-- SELECT create_clone_run(
--     p_client_id     => 1,
--     p_user_id       => 1,
--     p_source_env_id => 1,
--     p_target_env_id => 2
-- );


-- ============================================================
--  HELPER FUNCTION: retry_clone_run()
--  Inserts a new PENDING attempt for a failed step, and forces the overall run status to PENDING.
-- ============================================================
CREATE OR REPLACE FUNCTION retry_clone_run(
    p_clone_run_id INTEGER,
    p_function_id INTEGER
) RETURNS VOID AS $$
DECLARE
    v_last_attempt INTEGER;
    v_max_attempts CONSTANT INTEGER := 10;
    v_new_id INTEGER;
    v_base_pk INTEGER;
BEGIN
    -- Find latest clone_function_run_id for this function in this run
    SELECT MAX(clone_function_run_id)
      INTO v_last_attempt
      FROM clone_function_run_status
     WHERE clone_run_id = p_clone_run_id
       AND function_id = p_function_id;

    IF v_last_attempt IS NULL THEN
        RAISE EXCEPTION 'No previous attempt found for run % step %', p_clone_run_id, p_function_id;
    END IF;

    v_base_pk := p_clone_run_id + 1 + (p_function_id * 2);

    IF v_last_attempt >= v_base_pk + v_max_attempts - 1 THEN
        RAISE EXCEPTION 'Maximum number of retries (% attempts) exceeded for run % step %', v_max_attempts, p_clone_run_id, p_function_id;
    END IF;

    -- Insert next attempt if latest status is FAILED
    IF (
        SELECT status FROM clone_function_run_status WHERE clone_function_run_id = v_last_attempt
    ) <> 'FAILED' THEN
        RAISE EXCEPTION 'Last attempt is not FAILED. Retry is only allowed after a failure.';
    END IF;

    v_new_id := v_last_attempt + 1;

    INSERT INTO clone_function_run_status (
        clone_function_run_id, clone_run_id, function_id,
        status, start_time, end_time, step_func_log_location
    )
    VALUES (
        v_new_id,
        p_clone_run_id,
        p_function_id,
        'PENDING',
        NULL,
        NULL,
        NULL
    );

    -- Set overall run status explicitly to PENDING,
    -- and update last_update timestamp
    UPDATE clone_run_status
       SET status = 'PENDING', last_update = NOW()
     WHERE clone_run_id = p_clone_run_id;
END;
$$ LANGUAGE plpgsql;

-- Usage (example):
-- SELECT retry_clone_run(1000, 50);

-- ============================================================
--  HELPER FUNCTION: finish_clone_run()
--  Clears env_lock on a run once it has reached a terminal state.
--  Normally trg_sync_env_lock maintains env_lock automatically;
--  call this from the agent after the run concludes as an explicit
--  safety net, or when reconciling stale lock state.
-- ============================================================

CREATE OR REPLACE FUNCTION finish_clone_run(
    p_run_id INTEGER
) RETURNS VOID AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM clone_run_status WHERE clone_run_id = p_run_id
    ) THEN
        RAISE EXCEPTION 'Clone run % not found.', p_run_id;
    END IF;

    UPDATE clone_run_status
    SET env_lock = (status IN ('PENDING', 'RUNNING', 'FAILED'))
    WHERE clone_run_id = p_run_id;
END;
$$ LANGUAGE plpgsql;

-- Usage:
-- SELECT finish_clone_run(1000);