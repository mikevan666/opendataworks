package store

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"time"

	_ "github.com/go-sql-driver/mysql"

	"opendataagent/server/internal/config"
	"opendataagent/server/internal/models"
	"opendataagent/server/internal/util"
)

type MySQLStore struct {
	db   *sql.DB
	root string
	last models.StateSnapshot
}

func NewMySQLStore(cfg config.Config) (*MySQLStore, error) {
	if strings.TrimSpace(cfg.MySQLDSN) == "" {
		return nil, fmt.Errorf("mysql store requires ODA_MYSQL_DSN or MYSQL_* envs")
	}
	db, err := sql.Open("mysql", cfg.MySQLDSN)
	if err != nil {
		return nil, err
	}
	if err := db.Ping(); err != nil {
		_ = db.Close()
		return nil, err
	}
	store := &MySQLStore{db: db, root: cfg.ProjectRoot}
	if err := store.ensureSchema(); err != nil {
		_ = db.Close()
		return nil, err
	}
	return store, nil
}

func (s *MySQLStore) Close() error {
	if s == nil || s.db == nil {
		return nil
	}
	return s.db.Close()
}

func (s *MySQLStore) Load() (models.StateSnapshot, error) {
	snapshot := models.StateSnapshot{
		Topics:             map[string]*models.Topic{},
		Tasks:              map[string]*models.Task{},
		TaskEvents:         map[string][]models.TaskEvent{},
		SkillDocuments:     map[string]*models.SkillDocument{},
		SkillRuntime:       map[string]*models.SkillRuntimeConfig{},
		SkillInstallations: map[string]*models.SkillInstallation{},
		MCPServers:         map[string]*models.MCPServer{},
	}

	if err := s.loadSettings(&snapshot); err != nil {
		return models.StateSnapshot{}, err
	}
	if err := s.loadTopics(&snapshot); err != nil {
		return models.StateSnapshot{}, err
	}
	if err := s.loadTasks(&snapshot); err != nil {
		return models.StateSnapshot{}, err
	}
	if err := s.loadMessages(&snapshot); err != nil {
		return models.StateSnapshot{}, err
	}
	if err := s.loadTaskEvents(&snapshot); err != nil {
		return models.StateSnapshot{}, err
	}
	if err := s.loadSkillDocuments(&snapshot); err != nil {
		return models.StateSnapshot{}, err
	}
	if err := s.loadSkillInstallations(&snapshot); err != nil {
		return models.StateSnapshot{}, err
	}
	if err := s.loadSkillRuntime(&snapshot); err != nil {
		return models.StateSnapshot{}, err
	}
	if err := s.loadMCPServers(&snapshot); err != nil {
		return models.StateSnapshot{}, err
	}
	s.last = mustCloneSnapshot(snapshot)
	return snapshot, nil
}

func (s *MySQLStore) Save(snapshot models.StateSnapshot) error {
	prev := mustCloneSnapshot(s.last)
	tx, err := s.db.Begin()
	if err != nil {
		return err
	}
	defer func() {
		if err != nil {
			_ = tx.Rollback()
		}
	}()

	if err = s.syncSettings(tx, prev.Settings, snapshot.Settings); err != nil {
		return err
	}
	if err = s.syncTopics(tx, prev.Topics, snapshot.Topics); err != nil {
		return err
	}
	if err = s.syncMessages(tx, flattenMessages(prev.Topics), flattenMessages(snapshot.Topics)); err != nil {
		return err
	}
	if err = s.syncTasks(tx, prev.Tasks, snapshot.Tasks); err != nil {
		return err
	}
	if err = s.syncTaskEvents(tx, prev.TaskEvents, snapshot.TaskEvents); err != nil {
		return err
	}
	if err = s.syncSkillDocuments(tx, prev.SkillDocuments, snapshot.SkillDocuments); err != nil {
		return err
	}
	if err = s.syncSkillInstallations(tx, prev.SkillInstallations, snapshot.SkillInstallations); err != nil {
		return err
	}
	if err = s.syncSkillRuntime(tx, prev.SkillRuntime, snapshot.SkillRuntime); err != nil {
		return err
	}
	if err = s.syncMCPServers(tx, prev.MCPServers, snapshot.MCPServers); err != nil {
		return err
	}
	if err = tx.Commit(); err != nil {
		return err
	}
	s.last = mustCloneSnapshot(snapshot)
	return nil
}

func (s *MySQLStore) ensureSchema() error {
	path := filepath.Join(s.root, "migrations", "001_init.sql")
	payload, err := os.ReadFile(path)
	if err != nil {
		return err
	}
	for _, statement := range strings.Split(string(payload), ";") {
		query := strings.TrimSpace(statement)
		if query == "" {
			continue
		}
		if _, err := s.db.Exec(query); err != nil {
			return fmt.Errorf("apply schema statement %q: %w", query, err)
		}
	}
	if ok, err := s.columnExists("oda_agent_message", "blocks_json"); err != nil {
		return err
	} else if !ok {
		statement := `ALTER TABLE oda_agent_message ADD COLUMN blocks_json LONGTEXT NULL AFTER usage_json`
		if _, err := s.db.Exec(statement); err != nil {
			return fmt.Errorf("apply schema patch %q: %w", statement, err)
		}
	}
	return nil
}

func (s *MySQLStore) clearTables(tx *sql.Tx) error {
	tables := []string{
		"oda_agent_chunk",
		"oda_agent_message",
		"oda_agent_task",
		"oda_agent_topic",
		"oda_skill_document_version",
		"oda_skill_document",
		"oda_skill_installation",
		"oda_skill_runtime",
		"oda_mcp_server_version",
		"oda_mcp_server",
		"oda_agent_settings",
	}
	for _, table := range tables {
		if _, err := tx.Exec("DELETE FROM " + table); err != nil {
			return err
		}
	}
	return nil
}

func (s *MySQLStore) columnExists(table string, column string) (bool, error) {
	var count int
	row := s.db.QueryRow(`
		SELECT COUNT(*)
		FROM information_schema.columns
		WHERE table_schema = DATABASE() AND table_name = ? AND column_name = ?
	`, table, column)
	if err := row.Scan(&count); err != nil {
		return false, err
	}
	return count > 0, nil
}

func (s *MySQLStore) loadSettings(snapshot *models.StateSnapshot) error {
	row := s.db.QueryRow(`SELECT raw_json, default_provider_id, default_model, managed_skills_dir, skills_root_dir, updated_at FROM oda_agent_settings WHERE settings_key = 'default' LIMIT 1`)
	var (
		raw                             sql.NullString
		defaultProviderID, defaultModel string
		managedSkillsDir, skillsRootDir string
		updatedAt                       timeCarrier
	)
	if err := row.Scan(&raw, &defaultProviderID, &defaultModel, &managedSkillsDir, &skillsRootDir, &updatedAt); err != nil {
		if err == sql.ErrNoRows {
			return nil
		}
		return err
	}
	if raw.Valid && strings.TrimSpace(raw.String) != "" {
		if err := json.Unmarshal([]byte(raw.String), &snapshot.Settings); err != nil {
			return err
		}
		return nil
	}
	snapshot.Settings = models.AgentSettings{
		DefaultProviderID: defaultProviderID,
		DefaultModel:      defaultModel,
		ProviderID:        defaultProviderID,
		Model:             defaultModel,
		ManagedSkillsDir:  managedSkillsDir,
		SkillsRootDir:     skillsRootDir,
		UpdatedAt:         updatedAt.String(),
	}
	return nil
}

func (s *MySQLStore) loadTopics(snapshot *models.StateSnapshot) error {
	rows, err := s.db.Query(`SELECT topic_id, title, current_task_id, current_task_status, last_message_seq, created_at, updated_at FROM oda_agent_topic`)
	if err != nil {
		return err
	}
	defer rows.Close()
	for rows.Next() {
		var item models.Topic
		var currentTaskID, currentTaskStatus sql.NullString
		var createdAt, updatedAt timeCarrier
		if err := rows.Scan(&item.TopicID, &item.Title, &currentTaskID, &currentTaskStatus, &item.LastMessageSeq, &createdAt, &updatedAt); err != nil {
			return err
		}
		item.CurrentTaskID = nullableString(currentTaskID)
		item.CurrentTaskStatus = nullableString(currentTaskStatus)
		item.CreatedAt = createdAt.String()
		item.UpdatedAt = updatedAt.String()
		item.Messages = []models.Message{}
		snapshot.Topics[item.TopicID] = &item
	}
	return rows.Err()
}

func (s *MySQLStore) loadTasks(snapshot *models.StateSnapshot) error {
	rows, err := s.db.Query(`SELECT task_id, topic_id, assistant_message_id, prompt, provider_id, model_name, task_status, last_event_seq, created_at, updated_at, started_at, finished_at, error_json FROM oda_agent_task`)
	if err != nil {
		return err
	}
	defer rows.Close()
	for rows.Next() {
		var item models.Task
		var createdAt, updatedAt, startedAt, finishedAt timeCarrier
		var rawError sql.NullString
		if err := rows.Scan(&item.TaskID, &item.TopicID, &item.AssistantMessageID, &item.Prompt, &item.ProviderID, &item.ModelName, &item.TaskStatus, &item.LastEventSeq, &createdAt, &updatedAt, &startedAt, &finishedAt, &rawError); err != nil {
			return err
		}
		item.CreatedAt = createdAt.String()
		item.UpdatedAt = updatedAt.String()
		item.StartedAt = startedAt.String()
		item.FinishedAt = finishedAt.String()
		if rawError.Valid && strings.TrimSpace(rawError.String) != "" {
			_ = json.Unmarshal([]byte(rawError.String), &item.Error)
		}
		snapshot.Tasks[item.TaskID] = &item
	}
	return rows.Err()
}

func (s *MySQLStore) loadMessages(snapshot *models.StateSnapshot) error {
	rows, err := s.db.Query(`SELECT message_id, topic_id, task_id, message_seq, sender_type, status, content, provider_id, model_name, usage_json, blocks_json, error_json, resume_after_seq, created_at, updated_at FROM oda_agent_message ORDER BY topic_id, message_seq, created_at, message_id`)
	if err != nil {
		return err
	}
	defer rows.Close()
	for rows.Next() {
		var item models.Message
		var taskID, providerID, modelName sql.NullString
		var rawUsage, rawBlocks, rawError sql.NullString
		var createdAt, updatedAt timeCarrier
		if err := rows.Scan(&item.MessageID, &item.TopicID, &taskID, &item.MessageSeq, &item.SenderType, &item.Status, &item.Content, &providerID, &modelName, &rawUsage, &rawBlocks, &rawError, &item.ResumeAfterSeq, &createdAt, &updatedAt); err != nil {
			return err
		}
		item.TaskID = nullableString(taskID)
		item.ProviderID = nullableString(providerID)
		item.Model = nullableString(modelName)
		item.CreatedAt = createdAt.String()
		item.UpdatedAt = updatedAt.String()
		if rawUsage.Valid && strings.TrimSpace(rawUsage.String) != "" {
			_ = json.Unmarshal([]byte(rawUsage.String), &item.Usage)
		}
		if rawBlocks.Valid && strings.TrimSpace(rawBlocks.String) != "" {
			_ = json.Unmarshal([]byte(rawBlocks.String), &item.Blocks)
		}
		if rawError.Valid && strings.TrimSpace(rawError.String) != "" {
			_ = json.Unmarshal([]byte(rawError.String), &item.Error)
		}
		if topic := snapshot.Topics[item.TopicID]; topic != nil {
			topic.Messages = append(topic.Messages, item)
			topic.MessageCount = len(topic.Messages)
		}
	}
	return rows.Err()
}

func (s *MySQLStore) loadTaskEvents(snapshot *models.StateSnapshot) error {
	rows, err := s.db.Query(`SELECT payload_json FROM oda_agent_chunk ORDER BY task_id, seq_id, id`)
	if err != nil {
		return err
	}
	defer rows.Close()
	for rows.Next() {
		var raw sql.NullString
		if err := rows.Scan(&raw); err != nil {
			return err
		}
		if !raw.Valid || strings.TrimSpace(raw.String) == "" {
			continue
		}
		var item models.TaskEvent
		if err := json.Unmarshal([]byte(raw.String), &item); err != nil {
			return err
		}
		snapshot.TaskEvents[item.TaskID] = append(snapshot.TaskEvents[item.TaskID], item)
	}
	return rows.Err()
}

func (s *MySQLStore) loadSkillDocuments(snapshot *models.StateSnapshot) error {
	rows, err := s.db.Query(`SELECT id, folder, relative_path, file_name, source, category, current_hash, current_version_id, version_count, last_change_source, last_change_summary, created_at, updated_at FROM oda_skill_document`)
	if err != nil {
		return err
	}
	defer rows.Close()
	for rows.Next() {
		var item models.SkillDocument
		var currentVersionID sql.NullString
		var createdAt, updatedAt timeCarrier
		if err := rows.Scan(&item.ID, &item.Folder, &item.RelativePath, &item.FileName, &item.Source, &item.Category, &item.CurrentHash, &currentVersionID, &item.VersionCount, &item.LastChangeSource, &item.LastChangeSummary, &createdAt, &updatedAt); err != nil {
			return err
		}
		item.CurrentVersionID = nullableString(currentVersionID)
		item.CreatedAt = createdAt.String()
		item.UpdatedAt = updatedAt.String()
		item.Editable = item.Source == "managed"
		snapshot.SkillDocuments[item.ID] = &item
	}
	if err := rows.Err(); err != nil {
		return err
	}

	versionRows, err := s.db.Query(`SELECT id, document_id, version_no, change_source, change_summary, actor, content_hash, content, parent_version_id, created_at FROM oda_skill_document_version ORDER BY document_id, version_no`)
	if err != nil {
		return err
	}
	defer versionRows.Close()
	for versionRows.Next() {
		var version models.SkillDocumentVersion
		var changeSummary, actor, parentVersionID sql.NullString
		var createdAt timeCarrier
		if err := versionRows.Scan(&version.ID, &version.DocumentID, &version.VersionNo, &version.ChangeSource, &changeSummary, &actor, &version.ContentHash, &version.Content, &parentVersionID, &createdAt); err != nil {
			return err
		}
		version.ChangeSummary = nullableString(changeSummary)
		version.Actor = nullableString(actor)
		version.ParentVersionID = nullableString(parentVersionID)
		version.CreatedAt = createdAt.String()
		doc := snapshot.SkillDocuments[version.DocumentID]
		if doc == nil {
			continue
		}
		version.IsCurrent = version.ID == doc.CurrentVersionID
		doc.Versions = append(doc.Versions, version)
		if version.IsCurrent {
			doc.CurrentContent = version.Content
		}
	}
	return versionRows.Err()
}

func (s *MySQLStore) loadSkillInstallations(snapshot *models.StateSnapshot) error {
	rows, err := s.db.Query(`SELECT id, item_id, folder, source, installed_at FROM oda_skill_installation`)
	if err != nil {
		return err
	}
	defer rows.Close()
	for rows.Next() {
		var item models.SkillInstallation
		var installedAt timeCarrier
		if err := rows.Scan(&item.ID, &item.ItemID, &item.Folder, &item.Source, &installedAt); err != nil {
			return err
		}
		item.InstalledAt = installedAt.String()
		snapshot.SkillInstallations[item.Folder] = &item
	}
	return rows.Err()
}

func (s *MySQLStore) loadSkillRuntime(snapshot *models.StateSnapshot) error {
	rows, err := s.db.Query(`SELECT skill_id, enabled FROM oda_skill_runtime`)
	if err != nil {
		return err
	}
	defer rows.Close()
	for rows.Next() {
		var item models.SkillRuntimeConfig
		var enabled bool
		if err := rows.Scan(&item.SkillID, &enabled); err != nil {
			return err
		}
		item.Enabled = boolPtr(enabled)
		snapshot.SkillRuntime[item.SkillID] = &item
	}
	return rows.Err()
}

func (s *MySQLStore) loadMCPServers(snapshot *models.StateSnapshot) error {
	rows, err := s.db.Query(`SELECT raw_json FROM oda_mcp_server`)
	if err != nil {
		return err
	}
	defer rows.Close()
	for rows.Next() {
		var raw string
		if err := rows.Scan(&raw); err != nil {
			return err
		}
		var item models.MCPServer
		if err := json.Unmarshal([]byte(raw), &item); err != nil {
			return err
		}
		snapshot.MCPServers[item.ID] = &item
	}
	return rows.Err()
}

func (s *MySQLStore) saveSettings(tx *sql.Tx, settings models.AgentSettings) error {
	raw, err := json.Marshal(settings)
	if err != nil {
		return err
	}
	_, err = tx.Exec(`REPLACE INTO oda_agent_settings (settings_key, default_provider_id, default_model, managed_skills_dir, skills_root_dir, raw_json, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)`,
		"default",
		settings.DefaultProviderID,
		settings.DefaultModel,
		settings.ManagedSkillsDir,
		settings.SkillsRootDir,
		string(raw),
		toDBTime(settings.UpdatedAt),
	)
	return err
}

func (s *MySQLStore) saveTopics(tx *sql.Tx, items map[string]*models.Topic) error {
	keys := sortedKeys(items)
	for _, key := range keys {
		item := items[key]
		if item == nil {
			continue
		}
		if _, err := tx.Exec(`REPLACE INTO oda_agent_topic (topic_id, title, current_task_id, current_task_status, last_message_seq, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)`,
			item.TopicID,
			item.Title,
			nilIfEmpty(item.CurrentTaskID),
			nilIfEmpty(item.CurrentTaskStatus),
			item.LastMessageSeq,
			toDBTime(item.CreatedAt),
			toDBTime(item.UpdatedAt),
		); err != nil {
			return err
		}
	}
	return nil
}

func (s *MySQLStore) saveMessages(tx *sql.Tx, topics map[string]*models.Topic) error {
	topicKeys := sortedKeys(topics)
	for _, topicKey := range topicKeys {
		topic := topics[topicKey]
		if topic == nil {
			continue
		}
		for idx, msg := range topic.Messages {
			if msg.MessageSeq == 0 {
				msg.MessageSeq = int64(idx + 1)
			}
			rawUsage, _ := json.Marshal(msg.Usage)
			rawBlocks, _ := json.Marshal(msg.Blocks)
			rawError, _ := json.Marshal(msg.Error)
			if _, err := tx.Exec(`REPLACE INTO oda_agent_message (message_id, topic_id, task_id, message_seq, sender_type, status, content, provider_id, model_name, usage_json, blocks_json, error_json, resume_after_seq, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
				msg.MessageID,
				msg.TopicID,
				nilIfEmpty(msg.TaskID),
				msg.MessageSeq,
				msg.SenderType,
				msg.Status,
				msg.Content,
				nilIfEmpty(msg.ProviderID),
				nilIfEmpty(msg.Model),
				nullJSON(rawUsage),
				nullJSON(rawBlocks),
				nullJSON(rawError),
				msg.ResumeAfterSeq,
				toDBTime(msg.CreatedAt),
				toDBTime(msg.UpdatedAt),
			); err != nil {
				return err
			}
		}
	}
	return nil
}

func (s *MySQLStore) saveTasks(tx *sql.Tx, items map[string]*models.Task) error {
	keys := sortedKeys(items)
	for _, key := range keys {
		item := items[key]
		if item == nil {
			continue
		}
		rawError, _ := json.Marshal(item.Error)
		if _, err := tx.Exec(`REPLACE INTO oda_agent_task (task_id, topic_id, assistant_message_id, prompt, provider_id, model_name, task_status, last_event_seq, created_at, updated_at, started_at, finished_at, error_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
			item.TaskID,
			item.TopicID,
			item.AssistantMessageID,
			item.Prompt,
			item.ProviderID,
			item.ModelName,
			item.TaskStatus,
			item.LastEventSeq,
			toDBTime(item.CreatedAt),
			toDBTime(item.UpdatedAt),
			nullTime(item.StartedAt),
			nullTime(item.FinishedAt),
			nullJSON(rawError),
		); err != nil {
			return err
		}
	}
	return nil
}

func (s *MySQLStore) saveTaskEvents(tx *sql.Tx, items map[string][]models.TaskEvent) error {
	taskIDs := sortedSliceKeys(items)
	for _, taskID := range taskIDs {
		for _, item := range items[taskID] {
			raw, err := json.Marshal(item)
			if err != nil {
				return err
			}
			if _, err := tx.Exec(`INSERT INTO oda_agent_chunk (task_id, message_id, seq_id, record_type, event_type, content_type, correlation_id, payload_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`,
				item.TaskID,
				item.MessageID,
				item.SeqID,
				item.RecordType,
				nilIfEmpty(item.EventType),
				nilIfEmpty(item.ContentType),
				nilIfEmpty(item.CorrelationID),
				string(raw),
				toDBTime(item.CreatedAt),
			); err != nil {
				return err
			}
		}
	}
	return nil
}

func (s *MySQLStore) saveSkillDocuments(tx *sql.Tx, items map[string]*models.SkillDocument) error {
	keys := sortedKeys(items)
	for _, key := range keys {
		item := items[key]
		if item == nil {
			continue
		}
		if _, err := tx.Exec(`REPLACE INTO oda_skill_document (id, folder, relative_path, file_name, source, category, current_hash, current_version_id, version_count, last_change_source, last_change_summary, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
			item.ID,
			item.Folder,
			item.RelativePath,
			item.FileName,
			item.Source,
			item.Category,
			item.CurrentHash,
			nilIfEmpty(item.CurrentVersionID),
			item.VersionCount,
			item.LastChangeSource,
			item.LastChangeSummary,
			toDBTime(item.CreatedAt),
			toDBTime(item.UpdatedAt),
		); err != nil {
			return err
		}
		for _, version := range item.Versions {
			if _, err := tx.Exec(`REPLACE INTO oda_skill_document_version (id, document_id, version_no, change_source, change_summary, actor, content_hash, content, parent_version_id, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
				version.ID,
				version.DocumentID,
				version.VersionNo,
				version.ChangeSource,
				version.ChangeSummary,
				version.Actor,
				version.ContentHash,
				version.Content,
				nilIfEmpty(version.ParentVersionID),
				toDBTime(version.CreatedAt),
			); err != nil {
				return err
			}
		}
	}
	return nil
}

func (s *MySQLStore) saveSkillInstallations(tx *sql.Tx, items map[string]*models.SkillInstallation) error {
	keys := sortedKeys(items)
	for _, key := range keys {
		item := items[key]
		if item == nil {
			continue
		}
		if _, err := tx.Exec(`REPLACE INTO oda_skill_installation (id, item_id, folder, source, installed_at) VALUES (?, ?, ?, ?, ?)`,
			item.ID,
			item.ItemID,
			item.Folder,
			item.Source,
			toDBTime(item.InstalledAt),
		); err != nil {
			return err
		}
	}
	return nil
}

func (s *MySQLStore) saveSkillRuntime(tx *sql.Tx, items map[string]*models.SkillRuntimeConfig) error {
	keys := sortedKeys(items)
	for _, key := range keys {
		item := items[key]
		if item == nil || item.Enabled == nil {
			continue
		}
		if _, err := tx.Exec(`REPLACE INTO oda_skill_runtime (skill_id, enabled) VALUES (?, ?)`, item.SkillID, *item.Enabled); err != nil {
			return err
		}
	}
	return nil
}

func (s *MySQLStore) saveMCPServers(tx *sql.Tx, items map[string]*models.MCPServer) error {
	keys := sortedKeys(items)
	for _, key := range keys {
		item := items[key]
		if item == nil {
			continue
		}
		raw, err := json.Marshal(item)
		if err != nil {
			return err
		}
		if _, err := tx.Exec(`REPLACE INTO oda_mcp_server (id, name, connection_type, tool_prefix, enabled, raw_json, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
			item.ID,
			item.Name,
			item.ConnectionType,
			nilIfEmpty(item.ToolPrefix),
			item.Enabled,
			string(raw),
			toDBTime(item.CreatedAt),
			toDBTime(item.UpdatedAt),
		); err != nil {
			return err
		}
		for _, version := range item.Versions {
			if _, err := tx.Exec(`REPLACE INTO oda_mcp_server_version (id, server_id, version_no, summary, created_at) VALUES (?, ?, ?, ?, ?)`,
				version.ID,
				item.ID,
				version.VersionNo,
				version.Summary,
				toDBTime(version.CreatedAt),
			); err != nil {
				return err
			}
		}
	}
	return nil
}

func (s *MySQLStore) syncSettings(tx *sql.Tx, prev models.AgentSettings, next models.AgentSettings) error {
	if sameJSON(prev, next) {
		return nil
	}
	return s.saveSettings(tx, next)
}

func (s *MySQLStore) syncTopics(tx *sql.Tx, prev map[string]*models.Topic, next map[string]*models.Topic) error {
	for key := range prev {
		if next[key] != nil {
			continue
		}
		if _, err := tx.Exec(`DELETE FROM oda_agent_topic WHERE topic_id = ?`, key); err != nil {
			return err
		}
	}
	changed := make(map[string]*models.Topic)
	for key, item := range next {
		if item == nil {
			continue
		}
		if sameJSON(prev[key], item) {
			continue
		}
		changed[key] = item
	}
	if len(changed) == 0 {
		return nil
	}
	return s.saveTopics(tx, changed)
}

func (s *MySQLStore) syncMessages(tx *sql.Tx, prev map[string]models.Message, next map[string]models.Message) error {
	for key := range prev {
		if _, ok := next[key]; ok {
			continue
		}
		if _, err := tx.Exec(`DELETE FROM oda_agent_message WHERE message_id = ?`, key); err != nil {
			return err
		}
	}
	if len(next) == 0 {
		return nil
	}
	changedTopics := map[string]*models.Topic{}
	for key, item := range next {
		if prevItem, ok := prev[key]; ok && sameJSON(prevItem, item) {
			continue
		}
		topic := changedTopics[item.TopicID]
		if topic == nil {
			topic = &models.Topic{TopicID: item.TopicID, Messages: []models.Message{}}
			changedTopics[item.TopicID] = topic
		}
		topic.Messages = append(topic.Messages, item)
	}
	if len(changedTopics) == 0 {
		return nil
	}
	for _, topic := range changedTopics {
		sort.Slice(topic.Messages, func(i, j int) bool {
			if topic.Messages[i].MessageSeq == topic.Messages[j].MessageSeq {
				return topic.Messages[i].CreatedAt < topic.Messages[j].CreatedAt
			}
			return topic.Messages[i].MessageSeq < topic.Messages[j].MessageSeq
		})
	}
	return s.saveMessages(tx, changedTopics)
}

func (s *MySQLStore) syncTasks(tx *sql.Tx, prev map[string]*models.Task, next map[string]*models.Task) error {
	for key := range prev {
		if next[key] != nil {
			continue
		}
		if _, err := tx.Exec(`DELETE FROM oda_agent_task WHERE task_id = ?`, key); err != nil {
			return err
		}
	}
	changed := make(map[string]*models.Task)
	for key, item := range next {
		if item == nil {
			continue
		}
		if sameJSON(prev[key], item) {
			continue
		}
		changed[key] = item
	}
	if len(changed) == 0 {
		return nil
	}
	return s.saveTasks(tx, changed)
}

func (s *MySQLStore) syncTaskEvents(tx *sql.Tx, prev map[string][]models.TaskEvent, next map[string][]models.TaskEvent) error {
	rewrite := map[string][]models.TaskEvent{}
	seen := map[string]struct{}{}
	for key, items := range prev {
		seen[key] = struct{}{}
		if sameJSON(items, next[key]) {
			continue
		}
		if _, err := tx.Exec(`DELETE FROM oda_agent_chunk WHERE task_id = ?`, key); err != nil {
			return err
		}
		if len(next[key]) > 0 {
			rewrite[key] = next[key]
		}
	}
	for key, items := range next {
		if _, ok := seen[key]; ok {
			continue
		}
		if _, err := tx.Exec(`DELETE FROM oda_agent_chunk WHERE task_id = ?`, key); err != nil {
			return err
		}
		if len(items) > 0 {
			rewrite[key] = items
		}
	}
	if len(rewrite) == 0 {
		return nil
	}
	return s.saveTaskEvents(tx, rewrite)
}

func (s *MySQLStore) syncSkillDocuments(tx *sql.Tx, prev map[string]*models.SkillDocument, next map[string]*models.SkillDocument) error {
	for key := range prev {
		if next[key] != nil {
			continue
		}
		if _, err := tx.Exec(`DELETE FROM oda_skill_document_version WHERE document_id = ?`, key); err != nil {
			return err
		}
		if _, err := tx.Exec(`DELETE FROM oda_skill_document WHERE id = ?`, key); err != nil {
			return err
		}
	}
	changed := make(map[string]*models.SkillDocument)
	for key, item := range next {
		if item == nil {
			continue
		}
		if sameJSON(prev[key], item) {
			continue
		}
		if _, err := tx.Exec(`DELETE FROM oda_skill_document_version WHERE document_id = ?`, key); err != nil {
			return err
		}
		changed[key] = item
	}
	if len(changed) == 0 {
		return nil
	}
	return s.saveSkillDocuments(tx, changed)
}

func (s *MySQLStore) syncSkillInstallations(tx *sql.Tx, prev map[string]*models.SkillInstallation, next map[string]*models.SkillInstallation) error {
	for key := range prev {
		if next[key] != nil {
			continue
		}
		if _, err := tx.Exec(`DELETE FROM oda_skill_installation WHERE folder = ?`, key); err != nil {
			return err
		}
	}
	changed := make(map[string]*models.SkillInstallation)
	for key, item := range next {
		if item == nil {
			continue
		}
		if sameJSON(prev[key], item) {
			continue
		}
		changed[key] = item
	}
	if len(changed) == 0 {
		return nil
	}
	return s.saveSkillInstallations(tx, changed)
}

func (s *MySQLStore) syncSkillRuntime(tx *sql.Tx, prev map[string]*models.SkillRuntimeConfig, next map[string]*models.SkillRuntimeConfig) error {
	for key, item := range prev {
		nextItem := next[key]
		if nextItem != nil && nextItem.Enabled != nil {
			continue
		}
		if item == nil || item.Enabled == nil {
			continue
		}
		if _, err := tx.Exec(`DELETE FROM oda_skill_runtime WHERE skill_id = ?`, key); err != nil {
			return err
		}
	}
	changed := make(map[string]*models.SkillRuntimeConfig)
	for key, item := range next {
		if item == nil || item.Enabled == nil {
			continue
		}
		if sameJSON(prev[key], item) {
			continue
		}
		changed[key] = item
	}
	if len(changed) == 0 {
		return nil
	}
	return s.saveSkillRuntime(tx, changed)
}

func (s *MySQLStore) syncMCPServers(tx *sql.Tx, prev map[string]*models.MCPServer, next map[string]*models.MCPServer) error {
	for key := range prev {
		if next[key] != nil {
			continue
		}
		if _, err := tx.Exec(`DELETE FROM oda_mcp_server_version WHERE server_id = ?`, key); err != nil {
			return err
		}
		if _, err := tx.Exec(`DELETE FROM oda_mcp_server WHERE id = ?`, key); err != nil {
			return err
		}
	}
	changed := make(map[string]*models.MCPServer)
	for key, item := range next {
		if item == nil {
			continue
		}
		if sameJSON(prev[key], item) {
			continue
		}
		if _, err := tx.Exec(`DELETE FROM oda_mcp_server_version WHERE server_id = ?`, key); err != nil {
			return err
		}
		changed[key] = item
	}
	if len(changed) == 0 {
		return nil
	}
	return s.saveMCPServers(tx, changed)
}

func flattenMessages(topics map[string]*models.Topic) map[string]models.Message {
	out := map[string]models.Message{}
	for topicID, topic := range topics {
		if topic == nil {
			continue
		}
		for idx, msg := range topic.Messages {
			if strings.TrimSpace(msg.MessageID) == "" {
				continue
			}
			if strings.TrimSpace(msg.TopicID) == "" {
				msg.TopicID = topicID
			}
			if msg.MessageSeq == 0 {
				msg.MessageSeq = int64(idx + 1)
			}
			out[msg.MessageID] = msg
		}
	}
	return out
}

func mustCloneSnapshot(snapshot models.StateSnapshot) models.StateSnapshot {
	cloned := models.StateSnapshot{}
	payload, err := json.Marshal(snapshot)
	if err != nil {
		panic(err)
	}
	if len(payload) == 0 {
		return cloned
	}
	if err := json.Unmarshal(payload, &cloned); err != nil {
		panic(err)
	}
	if cloned.Topics == nil {
		cloned.Topics = map[string]*models.Topic{}
	}
	if cloned.Tasks == nil {
		cloned.Tasks = map[string]*models.Task{}
	}
	if cloned.TaskEvents == nil {
		cloned.TaskEvents = map[string][]models.TaskEvent{}
	}
	if cloned.SkillDocuments == nil {
		cloned.SkillDocuments = map[string]*models.SkillDocument{}
	}
	if cloned.SkillRuntime == nil {
		cloned.SkillRuntime = map[string]*models.SkillRuntimeConfig{}
	}
	if cloned.SkillInstallations == nil {
		cloned.SkillInstallations = map[string]*models.SkillInstallation{}
	}
	if cloned.MCPServers == nil {
		cloned.MCPServers = map[string]*models.MCPServer{}
	}
	return cloned
}

func sameJSON(left interface{}, right interface{}) bool {
	leftPayload, err := json.Marshal(left)
	if err != nil {
		return false
	}
	rightPayload, err := json.Marshal(right)
	if err != nil {
		return false
	}
	return string(leftPayload) == string(rightPayload)
}

type timeCarrier struct {
	Time  sql.NullTime
	Bytes sql.RawBytes
}

func (t *timeCarrier) Scan(src interface{}) error {
	switch value := src.(type) {
	case time.Time:
		t.Time = sql.NullTime{Time: value.UTC(), Valid: true}
		return nil
	case []byte:
		t.Bytes = append(t.Bytes[:0], value...)
		return nil
	case string:
		t.Bytes = append(t.Bytes[:0], value...)
		return nil
	case nil:
		t.Time = sql.NullTime{}
		t.Bytes = nil
		return nil
	default:
		return fmt.Errorf("unsupported time scan type %T", src)
	}
}

func (t timeCarrier) String() string {
	if t.Time.Valid {
		return t.Time.Time.UTC().Format(time.RFC3339)
	}
	if len(t.Bytes) == 0 {
		return ""
	}
	text := string(t.Bytes)
	if parsed, err := time.Parse("2006-01-02 15:04:05", text); err == nil {
		return parsed.UTC().Format(time.RFC3339)
	}
	if parsed := util.ParseTime(text); !parsed.IsZero() {
		return parsed.Format(time.RFC3339)
	}
	return ""
}

func toDBTime(value string) interface{} {
	parsed := util.ParseTime(value)
	if parsed.IsZero() {
		return nil
	}
	return parsed
}

func nullTime(value string) interface{} {
	return toDBTime(value)
}

func nilIfEmpty(value string) interface{} {
	if strings.TrimSpace(value) == "" {
		return nil
	}
	return value
}

func nullJSON(value []byte) interface{} {
	text := strings.TrimSpace(string(value))
	if text == "" || text == "null" || text == "{}" {
		return nil
	}
	return text
}

func sortedKeys[T any](items map[string]*T) []string {
	keys := make([]string, 0, len(items))
	for key := range items {
		keys = append(keys, key)
	}
	sort.Strings(keys)
	return keys
}

func sortedSliceKeys[T any](items map[string][]T) []string {
	keys := make([]string, 0, len(items))
	for key := range items {
		keys = append(keys, key)
	}
	sort.Strings(keys)
	return keys
}

func boolPtr(value bool) *bool {
	return &value
}

func nullableString(value sql.NullString) string {
	if !value.Valid {
		return ""
	}
	return value.String
}
