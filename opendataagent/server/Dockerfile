FROM golang:1.24 AS builder

WORKDIR /src

COPY go.mod go.sum ./
RUN go mod download

COPY . .

ARG TARGETOS=linux
ARG TARGETARCH=amd64
RUN CGO_ENABLED=0 GOOS=${TARGETOS} GOARCH=${TARGETARCH} go build -o /out/opendataagent ./cmd/opendataagent

FROM debian:bookworm-slim

RUN apt-get update \
  && apt-get install -y --no-install-recommends ca-certificates tzdata curl \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /out/opendataagent /app/opendataagent
COPY skills /app/skills
COPY migrations /app/migrations

ENV ODA_ADDR=:18900
ENV ODA_STATE_DIR=/var/lib/opendataagent
ENV ODA_MANAGED_SKILLS_DIR=/var/lib/opendataagent/skills/managed
ENV ODA_BUNDLED_SKILLS_DIR=/app/skills/bundled

RUN mkdir -p /var/lib/opendataagent/skills/managed

EXPOSE 18900

ENTRYPOINT ["/app/opendataagent"]
