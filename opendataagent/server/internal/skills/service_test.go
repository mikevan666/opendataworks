package skills

import (
	"archive/zip"
	"bytes"
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestBuildDocumentsPreservesFrontmatter(t *testing.T) {
	root := t.TempDir()
	bundled := filepath.Join(root, "bundled")
	managed := filepath.Join(root, "managed")
	skillDir := filepath.Join(bundled, "smoke")
	if err := os.MkdirAll(skillDir, 0755); err != nil {
		t.Fatal(err)
	}
	content := `---
name: Smoke Skill
description: Smoke description
tags:
  - smoke
  - demo
version: v2
---
# Smoke

Please reply smoke-ok.
`
	if err := os.WriteFile(filepath.Join(skillDir, "SKILL.md"), []byte(content), 0644); err != nil {
		t.Fatal(err)
	}

	svc := Service{BundledDir: bundled, ManagedDir: managed}
	docs, err := svc.BuildDocuments()
	if err != nil {
		t.Fatal(err)
	}
	if len(docs) != 1 {
		t.Fatalf("expected 1 document, got %d", len(docs))
	}
	if !strings.Contains(docs[0].CurrentContent, "name: Smoke Skill") {
		t.Fatalf("expected frontmatter to be preserved in current content, got %q", docs[0].CurrentContent)
	}
	if docs[0].Metadata["name"] != "Smoke Skill" {
		t.Fatalf("expected metadata name to be parsed, got %#v", docs[0].Metadata["name"])
	}

	entries, err := svc.ScanRuntimeEntries()
	if err != nil {
		t.Fatal(err)
	}
	if len(entries) != 1 {
		t.Fatalf("expected 1 runtime entry, got %d", len(entries))
	}
	if strings.Contains(entries[0].RuntimeContent, "name: Smoke Skill") {
		t.Fatalf("expected runtime content to exclude frontmatter, got %q", entries[0].RuntimeContent)
	}
	if !strings.Contains(entries[0].RuntimeContent, "Please reply smoke-ok.") {
		t.Fatalf("expected runtime content body to remain, got %q", entries[0].RuntimeContent)
	}
	if len(entries[0].Tags) != 2 || entries[0].Tags[0] != "smoke" {
		t.Fatalf("expected tags to be parsed, got %#v", entries[0].Tags)
	}
}

func TestDeleteManagedSkillRemovesDirectory(t *testing.T) {
	root := t.TempDir()
	managed := filepath.Join(root, "managed")
	skillDir := filepath.Join(managed, "smoke")
	if err := os.MkdirAll(skillDir, 0755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(skillDir, "SKILL.md"), []byte("# Smoke"), 0644); err != nil {
		t.Fatal(err)
	}

	svc := Service{ManagedDir: managed}
	if err := svc.DeleteManagedSkill("smoke"); err != nil {
		t.Fatal(err)
	}
	if _, err := os.Stat(skillDir); !os.IsNotExist(err) {
		t.Fatalf("expected managed skill dir to be deleted, got err=%v", err)
	}
}

func TestImportSkillPackageFromMarkdown(t *testing.T) {
	root := t.TempDir()
	managed := filepath.Join(root, "managed")
	svc := Service{ManagedDir: managed}

	targetDir, err := svc.ImportSkillPackage("weather-skill.md", []byte("# Weather\n\nReply with forecast."), "")
	if err != nil {
		t.Fatal(err)
	}
	if filepath.Base(targetDir) != "weather-skill" {
		t.Fatalf("expected derived folder weather-skill, got %s", filepath.Base(targetDir))
	}
	content, err := os.ReadFile(filepath.Join(targetDir, "SKILL.md"))
	if err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(string(content), "Reply with forecast.") {
		t.Fatalf("expected imported markdown content, got %q", string(content))
	}
	meta, err := os.ReadFile(filepath.Join(targetDir, ".opendataagent-meta.json"))
	if err != nil {
		t.Fatal(err)
	}
	payload := map[string]string{}
	if err := json.Unmarshal(meta, &payload); err != nil {
		t.Fatal(err)
	}
	if payload["source"] != "uploaded" || payload["itemId"] != "weather-skill" {
		t.Fatalf("unexpected meta payload: %#v", payload)
	}
}

func TestImportSkillPackageFromZip(t *testing.T) {
	root := t.TempDir()
	managed := filepath.Join(root, "managed")
	svc := Service{ManagedDir: managed}

	zipPayload := bytes.NewBuffer(nil)
	zw := zip.NewWriter(zipPayload)
	skillFile, err := zw.Create("bundle/hello-world/SKILL.md")
	if err != nil {
		t.Fatal(err)
	}
	if _, err := skillFile.Write([]byte("---\nname: Hello World\n---\n# Hello\n\nSay hi.\n")); err != nil {
		t.Fatal(err)
	}
	if err := zw.Close(); err != nil {
		t.Fatal(err)
	}

	targetDir, err := svc.ImportSkillPackage("hello-world.zip", zipPayload.Bytes(), "")
	if err != nil {
		t.Fatal(err)
	}
	if filepath.Base(targetDir) != "hello-world" {
		t.Fatalf("expected folder hello-world, got %s", filepath.Base(targetDir))
	}
	content, err := os.ReadFile(filepath.Join(targetDir, "SKILL.md"))
	if err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(string(content), "name: Hello World") {
		t.Fatalf("expected zip content to be extracted, got %q", string(content))
	}
}
