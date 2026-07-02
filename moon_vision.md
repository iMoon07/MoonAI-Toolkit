# MoonAI — Vision Document v3.0

> Principal Architects: Claude Sonnet 4.6 + ChatGPT
> Owner: Raja
> Last updated: 2026-07-01
> Status: Living document — challenge before implementing.

---

## Core Identity

Moon adalah:

> Junior engineer yang tinggal di komputer Raja. Dia punya indera, otak, tangan, ingatan, akses ke dunia luar, dan kemampuan menentukan kapan harus bertindak dan kapan harus berhenti. Dia tidak tahu segalanya sejak lahir — tapi dia terus belajar, tumbuh, dan bekerja bersama Raja.

Moon bukan AI universal. Moon bukan chatbot dengan fitur. Moon adalah:

> **AI Engineering Companion yang fokus pada engineering dan cybersecurity, yang aman, modular, dan terus berkembang bersama penggunanya.**

Fokus itu yang bikin Moon bisa jauh lebih powerful daripada chatbot umum.

---

## The One Question

Setiap keputusan teknis harus jawab satu pertanyaan:

> "Does this make Moon a more coherent, safer, and more capable engineering companion for Raja?"

Kalau jawabannya tidak, jangan diimplementasikan.

---

## Moon's Senses + Will

```
👀 Eyes        → Vision, OCR, Screenshot Analysis
👂 Ears        → Voice STT, Microphone, Wakeword
🧠 Brain       → moon_core: Reasoning, Memory, Planning, Reflection
👐 Hands       → Tool Runtime: Terminal, Files, Commands (always interruptible)
🌍 World       → Knowledge Runtime: News, CVE, GitHub, Documentation
❤️ Personality → system.md + Persistent Memory + Learned Facts
💭 Will        → Intent Engine: when to act, when to ask, when to refuse
```

**Will** adalah yang membedakan Moon dari automation script. Moon tahu kapan harus diam, kapan harus bertanya, kapan harus menolak, dan kapan harus meminta izin sebelum bertindak.

---

## Target Architecture

```
                    moon_core (The Brain)
                          │
   ┌──────────────────────┼──────────────────────┐
   │                      │                      │
Conversation           Memory               Planning
   │                      │                      │
Reasoning            World Model           Reflection
   │                      │                      │
Tool Runtime      Knowledge Runtime        Observation
   │                      │                      │
Will / Intent      Provider Registry       Automation
   │                      │                      │
   └──────────────────────┼──────────────────────┘
                          │
                   Interface Layer
         ┌──────────┬─────────┬────────┬──────────┐
         │          │         │        │          │
       CLI      Telegram    Voice   Desktop    Future
```

---

## Core Capabilities (The 8 Pillars)

### 1. Memory (Historical)
Menyimpan percakapan, projects, labs, preferensi, kebiasaan, pekerjaan yang belum selesai.
Memory adalah masa lalu. Memory semakin berharga seiring waktu.

---

### 2. World Model (Ephemeral — bukan Memory)

> Memory ≠ World Model. Ini dua hal yang fundamental berbeda.

World Model adalah snapshot kondisi sekarang. Tidak disimpan ke SQLite history. Di-refresh setiap request atau on-demand.

```python
@dataclass
class WorldState:
    current_project:   str           # dari git atau config
    active_git_branch: str           # git branch
    working_directory: str           # cwd
    docker_status:     List[str]     # containers running
    vpn_connected:     bool          # HTB/lab VPN
    active_lab_ip:     Optional[str] # lab machine IP
    gpu_load_pct:      float         # RTX 3060 usage
    time_of_day:       str           # morning / afternoon / night
```

World Model membuat Moon bisa bilang:
> "Gue lihat HTB VPN lu aktif dan ada container Metasploitable hidup. Mau lanjut enum?"

Bukan karena dia "ingat" — tapi karena dia "lihat" kondisi sekarang.

---

### 3. Will (Intent Engine)

Moon tidak langsung eksekusi goal. Dia evaluasi dulu.

```
User input
    ↓
Intent Classification
    ↓
Risk Assessment
    ↓
Context Check (World Model + Memory)
    ↓
Decision:
  PROCEED          → lanjut
  CLARIFY          → tanya dulu
  REQUEST_APPROVAL → minta izin eksplisit
  REFUSE           → tolak dengan penjelasan
```

Contoh: "Moon, hack server itu."
Moon tidak langsung jalan. Moon berpikir:
```
Goal: unclear (server mana?)
Environment: perlu konfirmasi
Permission: belum ada
Risk: DANGEROUS
Decision: CLARIFY
```

Moon: "Server mana yang dimaksud? Ini lab authorized? Gue butuh konteks sebelum lanjut."

Will bukan Planner. Will adalah *decision gate* sebelum Planner.

---

### 3a. Scoped MoonContext (bukan God Object)

Setiap capability butuh context yang berbeda. Solusi bukan membagikan semua ke semua — tapi scoping.

```python
@dataclass
class MoonContext:           # Full context — hanya di MoonAgent level
    memory: ConversationHistory
    world: WorldState
    knowledge: List[KnowledgeResult]
    reflection: List[Reflection]
    project: ProjectContext
    permissions: PermissionPolicy
    conversation: List[Message]

# Ke bawah, setiap layer dapat slice yang mereka butuhkan:
@dataclass
class PlannerContext:        # Planner hanya butuh ini
    goal: str
    world: WorldState
    project: ProjectContext
    available_tools: List[ToolBase]

@dataclass
class ExecutorContext:       # Executor hanya butuh ini
    plan: ExecutionPlan
    permissions: PermissionPolicy
    interrupt_flag: Event

@dataclass
class ReasoningContext:      # LLM reasoning hanya butuh ini
    conversation: List[Message]
    facts: List[Fact]
    knowledge: List[KnowledgeResult]
```

`MoonAgent` yang pegang full context. Ke bawah, hanya slice. God Object dicegah bukan dengan tidak membuat context — tapi dengan tidak membagikan context penuh ke semua lapisan.

---

### 4. Tool Runtime

Moon bukan tool-nya. Moon REQUEST tool. Executor yang eksekusi.

Full pipeline (The ReAct Loop):
```
MoonAgent (Reasoning)
    ↓
Will (Intent Gate)
    ↓
Planner → updates WorkingPlan (State)
    ↓
PermissionEngine
    ↓
Executor → executes 1 step
    ↓
ToolResult (structured)
    ↓
MoonAgent (Reasoning) → evaluates result and plans next step
```

Penting: **Planning di Moon adalah ReAct Loop, bukan Static Plan.**
Moon tidak membuat plan 10 langkah di awal yang kaku. Moon membuat *Working Plan* (atau Reasoning State) yang dievaluasi dan diubah setiap kali mendapat `ToolResult` baru.

```python
@dataclass
class WorkingPlan:
    goal: str
    current_step: PlannedStep
    completed_steps: List[ToolResult]
    status: str
```

**Interrupt adalah requirement bukan opsional.** Tool Runtime dan Interrupt harus ship bersamaan.

Architecture:
```
moon_core/
  tools/
    base.py          # ToolBase abstract class
    registry.py      # ToolRegistry
    executor.py      # ToolExecutor
    interrupt.py     # InterruptHandler (STOP/CANCEL/ABORT)
    permissions.py   # PermissionEngine
    planner.py       # Produces ExecutionPlan, does NOT execute
    builtins/
      read_file.py   # SAFE
      run_command.py # CONFIRM
      http_get.py    # SAFE (foundation untuk Knowledge Runtime)
```

Structured ToolResult:
```python
@dataclass
class ToolResult:
    success:     bool
    exit_code:   int
    stdout:      str
    stderr:      str
    duration_ms: int
    artifacts:   List[str]   # file paths produced
    summary:     str         # LLM-friendly 1-line summary
    confidence:  float       # 0.0 - 1.0, dari tool sendiri
```

Permission Tiers:
```
SAFE       → langsung, tanpa konfirmasi
             (read_file, list_dir, ping, http_get, whois)

CONFIRM    → Approval Token [lihat bawah]
             (nmap, rustscan, ffuf, docker run, write_file)

DANGEROUS  → Peringatan merah + ketik ulang exact command
             (rm, iptables -F, exploit, privesc tools)

BLOCKED    → Tidak pernah
             (shutdown, format disk, rm -rf /)
```

Approval Token:
```
Moon ingin menjalankan:

  nmap -sV 192.168.56.10

Reason  : Enumerate services di lab Metasploitable
Impact  : Network scan, mungkin detectable
Tier    : CONFIRM

Ketik APPROVE untuk lanjut, atau CANCEL untuk batalkan.
```

Replaceability principle: kalau Raja ganti nmap dengan masscan, hanya `nmap.py` tool file yang berubah. Zero perubahan di executor, planner, atau agent. Semua capability harus replaceable dengan mengganti satu file, bukan setengah repository.

---

### 5. Interrupt System

Wajib ada sejak Level 2. Autonomous tanpa interrupt = berbahaya.

Commands yang selalu diproses:
- `STOP` → pause eksekusi saat ini
- `CANCEL` → batalkan current task
- `ABORT` → terminate semua tool + queue

Implementation: setiap `Executor.run()` harus check interrupt flag sebelum dan selama eksekusi. Tool yang long-running (nmap, ffuf) harus handle SIGTERM gracefully.

---

### 6. Knowledge Runtime

Built ON TOP of Tool Runtime (bukan sebelum). `http_get` builtin adalah pondasi.

```
moon_core/
  knowledge/
    base.py          # ProviderBase abstract class
    registry.py      # ProviderRegistry
    aggregator.py    # Multi-source + confidence scoring
    providers/
      news.py        # RSS feeds
      cybersec.py    # BleepingComputer, The Record
      cve.py         # NVD API
      mitre.py       # ATT&CK
      github.py      # Search + trending
      hackernews.py  # HN top
      arxiv.py       # Research papers
```

Kalau dua sumber bertentangan:
> "Aku menemukan informasi berbeda. Confidence: Medium. Mau aku tampilkan sumber-sumbernya?"

---

### 6a. Event Injection (Bukan Event Bus Microservices)

Moon mendukung masuknya stimulus dari luar (seperti file berubah, jadwal alert), tapi **tanpa over-engineering**.

Bukan pakai Kafka/Redis Stream. Cukup inject `SYSTEM_ALERT` ke pipeline utama MoonAgent.

```
Watcher (detects file change)
   ↓
injects: ChatRequest(intent="SYSTEM_ALERT", message="File X changed")
   ↓
MoonAgent (processes normally)
```
Semua stimulus diproses secara linear oleh satu "otak". Simple dan mudah di-debug.

---

### 7. Confidence as Architecture

Kepercayaan diri Moon harus menjadi bagian dari arsitektur, bukan hanya prompting.

Bukan:
> "The exploit is vulnerable."

Tapi:
> "Berdasarkan hasil enumeration, confidence gue high bahwa target vulnerable ke CVE-XXXX. Tapi gue rekomendasiin verifikasi service version dulu sebelum lanjut."

`ChatResponse` harus punya field ini:
```python
@dataclass
class ChatResponse:
    text:             str
    confidence:       float           # 0.0 - 1.0
    uncertainty_note: Optional[str]   # kalau confidence < 0.7
    sources:          List[str]       # kalau dari Knowledge Runtime
```

Ini terutama penting di cybersecurity — di mana confidence salah bisa bikin Raja eksekusi exploit ke target yang salah.

---

### 8. Reflection

Setelah selesai workflow, Moon menyimpan evaluasi operasional:

```python
@dataclass
class Reflection:
    goal:           str
    success:        bool
    what_worked:    str
    what_failed:    str
    recommendation: str   # untuk workflow serupa di masa depan
    confidence:     float
    timestamp:      datetime
```

Contoh:
```
Goal: Privilege escalation di Metasploitable
Success: No
What failed: Kernel exploit tidak kompatibel dengan kernel version
Recommendation: Jalankan LinPEAS dulu untuk recon sebelum pilih exploit
Confidence: High
```

Reflection bukan self-awareness. Reflection adalah operational learning — Moon belajar workflow yang cocok untuk Raja, bukan sekadar mengingat chat.

---

## Level Roadmap

### Level 1 — Assistant (Sekarang)
Status aktual:
- [x] Chat dengan memory (SQLite, WAL, thread-safe)
- [x] Voice STT + TTS
- [x] Vision OCR
- [x] Unified MoonAgent pipeline
- [x] All 3 frontends menggunakan moon_core
- [ ] `/clear` creates new session
- [ ] `moon doctor` health check
- [ ] **VALIDATION SPRINT — belum dijalankan**

---

### Level 2 — Engineer
**Requires Level 1 validation selesai dulu.**

Priorities dalam urutan ini:
1. Validation Sprint (CLI + Bot + Voice jalan bersamaan, WAL proven)
2. `moon doctor` — health check semua dependencies
3. Tool Runtime + Interrupt (wajib satu paket):
   - `ToolBase`, `ToolRegistry`, `PermissionEngine`, `InterruptHandler`
   - `read_file` builtin (SAFE)
   - `run_command` builtin (CONFIRM) + Approval Token
   - `http_get` builtin (SAFE)
4. World Model (ephemeral, refresh per request)
5. Basic Planner (2-step sequential planning)

---

### Level 3 — Operator
6. Knowledge Runtime (di atas http_get)
7. Advanced Planner + Task Queue
8. Reflection (operational learning)
9. Observation (watch logs, monitor processes)

---

### Level 4 — Companion
10. Background Daemon + Wakeword
11. Moon Curiosity (pagi briefing, proactive alerts)
12. Long-term knowledge graph
13. Deep Reflection across sessions

---

### Level 5 — Embodied
Brain sama. Interface layer yang berubah.

---

## Development Rules

### Rule 1 — Architecture sebelum feature
Abstraction belum ada? Bikin dulu. Jangan hardcode.

### Rule 2 — Capability sebelum UI
Capability belum ada di moon_core? Jangan expose ke interface.

### Rule 3 — Quality sebelum quantity
Satu capability benar > lima capability setengah jalan.

### Rule 4 — Challenge dulu, implement kemudian
Setiap ide: "Level berapa? Fondasi sebelumnya solid?"

### Rule 5 — Jangan God Object, jangan God Context
MoonAgent = pure orchestrator. Setiap layer dapat context slice yang mereka butuhkan saja, bukan full MoonContext.

### Rule 6 — Moon bukan kumpulan fitur
> Every new capability must strengthen one coherent companion, not add another disconnected utility.

### Rule 7 — Moon dioptimasi untuk Raja, bukan publik
> Optimize Raja's workflow. Not public adoption.

### Rule 8 — Interrupt sebelum autonomous
> Tidak boleh ada autonomous execution tanpa interrupt capability.
> Tool Runtime dan Interrupt adalah satu paket. Tidak boleh dipisah.

### Rule 9 — Setiap subsystem harus replaceable
> "If Raja replaces this entire subsystem next year, how many files need to change?"
> Kalau jawabannya lebih dari satu modul: abstraction belum selesai.
> SQLite, LLM, OCR, STT, Provider — semuanya harus bisa diganti tanpa touching seluruh repo.

### Rule 10 — Challenge ideas aggressively
> Raja menggunakan AI sebagai senior engineering mentor, bukan code generator.
> Kalau ada yang melanggar arsitektur: bilang.
> Kalau ada technical debt: bilang.
> Kalau ada yang tidak aman: bilang.
> Jangan optimize untuk menyenangkan owner. Optimize untuk sistem yang masih bisa di-maintain 5 tahun dari sekarang.

---

## GitHub Policy
Private dulu. Moon belum divalidasi. Bangun alat kerja dulu, bukan showcase.

---

## Principal Statement

> Moon is not a chatbot with tools. Moon is an intelligent engineering companion that observes, learns, reasons, acquires knowledge, and acts — with Raja's permission — to help solve engineering and cybersecurity problems. Moon always remains under Raja's control. Moon always remains interruptible.

---

## To ChatGPT

Handoff diterima. Framework-mu solid.

Satu perbedaan posisi gue: Interrupt dan Tool Runtime adalah satu paket — tidak boleh ada salah satu tanpa yang lain. Mobil tanpa rem bukan mobil yang lebih cepat, itu accident waiting to happen.

Sisanya: setuju. Terima kasih untuk Will, Reflection, ToolResult, dan "Raja as learner not outsourcer."

Let's build something worth maintaining.

— Claude
