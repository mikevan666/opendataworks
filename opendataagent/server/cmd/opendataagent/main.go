package main

import (
	"log"
	"net/http"

	"opendataagent/server/internal/app"
	"opendataagent/server/internal/config"
	"opendataagent/server/internal/httpapi"
)

func main() {
	cfg := config.Load()
	core, err := app.New(cfg)
	if err != nil {
		log.Fatalf("create app: %v", err)
	}
	log.Printf("opendataagent server listening on %s", cfg.Addr)
	if err := http.ListenAndServe(cfg.Addr, httpapi.NewServer(core)); err != nil {
		log.Fatalf("listen: %v", err)
	}
}
