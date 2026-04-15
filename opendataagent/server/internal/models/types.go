package models

import (
	"encoding/json"
	"strings"
)

type ModelConfig struct {
	Name    string `json:"name"`
	Enabled bool   `json:"enabled"`
}

func (m *ModelConfig) UnmarshalJSON(data []byte) error {
	var stringValue string
	if err := json.Unmarshal(data, &stringValue); err == nil {
		m.Name = strings.TrimSpace(stringValue)
		m.Enabled = true
		return nil
	}

	type modelAlias struct {
		Name    string `json:"name"`
		Enabled *bool  `json:"enabled"`
	}
	var raw modelAlias
	if err := json.Unmarshal(data, &raw); err != nil {
		return err
	}
	m.Name = strings.TrimSpace(raw.Name)
	if raw.Enabled == nil {
		m.Enabled = true
	} else {
		m.Enabled = *raw.Enabled
	}
	return nil
}

type ProviderConfig struct {
	ProviderID   string        `json:"provider_id"`
	ProviderType string        `json:"provider_type"`
	DisplayName  string        `json:"display_name"`
	DefaultModel string        `json:"default_model"`
	Models       []ModelConfig `json:"models"`
	BaseURL      string        `json:"base_url"`
	APIToken     string        `json:"api_token"`
	Enabled      bool          `json:"enabled"`
}

type AgentSettings struct {
	DefaultProviderID string           `json:"default_provider_id"`
	DefaultModel      string           `json:"default_model"`
	ProviderID        string           `json:"provider_id"`
	Model             string           `json:"model"`
	ManagedSkillsDir  string           `json:"managed_skills_dir"`
	SkillsRootDir     string           `json:"skills_root_dir"`
	SessionMySQLDB    string           `json:"session_mysql_database"`
	AdminToken        string           `json:"admin_token,omitempty"`
	Providers         []ProviderConfig `json:"providers"`
	UpdatedAt         string           `json:"updated_at"`
}

type ErrorPayload struct {
	Code    string `json:"code,omitempty"`
	Message string `json:"message,omitempty"`
}

type ToolPayload struct {
	ID     string      `json:"id"`
	Name   string      `json:"name"`
	Status string      `json:"status"`
	Input  interface{} `json:"input,omitempty"`
	Output interface{} `json:"output,omitempty"`
}

type MessageBlock struct {
	BlockID string       `json:"block_id"`
	Type    string       `json:"type"`
	Status  string       `json:"status"`
	Text    string       `json:"text,omitempty"`
	Tool    *ToolPayload `json:"tool,omitempty"`
}

type Message struct {
	MessageID      string                 `json:"message_id"`
	TopicID        string                 `json:"topic_id"`
	TaskID         string                 `json:"task_id,omitempty"`
	MessageSeq     int64                  `json:"message_seq,omitempty"`
	SenderType     string                 `json:"sender_type"`
	Content        string                 `json:"content"`
	Status         string                 `json:"status"`
	ProviderID     string                 `json:"provider_id,omitempty"`
	Model          string                 `json:"model,omitempty"`
	CreatedAt      string                 `json:"created_at"`
	UpdatedAt      string                 `json:"updated_at"`
	ResumeAfterSeq int64                  `json:"resume_after_seq"`
	Usage          map[string]interface{} `json:"usage,omitempty"`
	Error          *ErrorPayload          `json:"error,omitempty"`
	Blocks         []MessageBlock         `json:"blocks,omitempty"`
}

type Topic struct {
	TopicID           string    `json:"topic_id"`
	Title             string    `json:"title"`
	MessageCount      int       `json:"message_count"`
	CurrentTaskID     string    `json:"current_task_id,omitempty"`
	CurrentTaskStatus string    `json:"current_task_status,omitempty"`
	LastMessageSeq    int64     `json:"last_message_seq"`
	CreatedAt         string    `json:"created_at"`
	UpdatedAt         string    `json:"updated_at"`
	Messages          []Message `json:"messages,omitempty"`
}

type Task struct {
	TaskID             string        `json:"task_id"`
	TopicID            string        `json:"topic_id"`
	AssistantMessageID string        `json:"assistant_message_id"`
	Prompt             string        `json:"prompt"`
	ProviderID         string        `json:"provider_id"`
	ModelName          string        `json:"model_name"`
	TaskStatus         string        `json:"task_status"`
	LastEventSeq       int64         `json:"last_event_seq"`
	CreatedAt          string        `json:"created_at"`
	UpdatedAt          string        `json:"updated_at"`
	StartedAt          string        `json:"started_at,omitempty"`
	FinishedAt         string        `json:"finished_at,omitempty"`
	Error              *ErrorPayload `json:"error,omitempty"`
}

type TaskEvent struct {
	SeqID         int64                  `json:"seq_id"`
	TaskID        string                 `json:"task_id"`
	MessageID     string                 `json:"message_id,omitempty"`
	Type          string                 `json:"type,omitempty"`
	RecordType    string                 `json:"record_type"`
	EventType     string                 `json:"event_type,omitempty"`
	ContentType   string                 `json:"content_type,omitempty"`
	CorrelationID string                 `json:"correlation_id,omitempty"`
	RequestID     string                 `json:"request_id,omitempty"`
	ChunkID       int64                  `json:"chunk_id,omitempty"`
	Content       string                 `json:"content,omitempty"`
	Message       map[string]interface{} `json:"message,omitempty"`
	Index         *int                   `json:"index,omitempty"`
	ContentBlock  map[string]interface{} `json:"content_block,omitempty"`
	Payload       map[string]interface{} `json:"payload,omitempty"`
	Delta         map[string]interface{} `json:"delta,omitempty"`
	Data          map[string]interface{} `json:"data,omitempty"`
	Metadata      map[string]interface{} `json:"metadata,omitempty"`
	CreatedAt     string                 `json:"created_at"`
}

type SkillRuntimeConfig struct {
	SkillID string `json:"skill_id"`
	Enabled *bool  `json:"enabled,omitempty"`
}

type SkillDocumentVersion struct {
	ID              string `json:"id"`
	DocumentID      string `json:"document_id"`
	VersionNo       int    `json:"version_no"`
	ChangeSource    string `json:"change_source"`
	ChangeSummary   string `json:"change_summary"`
	Actor           string `json:"actor"`
	ContentHash     string `json:"content_hash"`
	FileSize        int    `json:"file_size"`
	ParentVersionID string `json:"parent_version_id,omitempty"`
	CreatedAt       string `json:"created_at"`
	IsCurrent       bool   `json:"is_current"`
	Content         string `json:"content,omitempty"`
}

type SkillDocument struct {
	ID                string                 `json:"id"`
	Folder            string                 `json:"folder"`
	RelativePath      string                 `json:"relative_path"`
	FileName          string                 `json:"file_name"`
	Category          string                 `json:"category"`
	ContentType       string                 `json:"content_type"`
	Source            string                 `json:"source"`
	CurrentContent    string                 `json:"current_content"`
	CurrentHash       string                 `json:"current_hash"`
	CurrentVersionID  string                 `json:"current_version_id,omitempty"`
	VersionCount      int                    `json:"version_count"`
	LastChangeSource  string                 `json:"last_change_source"`
	LastChangeSummary string                 `json:"last_change_summary"`
	CreatedAt         string                 `json:"created_at"`
	UpdatedAt         string                 `json:"updated_at"`
	Editable          bool                   `json:"editable"`
	Enabled           bool                   `json:"enabled"`
	Metadata          map[string]interface{} `json:"metadata,omitempty"`
	Versions          []SkillDocumentVersion `json:"versions,omitempty"`
}

type SkillInstallation struct {
	ID          string `json:"id"`
	ItemID      string `json:"item_id"`
	Folder      string `json:"folder"`
	Source      string `json:"source"`
	InstalledAt string `json:"installed_at"`
}

type SkillMarketItem struct {
	ID          string   `json:"id"`
	Folder      string   `json:"folder"`
	Name        string   `json:"name"`
	Description string   `json:"description"`
	Emoji       string   `json:"emoji,omitempty"`
	Tags        []string `json:"tags,omitempty"`
	Category    string   `json:"category"`
	Status      string   `json:"status"`
	Installed   bool     `json:"installed"`
	Enabled     bool     `json:"enabled"`
	Source      string   `json:"source"`
	Version     string   `json:"version"`
	Content     string   `json:"content,omitempty"`
}

type MCPServerVersion struct {
	ID        string `json:"id"`
	VersionNo int    `json:"version_no"`
	Summary   string `json:"summary"`
	CreatedAt string `json:"created_at"`
}

type MCPServer struct {
	ID             string             `json:"id"`
	Name           string             `json:"name"`
	ConnectionType string             `json:"connection_type"`
	ToolPrefix     string             `json:"tool_prefix"`
	Enabled        bool               `json:"enabled"`
	Command        string             `json:"command,omitempty"`
	Args           []string           `json:"args,omitempty"`
	Env            map[string]string  `json:"env,omitempty"`
	URL            string             `json:"url,omitempty"`
	Headers        map[string]string  `json:"headers,omitempty"`
	CreatedAt      string             `json:"created_at"`
	UpdatedAt      string             `json:"updated_at"`
	Versions       []MCPServerVersion `json:"versions,omitempty"`
}

type StateSnapshot struct {
	Settings           AgentSettings                  `json:"settings"`
	Topics             map[string]*Topic              `json:"topics"`
	Tasks              map[string]*Task               `json:"tasks"`
	TaskEvents         map[string][]TaskEvent         `json:"task_events"`
	SkillDocuments     map[string]*SkillDocument      `json:"skill_documents"`
	SkillRuntime       map[string]*SkillRuntimeConfig `json:"skill_runtime"`
	SkillInstallations map[string]*SkillInstallation  `json:"skill_installations"`
	MCPServers         map[string]*MCPServer          `json:"mcp_servers"`
}

type DeliverMessageRequest struct {
	TopicID    string `json:"topic_id"`
	Content    string `json:"content"`
	ProviderID string `json:"provider_id"`
	Model      string `json:"model"`
}

type UpdateTopicRequest struct {
	Title string `json:"title"`
}

type UpdateSkillDocumentRequest struct {
	Content       string `json:"content"`
	ChangeSummary string `json:"change_summary"`
}

type CompareSkillDocumentRequest struct {
	LeftVersionID  string `json:"left_version_id"`
	RightVersionID string `json:"right_version_id"`
}

type SkillSyncResult struct {
	DocumentCount     int      `json:"document_count"`
	ChangedDocuments  []string `json:"changed_documents"`
	ImportedDocuments []string `json:"imported_documents"`
}

type MCPSmokeResult struct {
	OK      bool   `json:"ok"`
	Message string `json:"message"`
}
