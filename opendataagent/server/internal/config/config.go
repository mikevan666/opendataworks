package config

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

type Config struct {
	Addr             string
	ProjectRoot      string
	StateDir         string
	SkillsDir        string
	ManagedSkillsDir string
	BundledSkillsDir string
	SharedSkillsDir  string
	AdminToken       string
	StoreDriver      string
	MySQLDSN         string
}

func Load() Config {
	cwd, _ := os.Getwd()
	stateDir := getenv("ODA_STATE_DIR", filepath.Join(cwd, "data"))
	skillsDir := getenv("ODA_SKILLS_DIR", filepath.Join(cwd, "skills"))
	storeDriver := strings.ToLower(getenv("ODA_STORE_DRIVER", "file"))
	return Config{
		Addr:             getenv("ODA_ADDR", ":18900"),
		ProjectRoot:      cwd,
		StateDir:         stateDir,
		SkillsDir:        skillsDir,
		ManagedSkillsDir: getenv("ODA_MANAGED_SKILLS_DIR", filepath.Join(stateDir, "skills", "managed")),
		BundledSkillsDir: getenv("ODA_BUNDLED_SKILLS_DIR", filepath.Join(skillsDir, "bundled")),
		SharedSkillsDir:  resolveSharedSkillsDir(cwd),
		AdminToken:       stringsTrim(os.Getenv("ODA_ADMIN_TOKEN")),
		StoreDriver:      storeDriver,
		MySQLDSN:         resolveMySQLDSN(storeDriver),
	}
}

func resolveSharedSkillsDir(cwd string) string {
	if configured := stringsTrim(os.Getenv("ODA_SHARED_SKILLS_DIR")); configured != "" {
		return configured
	}
	candidate := filepath.Clean(filepath.Join(cwd, "..", "..", "skills"))
	if info, err := os.Stat(candidate); err == nil && info.IsDir() {
		return candidate
	}
	return ""
}

func getenv(key string, fallback string) string {
	if value := stringsTrim(os.Getenv(key)); value != "" {
		return value
	}
	return fallback
}

func stringsTrim(value string) string {
	return strings.TrimSpace(value)
}

func resolveMySQLDSN(storeDriver string) string {
	if storeDriver != "mysql" {
		return stringsTrim(os.Getenv("ODA_MYSQL_DSN"))
	}
	if dsn := stringsTrim(os.Getenv("ODA_MYSQL_DSN")); dsn != "" {
		return dsn
	}

	host := getenv("MYSQL_HOST", "")
	port := getenv("MYSQL_PORT", "3306")
	user := getenv("MYSQL_USER", "")
	password := stringsTrim(os.Getenv("MYSQL_PASSWORD"))
	database := getenv("ODA_MYSQL_DATABASE", getenv("SESSION_MYSQL_DATABASE", "opendataagent"))
	if host == "" || user == "" || database == "" {
		return ""
	}
	return fmt.Sprintf("%s:%s@tcp(%s:%s)/%s?charset=utf8mb4&parseTime=true&loc=UTC", user, password, host, port, database)
}
