# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

Create a Legal AI Tool akin to the functionality of Claude Cowork (but perhaps more minimal to start) - seamless search and ability to retieve and leverage information to support analysis, perform research, and help generate legal documents from across exact structured client database + unstructured case data from briefings, transcriptions, agreements, emails, court proceedings and records in desktop app with data residency priority and some mechanism for PII concern management on the prompt injection and optional redaction on retrieval based on user access level. Generally, user auth applicable to accessible unstructured and structured data as well.

## Tech Stack

Desktop application with chat assistant and privileged data/file explorer built in Rust capable of verifiable fact, quantitative detail, qualitative detail retrieval in addition to conceptual assistant, research capability, legal analysis, and template-based legal document generation.

Multi-agent system built in [AutoAgents](https://github.com/liquidos-ai/AutoAgents)
OR multi-agent python backend with FastAPI, Langchain, and Langsmith which talks to Rust application layer (TBD).
MongoDB for checkpoints storage.

DuckDuckGo for web-search tooling to augment document and structured-data based research/AutoGPT/LangGraph.

RAG system as context engine in multi-agent which uses Pinecone as its vector db:
LlamaParse for complex PDFs for Parsing and Chunking
Document Loaders - LlamaIndex/Langchain DAGs (TBD) ANd for orchestration/re-indexing
use SHA-256 for dedup and r-embedding determination
Embedding models - Cohere/OpenAI Embed or `all-MiniLM-L6-v2` from HuggingFace
re-indexing triggers with Apache Airflow
Re-ranking + QA: bge-reranker

Langsmith for Observability

Separate Node REST API backend (Typscript, strict mode enforced) which talks to Postgres and manages client accounts, client profiles, case history, and account statuses for billing, etc.

MCP server layer on top of REST API backend.

LLMGateway abstraction wrapping Claude API akin to Amazon Bedrock. Can manage input sanitization and flag potetnial prompt injection risks.

## Key Commands

- test
- lint
- build
