# AI Coding Tools

Usage strategies, context management, multi-agent orchestration, and human-AI interaction best practices for AI coding tools.

## Articles

| Article | Summary |
|---------|---------|
| [Claude Max Quota Mechanism](claude-max-quota-mechanism.md) | Dual quota mechanism (5h window + 7d weekly limit) deduction logic and optimization directions |
| [AI as GitHub Co-author Status](ai-coauthor-github.md) | Co-authored-by community controversy, legal implications, and tiered strategy recommendations |
| [Skill Language Choice and Distribution](skill-language-distribution.md) | Why SKILL.md must be English for skill distribution - ecosystem and technical reasons |
| [LLM Working Language Strategy](llm-working-language-strategy.md) | Bilingual developer's language choice: English for system content, Chinese for conversation - practical bilingual strategy, token savings overstated, agentic stability is the real reason |
| [Code Explanation for Non-Programmers](code-explanation-for-non-programmers.md) | Four-layer progressive explanation framework and CLAUDE.md task briefing rules |
| [Compact Instructions Best Practices](compact-instructions-best-practices.md) | auto-compact mechanism's lost content and information retention priority template |
| [Multi-Agent Orchestration Landscape](multi-agent-orchestration-landscape.md) | Five orchestration paradigms comparison, real user behavior patterns (role division not simultaneous coding),赛道新约束, 2026-04-11 IDE paradigm explosion (Paseo/super.engineering/Conductor/Emdash) and僵尸识别 (Vibe Kanban/Plandex) |
| [Multica Evaluation](multica-evaluation.md) | Open-source managed agents platform (2026-04-11 repositioning), Runtimes/Agents/Skills three-layer architecture mapping to Anthropic brain/hands/session, 8 days 3.7x stars growth |
| [Slock.ai Evaluation](slock-ai-evaluation.md) | Closed-source IM paradigm tool, MCP protocol bridging, Kimi CLI author personally maintains multi-driver abstraction, Moonshot ecosystem integration naturally deeper |
| [Context Window and Subagent Protection](context-window-subagent-protection.md) | Performance degradation when context exceeds 70%, subagents trade tokens for clean context |
| [Human-AI Feedback Loop](human-ai-feedback-loop.md) | Three-level intervention gradient replacing binary Q&A, reducing per-error cost |
| [Hooks and Deterministic Behavior Control](hooks-deterministic-control.md) | 25 event types, 4 execution types, deterministic alternative when CLAUDE.md unreliable |
| [Personal Context Engineering Practices](context-engineering-practices.md) | Four-layer practice: CLAUDE.md persistent layer, active compact, subagent isolation, session切断 |
| [Claude Code Statusline Tool Ecosystem](claude-code-statusline-landscape.md) | Statusline赛道 competitive landscape, real user pain points and feature feedback, zero dependencies and data reliability as core competition dimensions |
| [Prompt Caching Mechanism and Max Plan Behavior](prompt-caching-mechanism.md) | Prefix matching mechanism, TTL and pricing, Max Plan 1h TTL溯源, exit resume triple barriers |
| [Product Sense and Restraint](product-sense-and-restraint.md) | OpenCode Dax Raud on AI-era product degradation causes, progressive disclosure and wait-for-clarity restraint strategy |
| [Simon Willison: AI Coding Status and Dark Factory](simon-willison-ai-state-of-union.md) | November inflection point, agentic engineering vs vibe coding boundary, Dark Factory模式, lethal triangle security prophecy |
| [AutoAgent: Autonomous Agent Harness Engineering](autoagent-autonomous-harness-engineering.md) | Meta-agent automatically iterates agent harness optimization (prompt + tools + orchestration), AutoML → AutoAgent paradigm shift |
| [Code Harness to Financial Harness](code-harness-to-financial-harness.md) | Rebutting "Coding Agent equals General Agent", proposing capability general ≠ constraint general, using FluxA mandate protocol as financial harness sample |
| [Saymore: Agent Information Layer Product Analysis](saymore-agent-feed-layer.md) | Agent information subscription infrastructure, human-curated infoflow替代 self-built RAG, UGC模式 |
| [China AI Coding Agent Access Without VPN](china-ai-coding-agent-access.md) | API accessibility, harness selection, recommended组合 (OpenCode+Zen free models), relay service empirical risks |
| [Codex App Worktree Handoff](codex-app-worktree-handoff.md) | Handoff's official capability boundary, Local and associated worktree switching rules, permanent worktree适用场景 |
| [Codex Remote Compaction Mechanism](codex-remote-compaction-mechanism.md) | /responses/compact end-to-end training loop, encrypted_content承载的 "latent understanding", structural difference from local text summarization, moat判断 other harness难以复刻 |
| [OpenClaw Harness Stability Reality Check](openclaw-harness-stability.md) | Issue #62095 five bug categories + r/openclaw collective sentiment + positioning vs delivery structural gap; downstream impact on LobsterAI等 wrapper products |
| [Managed Agents Runtime Layer](managed-agents-runtime-layer.md) | Anthropic托管 agent runtime, brain/hands/session three-layer decoupling + six minimal interfaces + credential vault + TTFT p50 -60% / p95 -90% |
| [LLM Overconfidence and Hypothesis Correction](llm-overconfidence-mitigation.md) | Coding agent基于错误假设行动的结构性原因, five failure modes, reliability-ordered mitigation手段 (hooks > structural separation >精练规则 > CoVe > language prompts) |
| [Agent-First Development: OpenAI Zero Handwritten Code Case](agent-first-development-practices.md) | OpenAI 5 months zero handwritten code实战: progressive disclosure (AGENTS.md as directory), agent legibility, mechanized taste execution, entropy garbage collection, application observability接入 agent |
| [OpenAI Hosted Agent Runtime](openai-hosted-agent-runtime.md) | Responses API + shell tool (parallel multiplexing + output truncation) + container context (filesystem + SQLite + egress proxy credential isolation) + agent skills (SKILL.md versioned bundle), convergence comparison with Anthropic Managed Agents |

## Key Concepts

- **Dual Quota Mechanism**: Claude Max Plan's 5h rolling window and 7d weekly limit, controlling message count and equivalent API cost
- **Context Degradation**: When context window usage exceeds 70%, reasoning ability and instruction following全面下降
- **Context Engineering**: Designing workflows around context window utilization, not treating context management as副产品
- **Subagent Isolation**: Using independent context windows to isolate trial-and-error processes, trading total tokens for main context purity
- **Compact Instructions**: Specifying information retention priority during auto-compact, preventing architectural decisions等 key content loss
- **Hooks**: Lifecycle auto-trigger points, 25 event types + 4 execution types, implementing deterministic behavior control
- **Three-Level Intervention Gradient**: Intent declaration, small-step试探, proactive asking continuous spectrum, replacing binary yes/no questioning
- **Four-Layer Progressive Explanation**: Purpose layer, black-box layer, structure layer, detail layer, code explanation framework for zero-background users
- **MCP Protocol Bridging**: Connecting multiple AI coding CLIs via MCP protocol, loosely coupled but fixed token overhead
- **Prompt Caching**: Token reuse mechanism based on prefix hash, cache read only 0.1x price, normal session hit rate 92-99%
- **Handoff**: Codex App's official流程 for moving context and code between Local and associated Worktree at thread level, not arbitrary worktree switcher
- **Permanent Worktree**: Long-term保留的 worktree in Codex App, reused as independent project,适合 multi-thread持续工作
- **Practical Bilingual Strategy**: LLM working language allocation for bilingual developers, English for system-level content (CLAUDE.md, skills, subagents), Chinese preserved for interaction dialogue
- **Language-Intensive vs Language-Light Tasks**: MAPS evidence shows agentic long planning受语言影响大 (max 16% degradation), code and math tasks几乎不受影响
- **Capability General ≠ Constraint General**: Agent capabilities can cross-domain transfer (coding → tool calling), but harness must按领域重建, because each domain's consequence system根本不同
- **Harness as Permission Upgrade Function**: Agent capability upgrade本质上 is permission upgrade (file → browser → wallet), each level harness必须重写
- **Mandate as Sandbox**: Financial agent's constraint sandbox, defining budget/purpose/validity period, agent超出 mandate parts默认不可达
- **Pre-Settlement Verification**: Financial harness must把 verification前移到 settlement前, differentiating from code harness's post-execution verification
- **Remote Compaction**: Codex CLI's server-side path via /responses/compact for OpenAI provider, returning structured window not text summary, user messages原样保留, agent轨迹折叠为 Compaction { encrypted_content }
- **Latent Understanding**: OpenAI's official措辞 for encrypted_content semantics, explicitly stating "opaque and not intended to be human-interpretable",承载 density strictly higher than equivalent text summary
- **Harness Training Loop**: End-to-end training between compactor endpoint and codex model形成的 moat, harder for competitors to复刻 than pure model weights
- **Ceremonialization**: Instructions losing substance in long sessions, model claiming "verified" but actually未执行, meta-cognitive instructions最先衰减
- **Anchor Bias**: Model forming hypotheses in early rounds and not修正 even with contradictory evidence, multi-turn conversation average performance drops 39%
- **Check/Ask/Flag Three-Level Routing**: Checkable claims first check, user-intent-dependent first ask, both impossible flag as unverified; ask优先于 flag
- **Brain/Hands/Session Decoupling**: Managed Agents拆分 agent into three independent components (Claude + harness loop brain / sandbox and tools hands / append-only log session), each layer can independently fail and replace
- **Meta-Harness**: Agent runtime design not对具体 harness做假设, through minimal interfaces (execute / provision / wake / getSession / emitEvent / getEvents)让具体 harness implementations replaceable
- **Session External Persistence**: Treating session log as object living outside context window, harness通过 getEvents()按位置切片访问历史, avoiding compaction这类 irreversible keep-or-drop decisions
- **Progressive Disclosure**: AGENTS.md only as directory (约100行), pointing to docs/下 structured knowledge base,让 agent从小而稳定入口起步再按需深入, replacing "one big file塞所有指令" anti-pattern
- **Agent Legibility**: Information not accessible in agent runtime context等于不存在; Slack共识, Google Docs, oral约定必须落回 repo才能被 agent利用
- **Entropy Garbage Collection**: Agent-generated code会复制已有 patterns (含次优 patterns),需要周期性自动扫描偏差、开重构 PR的持续回收机制, analogous to GC
- **Taste Invariants**: Custom linter encoding architectural taste as mechanical rules, linter error messages直接写成 agent-readable repair guidance, implementing "encode once, execute globally"

## Related Topics

- [AI Research](../ai-research/_index.md) (Tool comparisons, personal developer practices; includes [Capability-Alignment Paradox](../ai-research/capability-alignment-paradox.md) and [Cyber-Driven Restricted Release](../ai-research/cyber-driven-restricted-release.md) related to Mythos Preview system card)
- [Agent Deployment](../agent-deployment/_index.md) (Non-technical team deploying AI agents' real blockers, four-ring gap, 9 person/day/expert IT time limit. Complements [OpenClaw Harness Stability](openclaw-harness-stability.md) and [China AI Coding Agent Access](china-ai-coding-agent-access.md): this topic from tool and harness perspective, agent-deployment from actual pushing tools to non-technical employees现场 perspective)
- [LLM Knowledge Bases](../llm-knowledge-bases/_index.md) (Tool practices in knowledge base workflows)
- [Open Source and Software Value](../open-source/_index.md) (Code depreciation and open source value migration)
- [GEO](../geo/_index.md) (GEO extending to agent economy: skill distribution as new distribution mechanism, to AI to People path, directly related to this topic's agent ecosystem and MCP discussions)

## Related Sources

- [Claude Code Documentation](https://code.claude.com/docs/en/)
- [Anthropic Platform Docs](https://platform.claude.com/docs/en/)
- [Anthropic Research](https://www.anthropic.com/research)
- [OpenAI Codex App Worktrees](https://developers.openai.com/codex/app/worktrees)
- [karpathy/autoresearch](https://github.com/karpathy/autoresearch) (Autonomous AI research loop, related analysis见 [Reward Signal Quality and Autonomous Optimization Boundary](../ai-research/reward-signal-automation-boundary.md))