package store

import (
	"fmt"
	"path/filepath"

	"opendataagent/server/internal/config"
	"opendataagent/server/internal/models"
)

type Store interface {
	Load() (models.StateSnapshot, error)
	Save(models.StateSnapshot) error
	Close() error
}

func New(cfg config.Config) (Store, error) {
	switch cfg.StoreDriver {
	case "", "file":
		return NewFileStore(filepath.Join(cfg.StateDir, "state.json")), nil
	case "mysql":
		return NewMySQLStore(cfg)
	default:
		return nil, fmt.Errorf("unsupported store driver: %s", cfg.StoreDriver)
	}
}
