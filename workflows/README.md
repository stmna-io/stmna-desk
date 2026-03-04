# STMNA Desk — Workflow Reference

This directory contains the n8n workflows that manage the Obsidian vault and its vector search layer. These are infrastructure workflows, not content pipelines. They provide the API that other workflows (Signal, Voice) call to read, write, and search vault content.

---

## Workflows

| File | Workflow | Nodes | Trigger | Purpose |
|------|----------|-------|---------|---------|
| `vault-ops.json` | Claude.ai Vault Operations | 17 | Webhook (POST) | 12-action API for vault file operations, git management, and semantic search |
| `vault-embedding.json` | Vault_Embedding_Pipeline | 6 | Webhook (Forgejo push) | Chunks new/changed vault files, generates embeddings, stores in PGVector |

---

## Vault Operations (vault-ops.json)

A single webhook endpoint that accepts POST requests with an `action` field. Routes to 12 different operations:

| Action | What It Does |
|--------|-------------|
| `read` | Read a vault file by path |
| `write` | Write content to a vault file (creates or overwrites) |
| `list` | List files in a vault directory |
| `mkdir` | Create a new directory |
| `delete` | Delete a vault file |
| `rename` | Rename or move a vault file |
| `git_commit` | Commit current vault changes with a message |
| `repo_read` | Read a file from a Forgejo repo (not just the vault) |
| `repo_list` | List directory contents in a Forgejo repo |
| `repo_commits` | Get recent commit history for a repo |
| `repo_diff` | Show diff for a specific commit |
| `search` | Semantic search across the vault using PGVector embeddings |

### Search Action

The `search` action embeds your query using TEI, runs a cosine similarity search against the PGVector index, and returns ranked chunks with file paths and relevance scores.

```bash
curl -X POST http://your-n8n:5678/webhook/vault \
  -H "Content-Type: application/json" \
  -d '{"action": "search", "query": "how does the TTS pipeline work", "top_k": 5}'
```

---

## Vault Embedding Pipeline (vault-embedding.json)

Triggered by a Forgejo webhook whenever code is pushed to the vault repository. It:

1. Receives the push webhook from Forgejo
2. Pulls the latest changes (`git pull`)
3. Identifies new or changed markdown files from the commit
4. Chunks each file into paragraphs (target 600 chars, 100 char overlap)
5. Generates embeddings via TEI (pplx-embed-context-v1, 1024 dimensions)
6. Upserts chunks into the `vault_embeddings` table in PostgreSQL with PGVector

Unchanged files are skipped via content hashing. The pipeline processes a typical vault push (5-10 changed files) in under a minute.

---

## Prerequisites

### Services

| Service | Required? | Notes |
|---------|-----------|-------|
| PostgreSQL 15+ with [PGVector](https://github.com/pgvector/pgvector) extension | Yes | Stores vault embeddings, provides vector similarity search |
| [TEI](https://github.com/huggingface/text-embeddings-inference) (text-embeddings-inference) | Yes | Generates embeddings (pplx-embed-context-v1-0.6b, 1024 dims) |
| Forgejo or compatible Git forge | For embedding pipeline | Sends push webhooks to trigger re-embedding |
| Git | Yes | Vault Ops uses git for commit operations, Embedding Pipeline uses git pull |

### Database

The embedding pipeline uses a `vault_embeddings` table in PostgreSQL with PGVector:

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE vault_embeddings (
    id SERIAL PRIMARY KEY,
    file_path TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    heading TEXT,
    content TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    embedding vector(1024),
    tsv tsvector,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(file_path, chunk_index)
);

CREATE INDEX ON vault_embeddings USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);
CREATE INDEX ON vault_embeddings USING gin (tsv);
```

### n8n Requirements

- n8n **1.75+**
- Environment variable: `NODE_FUNCTION_ALLOW_BUILTIN=fs,child_process,path`
- The vault must be mounted as a readable directory inside the n8n container

---

## Import Instructions

1. Import `vault-ops.json` first (the Embedding Pipeline and other workflows depend on it)
2. Import `vault-embedding.json`
3. Reassign the PostgreSQL credential on both workflows
4. Configure the Forgejo webhook to point to the Embedding Pipeline's webhook URL
5. **Activate** both workflows

### Forgejo Webhook Setup

In your vault repository settings on Forgejo:

1. Go to **Settings > Webhooks > Add Webhook > Forgejo**
2. Target URL: `http://your-n8n:5678/webhook/vault-embed` (or your equivalent)
3. HTTP Method: POST
4. Content Type: application/json
5. Events: Push Only
6. Secret: set a webhook secret and configure it in the workflow

---

## Required Credentials

### `Postgres` credential

Point to the database containing the `vault_embeddings` table.

| Workflow | Nodes using this credential |
|----------|-----------------------------|
| Vault Operations | Search PGVector |
| Vault Embedding Pipeline | Execute SQL (upsert embeddings) |

---

## Environment Variables

These workflows use container-internal service names rather than environment variables for most endpoints. The key configuration points:

| Setting | Value | Where |
|---------|-------|-------|
| TEI endpoint | `http://text-embeddings:80` | Code nodes in both workflows |
| Vault mount path | `/vault` | Code nodes in Vault Ops |
| PostgreSQL | Via n8n credential | PostgreSQL nodes |
| Forgejo webhook secret | Your secret | Webhook node in Embedding Pipeline |

---

## Consumers

These workflows serve as infrastructure for other systems:

| Consumer | How It Uses Vault Ops |
|----------|----------------------|
| Signal_Worker | Writes vault notes via `write` + `git_commit` actions |
| Claude.ai (via MCP) | Reads, writes, lists, searches vault content |
| Open WebUI | Uses `search` action via a custom tool for RAG |
| Agent Zero | Uses `search` action via a Python tool |

For the full RAG architecture, benchmarks, and design decisions, see the [vault RAG reference documentation](../docs/architecture-overview.md).
