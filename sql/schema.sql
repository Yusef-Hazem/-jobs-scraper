-- =============================================================
-- Jobs scraper — MySQL star schema
-- Run once to initialise the database:
--   mysql -u root -p < sql/schema.sql
-- =============================================================

CREATE DATABASE IF NOT EXISTS jobs
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE jobs;

-- ── Dimension: jobs ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS jobs_dim (
    job_id          INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    job_title       VARCHAR(255) NOT NULL,
    seniority_level VARCHAR(100),
    employment_type VARCHAR(100),
    UNIQUE KEY uq_job (job_title, seniority_level, employment_type)
) ENGINE=InnoDB;

-- ── Dimension: companies ──────────────────────────────────────
CREATE TABLE IF NOT EXISTS companies_dim (
    company_id   INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    UNIQUE KEY uq_company (company_name)
) ENGINE=InnoDB;

-- ── Dimension: countries ──────────────────────────────────────
CREATE TABLE IF NOT EXISTS countries_dim (
    country_id   INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    country_name VARCHAR(100) NOT NULL,
    UNIQUE KEY uq_country (country_name)
) ENGINE=InnoDB;

-- ── Dimension: cities ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS cities_dim (
    city_id    INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    city_name  VARCHAR(100) NOT NULL,
    country_id INT UNSIGNED NOT NULL,
    UNIQUE KEY uq_city (city_name, country_id),
    CONSTRAINT fk_city_country FOREIGN KEY (country_id)
        REFERENCES countries_dim (country_id) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- ── Dimension: skills ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS skills_dim (
    skill_id   INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    skill_name VARCHAR(150) NOT NULL,
    UNIQUE KEY uq_skill (skill_name)
) ENGINE=InnoDB;

-- ── Fact: job postings ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS job_postings_fact (
    posting_id  INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    job_id      INT UNSIGNED NOT NULL,
    company_id  INT UNSIGNED NOT NULL,
    city_id     INT UNSIGNED NOT NULL,
    posted_date DATE         NOT NULL,
    scraped_at  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_posting (job_id, company_id, city_id, posted_date),
    CONSTRAINT fk_posting_job     FOREIGN KEY (job_id)     REFERENCES jobs_dim      (job_id),
    CONSTRAINT fk_posting_company FOREIGN KEY (company_id) REFERENCES companies_dim (company_id),
    CONSTRAINT fk_posting_city    FOREIGN KEY (city_id)    REFERENCES cities_dim    (city_id)
) ENGINE=InnoDB;

-- ── Bridge: job posting ↔ skills ─────────────────────────────
CREATE TABLE IF NOT EXISTS job_posting_skills (
    posting_id INT UNSIGNED NOT NULL,
    skill_id   INT UNSIGNED NOT NULL,
    PRIMARY KEY (posting_id, skill_id),
    CONSTRAINT fk_jps_posting FOREIGN KEY (posting_id) REFERENCES job_postings_fact (posting_id) ON DELETE CASCADE,
    CONSTRAINT fk_jps_skill   FOREIGN KEY (skill_id)   REFERENCES skills_dim        (skill_id)   ON DELETE CASCADE
) ENGINE=InnoDB;
