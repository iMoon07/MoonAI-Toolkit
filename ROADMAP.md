# MoonAI Roadmap

This document outlines the future development path for the MoonAI Toolkit.

---

## [Current Baseline] V1.5.1 - Cognitive Stack
- Separated Identity, Reasoning, Conversation, Response, and Style.
- Proper Git version control initialized.

## [Next] V1.6 - Execution Stack MVP
- **Capability Registry**: Typed capability namespace (e.g., `filesystem.read`).
- **Provider System**: Abstract providers handling capabilities.
- **Permission Middleware**: Interceptor enforcing `ALLOW`, `DENY`, or `ASK` policies.
- **Providers**: `FilesystemProvider` and `ShellProvider` implemented.
- **Scheduler**: Simple V1 scheduler routing execution requests.

## V1.7 - Advanced Execution & OS Awareness
- **Workspace Manager**: Repo context and environment awareness.
- **Plugin System**: Dynamic loading of external providers (Docker, Web, Git).
- **Model Context Protocol (MCP)** integration.

## V2.0 - Distributed AI Runtime
- **Multi-Agent Coordinator**: Delegating capabilities to sub-agents.
- **Remote Workers**: Swarm execution across multiple machines via MQTT/sockets.
