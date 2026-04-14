package store

import (
	"encoding/json"
	"os"
	"path/filepath"

	"opendataagent/server/internal/models"
)

type FileStore struct {
	path string
}

func NewFileStore(path string) *FileStore {
	return &FileStore{path: path}
}

func (s *FileStore) Load() (models.StateSnapshot, error) {
	var snapshot models.StateSnapshot
	data, err := os.ReadFile(s.path)
	if err != nil {
		if os.IsNotExist(err) {
			return snapshot, nil
		}
		return snapshot, err
	}
	if len(data) == 0 {
		return snapshot, nil
	}
	if err := json.Unmarshal(data, &snapshot); err != nil {
		return models.StateSnapshot{}, err
	}
	return snapshot, nil
}

func (s *FileStore) Save(snapshot models.StateSnapshot) error {
	if err := os.MkdirAll(filepath.Dir(s.path), 0755); err != nil {
		return err
	}
	payload, err := json.MarshalIndent(snapshot, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(s.path, payload, 0644)
}

func (s *FileStore) Close() error { return nil }
