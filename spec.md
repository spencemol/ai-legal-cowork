# Legal AI Tool — Product Specification (v1)

## 1. Functional Requirements (FRs)

### FR-1: Chat Assistant
- FR-1.1: Provide a conversational chat interface where attorneys, paralegals, and partners can ask natural-language questions about matters, clients, and legal topics.
- FR-1.2: Stream responses in real-time as they are generated.
- FR-1.3: Produce inline citations linking directly to source documents; clicking a citation opens the referenced document in the split-view file viewer, navigated to the relevant chunk/section.
- FR-1.4: Persist all conversations and associate them with specific matters/cases so users can resume and search chat history across sessions.

### FR-2: Search & Retrieval
- FR-2.1: Provide unified search across all ingested unstructured data (PDFs, emails, transcripts, court records) and structured data (client profiles, matter metadata, billing records, opposing parties/counsel).
- FR-2.2: Supplement internal firm data with DuckDuckGo web search results for public legal research.
- FR-2.3: Integrate with paid legal research databases (Westlaw, LexisNexis, or similar) for case law and statute retrieval.
- FR-2.4: Re-rank retrieved results using bge-reranker to surface the most relevant content.
- FR-2.5: Support retrieval of verifiable facts, quantitative details, and qualitative details with source attribution.

### FR-3: Legal Document Generation
- FR-3.1: Support template-based document generation where firm-managed templates are populated from matter context and retrieved data.
- FR-3.2: Support freeform AI-driven document drafting from natural-language prompts.
- FR-3.3: Export generated documents in DOCX, PDF, and Markdown formats.

### FR-4: Research & Analysis
- FR-4.1: Perform multi-step legal research by cross-referencing firm data, web sources, and paid legal databases.
- FR-4.2: Provide legal analysis capabilities that synthesize information across multiple documents and data sources.

### FR-5: Document Ingestion & RAG Pipeline
- FR-5.1: Ingest documents automatically on application startup and user login.
- FR-5.2: Support manual refresh where users specify individual files to process.
- FR-5.3: Support automated syncing against a user-configured local file directory.
- FR-5.4: Parse complex PDFs using LlamaParse for chunking and extraction.
- FR-5.5: Use SHA-256 hashing for deduplication — skip re-embedding for unchanged files.
- FR-5.6: Embed document chunks using Cohere, OpenAI Embed, or `all-MiniLM-L6-v2` (TBD) and store in Pinecone vector database.
- FR-5.7: Support re-indexing triggers via Apache Airflow for corpus maintenance.

### FR-6: Read-Only Document Viewer
- FR-6.1: Display referenced documents in a split-view file viewer pane within the desktop app.
- FR-6.2: Open the viewer only when a user clicks an inline citation link or a search result pointing to a specific document.
- FR-6.3: Navigate directly to the referenced or applicable chunk/section within the document.
- FR-6.4: The viewer is strictly read-only — no editing, uploading, or file management.

### FR-7: Access Control & Authentication
- FR-7.1: Support pluggable authentication — SSO/SAML/OIDC preferred, with username/password fallback configurable per deployment.
- FR-7.2: Enforce matter-level access control — users can only access data for matters they are assigned to.
- FR-7.3: Enforce role-based access control — attorneys, paralegals, and partners have different data visibility rules.
- FR-7.4: Apply access control consistently across both unstructured document retrieval and structured data queries.

### FR-8: PII Management
- FR-8.1: Redact PII from document chunks before sending to the external LLM.
- FR-8.2: Redact PII in retrieved content displayed to users based on their access level.
- FR-8.3: Maintain an audit log tracking who accessed what PII-containing data and when.

### FR-9: Multi-Agent System
- FR-9.1: Implement an orchestrator/router agent that interprets user intent and delegates to specialist agents.
- FR-9.2: Implement a retrieval agent for RAG queries — searches vector DB, re-ranks, and returns relevant chunks.
- FR-9.3: Implement a research agent for multi-step legal research across firm data, web, and legal databases.
- FR-9.4: Implement a drafting agent for legal document generation (template-based and freeform).
- FR-9.5: Store agent checkpoints in MongoDB.
- FR-9.6: Additional agent roles TBD as the system evolves.

### FR-10: Structured Data Management
- FR-10.1: Manage client accounts, client profiles, case/matter history, and account statuses via the Node REST API backend backed by Postgres.
- FR-10.2: Expose structured data through an MCP server layer on top of the REST API.

### FR-11: LLM Gateway
- FR-11.1: Route all LLM calls through a gateway abstraction wrapping the Claude API.
- FR-11.2: Perform input sanitization to flag potential prompt injection risks before they reach the LLM.

### FR-12: Observability
- FR-12.1: Integrate LangSmith for tracing, monitoring, and debugging of agent workflows and LLM interactions.

---

## 2. Non-Functional Requirements (NFRs)

### NFR-1: Performance
- NFR-1.1: Support 200+ concurrent users per firm deployment.
- NFR-1.2: Stream AI responses so users see progressive output immediately regardless of total processing time.
- NFR-1.3: Handle a document corpus of 100K–1M documents per deployment.

### NFR-2: Security
- NFR-2.1: All data at rest and in transit must be encrypted.
- NFR-2.2: PII redaction must occur before any data is sent to external LLM APIs.
- NFR-2.3: Audit logs must capture all PII access events with user identity and timestamp.
- NFR-2.4: Safeguard attorney-client privilege — the system must not inadvertently expose privileged communications across matter boundaries or to unauthorized roles.

### NFR-3: Reliability
- NFR-3.1: The system requires a persistent internet connection (always-online).
- NFR-3.2: Agent checkpoints in MongoDB must ensure workflows can recover from interruptions.

### NFR-4: Maintainability
- NFR-4.1: Node REST API backend must use TypeScript in strict mode.
- NFR-4.2: LLM Gateway abstraction must be modular to allow future swapping of LLM providers.
- NFR-4.3: Authentication mechanism must be pluggable per deployment.

### NFR-5: Observability
- NFR-5.1: All agent interactions and LLM calls must be traceable via LangSmith.
- NFR-5.2: System must provide sufficient logging for debugging retrieval quality and agent routing decisions.

---

## 3. Constraints

- **Desktop only:** The application is a Rust-based desktop app. No web or mobile client for v1.
- **External LLM dependency:** v1 uses the Claude API exclusively. No local model support required.
- **Always-online:** A persistent internet connection is required for all functionality.
- **English only:** All documents, queries, and generated content are in English for v1.
- **Self-hosted per firm:** Each firm deploys their own isolated instance. No shared multi-tenant infrastructure.
- **Tech stack locked:** Rust (desktop), Python + FastAPI/LangChain/LangGraph or AutoAgents (multi-agent backend, TBD), Node/TypeScript strict (REST API), Postgres (structured data), MongoDB (checkpoints), Pinecone (vector DB), LlamaParse (PDF parsing), Apache Airflow (re-indexing), LangSmith (observability).

---

## 4. Out of Scope (v1)

- Mobile application
- Real-time collaboration (multi-user document editing/annotation)
- Automated court e-filing integration
- E-discovery workflows (litigation hold, custodian management, production)
- Billing and payment processing
- Multi-language support
- Mandatory human-in-the-loop review gates
- Offline / air-gapped operation
- Local LLM hosting
- Document version history tracking (dedup only, no version chain)
- File editing or management within the desktop app

---

## 5. Acceptance Criteria

### AC-1: Accurate Retrieval (Critical)
- Given an attorney asks a factual question about a specific matter, the system retrieves the correct source documents and provides an accurate, cited answer.
- All cited sources are clickable and open the correct document at the correct section in the split-view viewer.
- Retrieval respects matter-level and role-based access control — no results from unauthorized matters are returned.

### AC-2: Document Drafting (Critical)
- Given a user requests a legal document from a template, the system generates a complete draft populated with matter-specific data, exportable as DOCX, PDF, or Markdown.
- Given a user requests a freeform legal document via natural-language prompt, the system produces a coherent draft grounded in retrieved firm data.

### AC-3: Legal Research
- Given a research query, the system synthesizes information from firm documents, web search, and paid legal databases, presenting findings with inline citations.

### AC-4: Document Ingestion
- On startup/login, the system detects new or changed files, skips unchanged files (SHA-256 dedup), and processes new documents into the vector store.
- Manual refresh allows users to specify files or sync a directory, with results searchable immediately after processing.

### AC-5: PII Protection
- No PII is sent to the external LLM — redaction occurs before any API call.
- Retrieved content shown to users is redacted according to their access level.
- All PII access events are recorded in the audit log with user identity and timestamp.

### AC-6: Access Control
- Users only see data from matters they are assigned to.
- Role-based visibility rules are enforced — e.g., a paralegal cannot access partner-restricted content.
- Authentication works via SSO/SAML/OIDC or username/password fallback, configurable per deployment.

### AC-7: Performance at Scale
- The system supports 200+ concurrent users with streaming responses.
- Search and retrieval function correctly across a corpus of 100K–1M documents.

### AC-8: Chat Persistence
- Conversations are saved, linked to matters, and fully resumable across sessions.
- Users can search their chat history.

### AC-9: Attorney-Client Privilege
- The system never surfaces privileged communications to users who lack access to the associated matter.
- Cross-matter queries do not leak privileged information across matter boundaries.
