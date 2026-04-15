package skills

import (
	"archive/zip"
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"sort"
	"strings"

	"gopkg.in/yaml.v3"

	"opendataagent/server/internal/models"
	"opendataagent/server/internal/util"
)

type Entry struct {
	ID             string
	Folder         string
	Name           string
	Description    string
	Emoji          string
	Tags           []string
	Category       string
	Source         string
	Version        string
	BaseDir        string
	FilePath       string
	Content        string
	RuntimeContent string
	Frontmatter    map[string]interface{}
}

type Service struct {
	BundledDir string
	ManagedDir string
}

func (s Service) SyncSharedSource(sharedRoot string, skillsRoot string) error {
	sharedRoot = strings.TrimSpace(sharedRoot)
	if sharedRoot == "" {
		return nil
	}
	info, err := os.Stat(sharedRoot)
	if err != nil {
		if os.IsNotExist(err) {
			return nil
		}
		return err
	}
	if !info.IsDir() {
		return fmt.Errorf("shared skills root is not a directory: %s", sharedRoot)
	}
	if strings.TrimSpace(skillsRoot) == "" {
		return errors.New("skills root is required")
	}

	bundledTarget := filepath.Join(skillsRoot, "bundled")
	binTarget := filepath.Join(skillsRoot, "bin")
	libTarget := filepath.Join(skillsRoot, "lib")

	if err := os.RemoveAll(bundledTarget); err != nil {
		return err
	}
	if err := os.RemoveAll(binTarget); err != nil {
		return err
	}
	if err := os.RemoveAll(libTarget); err != nil {
		return err
	}
	if err := os.MkdirAll(bundledTarget, 0755); err != nil {
		return err
	}

	for _, pair := range []struct {
		src string
		dst string
	}{
		{src: filepath.Join(sharedRoot, "bin"), dst: binTarget},
		{src: filepath.Join(sharedRoot, "lib"), dst: libTarget},
	} {
		if stat, err := os.Stat(pair.src); err == nil && stat.IsDir() {
			if err := copyDir(pair.src, pair.dst); err != nil {
				return err
			}
		}
	}

	for _, group := range []string{"platform", "generic"} {
		groupRoot := filepath.Join(sharedRoot, group)
		entries, err := os.ReadDir(groupRoot)
		if err != nil {
			if os.IsNotExist(err) {
				continue
			}
			return err
		}
		for _, entry := range entries {
			if !entry.IsDir() {
				continue
			}
			srcPath := filepath.Join(groupRoot, entry.Name())
			dstPath := filepath.Join(bundledTarget, entry.Name())
			if err := copyDir(srcPath, dstPath); err != nil {
				return err
			}
		}
	}
	return nil
}

func (s Service) ScanRuntimeEntries() ([]Entry, error) {
	bundled, err := s.scanDir(s.BundledDir, "bundled")
	if err != nil {
		return nil, err
	}
	managed, err := s.scanDir(s.ManagedDir, "managed")
	if err != nil {
		return nil, err
	}

	merged := map[string]Entry{}
	for _, entry := range bundled {
		merged[entry.Folder] = entry
	}
	for _, entry := range managed {
		merged[entry.Folder] = entry
	}

	out := make([]Entry, 0, len(merged))
	for _, entry := range merged {
		out = append(out, entry)
	}
	sort.Slice(out, func(i, j int) bool { return out[i].Folder < out[j].Folder })
	return out, nil
}

func (s Service) ScanCatalogEntries() ([]Entry, error) {
	bundled, err := s.scanDir(s.BundledDir, "bundled")
	if err != nil {
		return nil, err
	}
	managed, err := s.scanDir(s.ManagedDir, "managed")
	if err != nil {
		return nil, err
	}

	byFolder := make(map[string]Entry)
	for _, entry := range bundled {
		byFolder[entry.Folder] = entry
	}
	for _, entry := range managed {
		byFolder[entry.Folder] = entry
	}

	out := make([]Entry, 0, len(byFolder))
	for _, entry := range byFolder {
		out = append(out, entry)
	}
	sort.Slice(out, func(i, j int) bool { return out[i].Folder < out[j].Folder })
	return out, nil
}

func (s Service) BuildMarketItems(runtimeState map[string]*models.SkillRuntimeConfig, installs map[string]*models.SkillInstallation) ([]models.SkillMarketItem, error) {
	entries, err := s.ScanCatalogEntries()
	if err != nil {
		return nil, err
	}
	items := make([]models.SkillMarketItem, 0, len(entries))
	for _, entry := range entries {
		_, installed := installs[entry.Folder]
		enabled := true
		if state, ok := runtimeState[entry.Folder]; ok && state != nil && state.Enabled != nil {
			enabled = *state.Enabled
		}
		if entry.Source == "managed" {
			installed = true
		}
		items = append(items, models.SkillMarketItem{
			ID:          entry.Folder,
			Folder:      entry.Folder,
			Name:        entry.Name,
			Description: entry.Description,
			Emoji:       entry.Emoji,
			Tags:        append([]string(nil), entry.Tags...),
			Category:    entry.Category,
			Status:      "open",
			Installed:   installed,
			Enabled:     enabled,
			Source:      entry.Source,
			Version:     entry.Version,
			Content:     entry.Content,
		})
	}
	return items, nil
}

func (s Service) DeleteManagedSkill(folder string) error {
	folder = strings.TrimSpace(folder)
	if folder == "" || filepath.Base(folder) != folder {
		return errors.New("invalid skill folder")
	}
	targetDir := filepath.Join(s.ManagedDir, folder)
	if _, err := os.Stat(filepath.Join(targetDir, "SKILL.md")); err != nil {
		if os.IsNotExist(err) {
			return errors.New("managed skill not found")
		}
		return err
	}
	return os.RemoveAll(targetDir)
}

func (s Service) InstallBundledSkill(itemID string) (string, error) {
	sourceDir := filepath.Join(s.BundledDir, itemID)
	if _, err := os.Stat(filepath.Join(sourceDir, "SKILL.md")); err != nil {
		return "", errors.New("bundled skill not found")
	}
	targetDir := filepath.Join(s.ManagedDir, itemID)
	if err := os.RemoveAll(targetDir); err != nil {
		return "", err
	}
	if err := copyDir(sourceDir, targetDir); err != nil {
		return "", err
	}
	meta := map[string]string{
		"source": "bundled",
		"itemId": itemID,
	}
	payload, _ := json.MarshalIndent(meta, "", "  ")
	if err := os.WriteFile(filepath.Join(targetDir, ".opendataagent-meta.json"), payload, 0644); err != nil {
		return "", err
	}
	return targetDir, nil
}

func (s Service) ImportSkillPackage(fileName string, payload []byte, folder string) (string, error) {
	targetFolder := sanitizeFolderName(folder)
	if bytes.HasPrefix(payload, []byte("PK\x03\x04")) || strings.HasSuffix(strings.ToLower(strings.TrimSpace(fileName)), ".zip") {
		return s.importZipPackage(fileName, payload, targetFolder)
	}
	if targetFolder == "" {
		targetFolder = sanitizeFolderName(strings.TrimSuffix(filepath.Base(fileName), filepath.Ext(fileName)))
	}
	if targetFolder == "" {
		return "", errors.New("skill folder is required")
	}
	if len(bytes.TrimSpace(payload)) == 0 {
		return "", errors.New("uploaded skill file is empty")
	}
	targetDir := filepath.Join(s.ManagedDir, targetFolder)
	if err := os.RemoveAll(targetDir); err != nil {
		return "", err
	}
	if err := os.MkdirAll(targetDir, 0755); err != nil {
		return "", err
	}
	if err := os.WriteFile(filepath.Join(targetDir, "SKILL.md"), payload, 0644); err != nil {
		return "", err
	}
	if err := writeManagedMeta(targetDir, "uploaded", targetFolder); err != nil {
		return "", err
	}
	return targetDir, nil
}

func (s Service) BuildDocuments() ([]models.SkillDocument, error) {
	entries, err := s.ScanRuntimeEntries()
	if err != nil {
		return nil, err
	}
	docs := make([]models.SkillDocument, 0, len(entries))
	now := util.Now()
	for _, entry := range entries {
		docs = append(docs, models.SkillDocument{
			ID:                entry.Folder,
			Folder:            entry.Folder,
			RelativePath:      filepath.ToSlash(filepath.Join(entry.Folder, "SKILL.md")),
			FileName:          "SKILL.md",
			Category:          entry.Category,
			ContentType:       "markdown",
			Source:            entry.Source,
			CurrentContent:    entry.Content,
			CurrentHash:       util.HashText(entry.Content),
			VersionCount:      0,
			LastChangeSource:  "sync",
			LastChangeSummary: "initial sync",
			CreatedAt:         now,
			UpdatedAt:         now,
			Editable:          entry.Source == "managed",
			Metadata:          cloneMap(entry.Frontmatter),
		})
	}
	return docs, nil
}

func (s Service) EnsureManagedSkill(folder string, bundledDir string) (string, error) {
	targetDir := filepath.Join(s.ManagedDir, folder)
	if _, err := os.Stat(filepath.Join(targetDir, "SKILL.md")); err == nil {
		return targetDir, nil
	}
	sourceDir := filepath.Join(bundledDir, folder)
	if _, err := os.Stat(filepath.Join(sourceDir, "SKILL.md")); err != nil {
		return "", errors.New("skill cannot be edited because managed copy does not exist")
	}
	if err := copyDir(sourceDir, targetDir); err != nil {
		return "", err
	}
	return targetDir, nil
}

func (s Service) importZipPackage(fileName string, payload []byte, folder string) (string, error) {
	reader, err := zip.NewReader(bytes.NewReader(payload), int64(len(payload)))
	if err != nil {
		return "", fmt.Errorf("open zip package: %w", err)
	}
	tempRoot, err := os.MkdirTemp("", "oda-skill-import-*")
	if err != nil {
		return "", err
	}
	defer os.RemoveAll(tempRoot)

	for _, file := range reader.File {
		normalized := filepath.Clean(file.Name)
		if normalized == "." || normalized == "" {
			continue
		}
		if strings.HasPrefix(normalized, "..") || filepath.IsAbs(normalized) {
			return "", fmt.Errorf("invalid zip entry %q", file.Name)
		}
		targetPath := filepath.Join(tempRoot, normalized)
		if file.FileInfo().IsDir() {
			if err := os.MkdirAll(targetPath, 0755); err != nil {
				return "", err
			}
			continue
		}
		if err := os.MkdirAll(filepath.Dir(targetPath), 0755); err != nil {
			return "", err
		}
		src, err := file.Open()
		if err != nil {
			return "", err
		}
		dst, err := os.Create(targetPath)
		if err != nil {
			_ = src.Close()
			return "", err
		}
		if _, err := io.Copy(dst, src); err != nil {
			_ = dst.Close()
			_ = src.Close()
			return "", err
		}
		_ = dst.Close()
		_ = src.Close()
	}

	skillRoot, err := detectSkillRoot(tempRoot)
	if err != nil {
		return "", err
	}
	targetFolder := folder
	if targetFolder == "" {
		targetFolder = sanitizeFolderName(filepath.Base(skillRoot))
	}
	if targetFolder == "" || targetFolder == "." {
		targetFolder = sanitizeFolderName(strings.TrimSuffix(filepath.Base(fileName), filepath.Ext(fileName)))
	}
	if targetFolder == "" {
		return "", errors.New("unable to determine imported skill folder")
	}
	targetDir := filepath.Join(s.ManagedDir, targetFolder)
	if err := os.RemoveAll(targetDir); err != nil {
		return "", err
	}
	if err := copyDir(skillRoot, targetDir); err != nil {
		return "", err
	}
	if _, err := os.Stat(filepath.Join(targetDir, "SKILL.md")); err != nil {
		return "", errors.New("imported package missing SKILL.md")
	}
	if err := writeManagedMeta(targetDir, "uploaded", targetFolder); err != nil {
		return "", err
	}
	return targetDir, nil
}

func (s Service) scanDir(root string, source string) ([]Entry, error) {
	if root == "" {
		return []Entry{}, nil
	}
	if _, err := os.Stat(root); err != nil {
		if os.IsNotExist(err) {
			return []Entry{}, nil
		}
		return nil, err
	}
	entries, err := os.ReadDir(root)
	if err != nil {
		return nil, err
	}

	result := []Entry{}
	for _, entry := range entries {
		if !entry.IsDir() {
			continue
		}
		skillDir := filepath.Join(root, entry.Name())
		skillFile := filepath.Join(skillDir, "SKILL.md")
		data, err := os.ReadFile(skillFile)
		if err != nil {
			continue
		}
		content := string(data)
		frontmatter, body := parseFrontmatter(content)
		result = append(result, Entry{
			ID:             entry.Name(),
			Folder:         entry.Name(),
			Name:           stringOr(frontmatter["name"], entry.Name()),
			Description:    stringOr(frontmatter["description"], ""),
			Emoji:          stringOr(frontmatter["emoji"], ""),
			Tags:           stringSliceOr(frontmatter["tags"]),
			Category:       stringOr(frontmatter["category"], defaultCategory(source)),
			Source:         source,
			Version:        stringOr(frontmatter["version"], "v1"),
			BaseDir:        skillDir,
			FilePath:       skillFile,
			Content:        content,
			RuntimeContent: body,
			Frontmatter:    frontmatter,
		})
	}
	return result, nil
}

func parseFrontmatter(content string) (map[string]interface{}, string) {
	trimmed := strings.TrimSpace(content)
	if !strings.HasPrefix(trimmed, "---") {
		return map[string]interface{}{}, content
	}
	parts := strings.SplitN(trimmed, "---", 3)
	if len(parts) < 3 {
		return map[string]interface{}{}, content
	}
	meta := map[string]interface{}{}
	if err := yaml.Unmarshal([]byte(parts[1]), &meta); err != nil {
		return map[string]interface{}{}, content
	}
	return meta, strings.TrimSpace(parts[2])
}

func copyDir(src string, dst string) error {
	if err := os.MkdirAll(dst, 0755); err != nil {
		return err
	}
	entries, err := os.ReadDir(src)
	if err != nil {
		return err
	}
	for _, entry := range entries {
		srcPath := filepath.Join(src, entry.Name())
		dstPath := filepath.Join(dst, entry.Name())
		if entry.IsDir() {
			if err := copyDir(srcPath, dstPath); err != nil {
				return err
			}
			continue
		}
		data, err := os.ReadFile(srcPath)
		if err != nil {
			return err
		}
		info, err := os.Stat(srcPath)
		if err != nil {
			return err
		}
		mode := info.Mode().Perm()
		if mode == 0 {
			mode = 0644
		}
		if err := os.WriteFile(dstPath, data, mode); err != nil {
			return err
		}
	}
	return nil
}

func detectSkillRoot(root string) (string, error) {
	if _, err := os.Stat(filepath.Join(root, "SKILL.md")); err == nil {
		return root, nil
	}
	matches := []string{}
	err := filepath.WalkDir(root, func(path string, entry os.DirEntry, walkErr error) error {
		if walkErr != nil {
			return walkErr
		}
		if entry.IsDir() {
			return nil
		}
		if entry.Name() != "SKILL.md" {
			return nil
		}
		matches = append(matches, filepath.Dir(path))
		return nil
	})
	if err != nil {
		return "", err
	}
	if len(matches) == 0 {
		return "", errors.New("uploaded package does not contain SKILL.md")
	}
	sort.Strings(matches)
	if len(matches) == 1 {
		return matches[0], nil
	}
	first := matches[0]
	for _, match := range matches[1:] {
		if match != first {
			return "", errors.New("uploaded package contains multiple SKILL.md files; specify a single skill package")
		}
	}
	return first, nil
}

func writeManagedMeta(targetDir string, source string, itemID string) error {
	meta := map[string]string{
		"source": source,
		"itemId": itemID,
	}
	payload, _ := json.MarshalIndent(meta, "", "  ")
	return os.WriteFile(filepath.Join(targetDir, ".opendataagent-meta.json"), payload, 0644)
}

func defaultCategory(source string) string {
	if source == "managed" {
		return "本地"
	}
	return "Bundled"
}

func stringOr(value interface{}, fallback string) string {
	text, ok := value.(string)
	if !ok || strings.TrimSpace(text) == "" {
		return fallback
	}
	return strings.TrimSpace(text)
}

func stringSliceOr(value interface{}) []string {
	switch typed := value.(type) {
	case []string:
		return append([]string(nil), typed...)
	case []interface{}:
		items := make([]string, 0, len(typed))
		for _, item := range typed {
			if text := stringOr(item, ""); text != "" {
				items = append(items, text)
			}
		}
		return items
	case string:
		text := strings.TrimSpace(typed)
		if text == "" {
			return nil
		}
		return []string{text}
	default:
		return nil
	}
}

func cloneMap(input map[string]interface{}) map[string]interface{} {
	if len(input) == 0 {
		return nil
	}
	output := make(map[string]interface{}, len(input))
	for key, value := range input {
		output[key] = value
	}
	return output
}

func sanitizeFolderName(value string) string {
	value = strings.TrimSpace(strings.ToLower(value))
	if value == "" {
		return ""
	}
	var builder strings.Builder
	lastDash := false
	for _, r := range value {
		switch {
		case (r >= 'a' && r <= 'z') || (r >= '0' && r <= '9'):
			builder.WriteRune(r)
			lastDash = false
		case r == '-' || r == '_' || r == ' ' || r == '.':
			if !lastDash && builder.Len() > 0 {
				builder.WriteByte('-')
				lastDash = true
			}
		}
	}
	out := strings.Trim(builder.String(), "-")
	if out == "" {
		return ""
	}
	return out
}
