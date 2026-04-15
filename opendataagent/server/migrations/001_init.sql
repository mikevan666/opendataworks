CREATE TABLE IF NOT EXISTS oda_agent_settings (
  settings_key VARCHAR(32) PRIMARY KEY,
  default_provider_id VARCHAR(64) NOT NULL,
  default_model VARCHAR(255) NOT NULL,
  managed_skills_dir VARCHAR(512) NOT NULL,
  skills_root_dir VARCHAR(512) NOT NULL,
  raw_json LONGTEXT NULL,
  updated_at DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS oda_agent_topic (
  topic_id VARCHAR(64) PRIMARY KEY,
  title VARCHAR(255) NOT NULL,
  current_task_id VARCHAR(64) NULL,
  current_task_status VARCHAR(32) NULL,
  last_message_seq BIGINT NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL,
  updated_at DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS oda_agent_task (
  task_id VARCHAR(64) PRIMARY KEY,
  topic_id VARCHAR(64) NOT NULL,
  assistant_message_id VARCHAR(64) NOT NULL,
  prompt LONGTEXT NOT NULL,
  provider_id VARCHAR(64) NOT NULL,
  model_name VARCHAR(255) NOT NULL,
  task_status VARCHAR(32) NOT NULL,
  last_event_seq BIGINT NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL,
  updated_at DATETIME NOT NULL,
  started_at DATETIME NULL,
  finished_at DATETIME NULL,
  error_json LONGTEXT NULL
);

CREATE TABLE IF NOT EXISTS oda_agent_message (
  message_id VARCHAR(64) PRIMARY KEY,
  topic_id VARCHAR(64) NOT NULL,
  task_id VARCHAR(64) NULL,
  message_seq BIGINT NOT NULL DEFAULT 0,
  sender_type VARCHAR(16) NOT NULL,
  status VARCHAR(32) NOT NULL,
  content LONGTEXT NOT NULL,
  provider_id VARCHAR(64) NULL,
  model_name VARCHAR(255) NULL,
  usage_json LONGTEXT NULL,
  blocks_json LONGTEXT NULL,
  error_json LONGTEXT NULL,
  resume_after_seq BIGINT NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL,
  updated_at DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS oda_agent_chunk (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  task_id VARCHAR(64) NOT NULL,
  message_id VARCHAR(64) NOT NULL,
  seq_id BIGINT NOT NULL,
  record_type VARCHAR(32) NOT NULL,
  event_type VARCHAR(64) NULL,
  content_type VARCHAR(64) NULL,
  correlation_id VARCHAR(128) NULL,
  payload_json LONGTEXT NULL,
  created_at DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS oda_skill_document (
  id VARCHAR(128) PRIMARY KEY,
  folder VARCHAR(128) NOT NULL,
  relative_path VARCHAR(255) NOT NULL,
  file_name VARCHAR(128) NOT NULL,
  source VARCHAR(32) NOT NULL,
  category VARCHAR(64) NOT NULL,
  current_hash CHAR(64) NOT NULL,
  current_version_id VARCHAR(128) NULL,
  version_count INT NOT NULL DEFAULT 0,
  last_change_source VARCHAR(32) NOT NULL,
  last_change_summary VARCHAR(255) NULL,
  created_at DATETIME NOT NULL,
  updated_at DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS oda_skill_document_version (
  id VARCHAR(128) PRIMARY KEY,
  document_id VARCHAR(128) NOT NULL,
  version_no INT NOT NULL,
  change_source VARCHAR(32) NOT NULL,
  change_summary VARCHAR(255) NULL,
  actor VARCHAR(64) NULL,
  content_hash CHAR(64) NOT NULL,
  content LONGTEXT NOT NULL,
  parent_version_id VARCHAR(128) NULL,
  created_at DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS oda_skill_installation (
  id VARCHAR(128) PRIMARY KEY,
  item_id VARCHAR(128) NOT NULL,
  folder VARCHAR(128) NOT NULL,
  source VARCHAR(32) NOT NULL,
  installed_at DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS oda_skill_runtime (
  skill_id VARCHAR(128) PRIMARY KEY,
  enabled TINYINT(1) NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS oda_mcp_server (
  id VARCHAR(128) PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  connection_type VARCHAR(32) NOT NULL,
  tool_prefix VARCHAR(128) NULL,
  enabled TINYINT(1) NOT NULL DEFAULT 1,
  raw_json LONGTEXT NOT NULL,
  created_at DATETIME NOT NULL,
  updated_at DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS oda_mcp_server_version (
  id VARCHAR(128) PRIMARY KEY,
  server_id VARCHAR(128) NOT NULL,
  version_no INT NOT NULL,
  summary VARCHAR(255) NULL,
  created_at DATETIME NOT NULL
);
