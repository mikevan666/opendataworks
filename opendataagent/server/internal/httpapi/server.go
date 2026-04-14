package httpapi

import (
	"crypto/subtle"
	"encoding/json"
	"io"
	"net/http"
	"strconv"
	"strings"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/cors"

	"opendataagent/server/internal/app"
	"opendataagent/server/internal/models"
)

func NewServer(core *app.App) http.Handler {
	router := chi.NewRouter()
	router.Use(cors.Handler(cors.Options{
		AllowedOrigins: []string{"*"},
		AllowedMethods: []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"},
		AllowedHeaders: []string{"Accept", "Authorization", "Content-Type"},
	}))
	router.Use(adminAuthMiddleware(core))

	router.Get("/api/v1/agent/health", func(w http.ResponseWriter, r *http.Request) {
		writeJSON(w, http.StatusOK, map[string]interface{}{"ok": true})
	})

	router.Get("/api/v1/settings/agent", func(w http.ResponseWriter, r *http.Request) {
		writeJSON(w, http.StatusOK, core.GetSettings())
	})
	router.Put("/api/v1/settings/agent", func(w http.ResponseWriter, r *http.Request) {
		var payload models.AgentSettings
		if err := json.NewDecoder(r.Body).Decode(&payload); err != nil {
			writeError(w, http.StatusBadRequest, err)
			return
		}
		settings, err := core.UpdateSettings(payload)
		if err != nil {
			writeError(w, http.StatusInternalServerError, err)
			return
		}
		writeJSON(w, http.StatusOK, settings)
	})

	router.Get("/api/v1/agent/topics", func(w http.ResponseWriter, r *http.Request) {
		writeJSON(w, http.StatusOK, core.ListTopics())
	})
	router.Post("/api/v1/agent/topics", func(w http.ResponseWriter, r *http.Request) {
		payload := struct {
			Title string `json:"title"`
		}{}
		_ = json.NewDecoder(r.Body).Decode(&payload)
		topic, err := core.CreateTopic(payload.Title)
		if err != nil {
			writeError(w, http.StatusInternalServerError, err)
			return
		}
		writeJSON(w, http.StatusOK, topic)
	})
	router.Get("/api/v1/agent/topics/{topicID}", func(w http.ResponseWriter, r *http.Request) {
		topic, err := core.GetTopic(chi.URLParam(r, "topicID"))
		if err != nil {
			writeError(w, http.StatusNotFound, err)
			return
		}
		writeJSON(w, http.StatusOK, topic)
	})
	router.Put("/api/v1/agent/topics/{topicID}", func(w http.ResponseWriter, r *http.Request) {
		var payload models.UpdateTopicRequest
		if err := json.NewDecoder(r.Body).Decode(&payload); err != nil {
			writeError(w, http.StatusBadRequest, err)
			return
		}
		topic, err := core.UpdateTopic(chi.URLParam(r, "topicID"), payload)
		if err != nil {
			writeError(w, http.StatusNotFound, err)
			return
		}
		writeJSON(w, http.StatusOK, topic)
	})
	router.Delete("/api/v1/agent/topics/{topicID}", func(w http.ResponseWriter, r *http.Request) {
		if err := core.DeleteTopic(chi.URLParam(r, "topicID")); err != nil {
			writeError(w, http.StatusNotFound, err)
			return
		}
		writeJSON(w, http.StatusOK, map[string]interface{}{"ok": true})
	})
	router.Get("/api/v1/agent/topics/{topicID}/messages", func(w http.ResponseWriter, r *http.Request) {
		items, err := core.ListTopicMessages(chi.URLParam(r, "topicID"))
		if err != nil {
			writeError(w, http.StatusNotFound, err)
			return
		}
		writeJSON(w, http.StatusOK, map[string]interface{}{"items": items, "total": len(items)})
	})

	router.Post("/api/v1/agent/tasks/deliver-message", func(w http.ResponseWriter, r *http.Request) {
		var payload models.DeliverMessageRequest
		if err := json.NewDecoder(r.Body).Decode(&payload); err != nil {
			writeError(w, http.StatusBadRequest, err)
			return
		}
		result, err := core.DeliverMessage(payload)
		if err != nil {
			writeError(w, http.StatusBadRequest, err)
			return
		}
		writeJSON(w, http.StatusOK, result)
	})
	router.Get("/api/v1/agent/tasks/{taskID}", func(w http.ResponseWriter, r *http.Request) {
		task, err := core.GetTask(chi.URLParam(r, "taskID"))
		if err != nil {
			writeError(w, http.StatusNotFound, err)
			return
		}
		writeJSON(w, http.StatusOK, task)
	})
	router.Get("/api/v1/agent/tasks/{taskID}/events", func(w http.ResponseWriter, r *http.Request) {
		afterSeq, _ := strconv.ParseInt(r.URL.Query().Get("after_seq"), 10, 64)
		items, err := core.ListTaskEvents(chi.URLParam(r, "taskID"), afterSeq)
		if err != nil {
			writeError(w, http.StatusNotFound, err)
			return
		}
		writeJSON(w, http.StatusOK, map[string]interface{}{"items": items, "total": len(items)})
	})
	router.Get("/api/v1/agent/tasks/{taskID}/events/stream", func(w http.ResponseWriter, r *http.Request) {
		taskID := chi.URLParam(r, "taskID")
		afterSeq, _ := strconv.ParseInt(r.URL.Query().Get("after_seq"), 10, 64)
		items, err := core.ListTaskEvents(taskID, afterSeq)
		if err != nil {
			writeError(w, http.StatusNotFound, err)
			return
		}
		w.Header().Set("Content-Type", "text/event-stream")
		w.Header().Set("Cache-Control", "no-cache")
		w.Header().Set("Connection", "keep-alive")
		flusher, ok := w.(http.Flusher)
		if !ok {
			writeError(w, http.StatusInternalServerError, err)
			return
		}
		for _, item := range items {
			writeSSE(w, item)
			flusher.Flush()
		}
		ch, unsubscribe := core.Subscribe(taskID)
		defer unsubscribe()
		for {
			select {
			case <-r.Context().Done():
				return
			case event := <-ch:
				writeSSE(w, event)
				flusher.Flush()
			}
		}
	})
	router.Post("/api/v1/agent/tasks/{taskID}/cancel", func(w http.ResponseWriter, r *http.Request) {
		if err := core.CancelTask(chi.URLParam(r, "taskID")); err != nil {
			writeError(w, http.StatusNotFound, err)
			return
		}
		writeJSON(w, http.StatusOK, map[string]interface{}{"ok": true})
	})

	router.Get("/api/v1/skills/documents", func(w http.ResponseWriter, r *http.Request) {
		writeJSON(w, http.StatusOK, core.ListSkillDocuments())
	})
	router.Get("/api/v1/skills/documents/{documentID}", func(w http.ResponseWriter, r *http.Request) {
		doc, err := core.GetSkillDocument(chi.URLParam(r, "documentID"))
		if err != nil {
			writeError(w, http.StatusNotFound, err)
			return
		}
		writeJSON(w, http.StatusOK, doc)
	})
	router.Put("/api/v1/skills/documents/{documentID}", func(w http.ResponseWriter, r *http.Request) {
		var payload models.UpdateSkillDocumentRequest
		if err := json.NewDecoder(r.Body).Decode(&payload); err != nil {
			writeError(w, http.StatusBadRequest, err)
			return
		}
		doc, err := core.UpdateSkillDocument(chi.URLParam(r, "documentID"), payload)
		if err != nil {
			writeError(w, http.StatusBadRequest, err)
			return
		}
		writeJSON(w, http.StatusOK, doc)
	})
	router.Delete("/api/v1/skills/documents/{documentID}", func(w http.ResponseWriter, r *http.Request) {
		if err := core.DeleteSkillDocument(chi.URLParam(r, "documentID")); err != nil {
			writeError(w, http.StatusBadRequest, err)
			return
		}
		writeJSON(w, http.StatusOK, map[string]interface{}{"ok": true})
	})
	router.Post("/api/v1/skills/documents/{documentID}/compare", func(w http.ResponseWriter, r *http.Request) {
		var payload models.CompareSkillDocumentRequest
		_ = json.NewDecoder(r.Body).Decode(&payload)
		result, err := core.CompareSkillDocument(chi.URLParam(r, "documentID"), payload)
		if err != nil {
			writeError(w, http.StatusBadRequest, err)
			return
		}
		writeJSON(w, http.StatusOK, result)
	})
	router.Post("/api/v1/skills/documents/{documentID}/versions/{versionID}/rollback", func(w http.ResponseWriter, r *http.Request) {
		doc, err := core.RollbackSkillDocument(chi.URLParam(r, "documentID"), chi.URLParam(r, "versionID"))
		if err != nil {
			writeError(w, http.StatusBadRequest, err)
			return
		}
		writeJSON(w, http.StatusOK, doc)
	})
	router.Post("/api/v1/skills/runtime/sync", func(w http.ResponseWriter, r *http.Request) {
		if err := core.SyncSkills(); err != nil {
			writeError(w, http.StatusInternalServerError, err)
			return
		}
		writeJSON(w, http.StatusOK, models.SkillSyncResult{DocumentCount: len(core.ListSkillDocuments())})
	})
	router.Put("/api/v1/skills/runtime/{skillID}", func(w http.ResponseWriter, r *http.Request) {
		payload := struct {
			Enabled bool `json:"enabled"`
		}{}
		if err := json.NewDecoder(r.Body).Decode(&payload); err != nil {
			writeError(w, http.StatusBadRequest, err)
			return
		}
		result, err := core.UpdateSkillRuntime(chi.URLParam(r, "skillID"), payload.Enabled)
		if err != nil {
			writeError(w, http.StatusBadRequest, err)
			return
		}
		writeJSON(w, http.StatusOK, result)
	})

	router.Get("/api/v1/skill-market/items", func(w http.ResponseWriter, r *http.Request) {
		items, err := core.ListMarketItems()
		if err != nil {
			writeError(w, http.StatusInternalServerError, err)
			return
		}
		items = filterMarketItems(items, r.URL.Query().Get("q"), r.URL.Query().Get("source"))
		writeJSON(w, http.StatusOK, items)
	})
	router.Get("/api/v1/skill-market/items/{itemID}", func(w http.ResponseWriter, r *http.Request) {
		item, err := core.GetMarketItem(chi.URLParam(r, "itemID"))
		if err != nil {
			writeError(w, http.StatusNotFound, err)
			return
		}
		writeJSON(w, http.StatusOK, item)
	})
	router.Post("/api/v1/skill-market/install", func(w http.ResponseWriter, r *http.Request) {
		payload := struct {
			ItemID string `json:"item_id"`
		}{}
		if err := json.NewDecoder(r.Body).Decode(&payload); err != nil {
			writeError(w, http.StatusBadRequest, err)
			return
		}
		item, err := core.InstallMarketItem(payload.ItemID)
		if err != nil {
			writeError(w, http.StatusBadRequest, err)
			return
		}
		writeJSON(w, http.StatusOK, item)
	})
	router.Post("/api/v1/skill-market/import", func(w http.ResponseWriter, r *http.Request) {
		if err := r.ParseMultipartForm(32 << 20); err != nil {
			writeError(w, http.StatusBadRequest, err)
			return
		}
		file, header, err := r.FormFile("file")
		if err != nil {
			writeError(w, http.StatusBadRequest, err)
			return
		}
		defer file.Close()
		payload, err := io.ReadAll(file)
		if err != nil {
			writeError(w, http.StatusBadRequest, err)
			return
		}
		item, err := core.ImportMarketPackage(header.Filename, payload, r.FormValue("folder"))
		if err != nil {
			writeError(w, http.StatusBadRequest, err)
			return
		}
		writeJSON(w, http.StatusOK, item)
	})

	router.Get("/api/v1/mcps/servers", func(w http.ResponseWriter, r *http.Request) {
		writeJSON(w, http.StatusOK, core.ListMCPServers())
	})
	router.Post("/api/v1/mcps/servers", func(w http.ResponseWriter, r *http.Request) {
		var payload models.MCPServer
		if err := json.NewDecoder(r.Body).Decode(&payload); err != nil {
			writeError(w, http.StatusBadRequest, err)
			return
		}
		item, err := core.CreateMCPServer(payload)
		if err != nil {
			writeError(w, http.StatusBadRequest, err)
			return
		}
		writeJSON(w, http.StatusOK, item)
	})
	router.Put("/api/v1/mcps/servers/{serverID}", func(w http.ResponseWriter, r *http.Request) {
		var payload models.MCPServer
		if err := json.NewDecoder(r.Body).Decode(&payload); err != nil {
			writeError(w, http.StatusBadRequest, err)
			return
		}
		item, err := core.UpdateMCPServer(chi.URLParam(r, "serverID"), payload)
		if err != nil {
			writeError(w, http.StatusBadRequest, err)
			return
		}
		writeJSON(w, http.StatusOK, item)
	})
	router.Delete("/api/v1/mcps/servers/{serverID}", func(w http.ResponseWriter, r *http.Request) {
		if err := core.DeleteMCPServer(chi.URLParam(r, "serverID")); err != nil {
			writeError(w, http.StatusBadRequest, err)
			return
		}
		writeJSON(w, http.StatusOK, map[string]interface{}{"ok": true})
	})
	router.Post("/api/v1/mcps/servers/{serverID}/test", func(w http.ResponseWriter, r *http.Request) {
		result, err := core.TestMCPServer(chi.URLParam(r, "serverID"))
		if err != nil {
			writeError(w, http.StatusBadRequest, err)
			return
		}
		writeJSON(w, http.StatusOK, result)
	})

	return router
}

func writeJSON(w http.ResponseWriter, status int, payload interface{}) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(payload)
}

func writeError(w http.ResponseWriter, status int, err error) {
	writeJSON(w, status, map[string]interface{}{"detail": err.Error()})
}

func writeSSE(w http.ResponseWriter, payload interface{}) {
	data, _ := json.Marshal(payload)
	_, _ = w.Write([]byte("event: message\n"))
	_, _ = w.Write([]byte("data: "))
	_, _ = w.Write(data)
	_, _ = w.Write([]byte("\n\n"))
}

func adminAuthMiddleware(core *app.App) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			if r.Method == http.MethodOptions || r.URL.Path == "/api/v1/agent/health" {
				next.ServeHTTP(w, r)
				return
			}
			token := strings.TrimSpace(core.AdminToken())
			if token == "" {
				next.ServeHTTP(w, r)
				return
			}
			candidate := parseAuthToken(r)
			if subtle.ConstantTimeCompare([]byte(candidate), []byte(token)) != 1 {
				writeJSON(w, http.StatusUnauthorized, map[string]interface{}{"detail": "admin token required"})
				return
			}
			next.ServeHTTP(w, r)
		})
	}
}

func parseAuthToken(r *http.Request) string {
	header := strings.TrimSpace(r.Header.Get("Authorization"))
	if header != "" {
		parts := strings.SplitN(header, " ", 2)
		if len(parts) == 2 && strings.EqualFold(parts[0], "Bearer") {
			return strings.TrimSpace(parts[1])
		}
		return header
	}
	return strings.TrimSpace(r.Header.Get("X-Admin-Token"))
}

func filterMarketItems(items []models.SkillMarketItem, query string, source string) []models.SkillMarketItem {
	query = strings.ToLower(strings.TrimSpace(query))
	source = strings.ToLower(strings.TrimSpace(source))
	if query == "" && source == "" {
		return items
	}
	filtered := make([]models.SkillMarketItem, 0, len(items))
	for _, item := range items {
		if source != "" && strings.ToLower(item.Source) != source {
			continue
		}
		if query != "" {
			haystack := []string{item.Folder, item.Name, item.Description}
			haystack = append(haystack, item.Tags...)
			if !strings.Contains(strings.ToLower(strings.Join(haystack, " ")), query) {
				continue
			}
		}
		filtered = append(filtered, item)
	}
	return filtered
}
