# Reference Project Analysis

## Scope

Reference repositories were cloned to `/private/tmp/pre-vibe-reference-projects` for local inspection:

- `linshenkx/prompt-optimizer`
- `ckelsoe/prompt-architect`

The goal was not to copy their product model, but to identify implementation patterns that can make pre-vibe more usable while preserving its agent-workflow positioning.

## prompt-optimizer

Useful patterns:

- Treat prompt work as an asset lifecycle: optimize, test, compare, save, and reuse.
- Support multiple entry points: web, desktop, extension, Docker, and MCP.
- Keep template choices explicit so users can understand what style of optimization they are applying.
- Provide evaluation and comparison workflows instead of relying only on subjective "looks better" judgment.

What pre-vibe should not copy:

- Do not become a generic text-to-text prompt optimizer.
- Do not default to long optimized prompts when the agent already has local project files.
- Do not mix generated reports into the plugin source package.

Adopted in v0.1.1:

- Separate package source and reports.
- Keep deterministic comparison tests.
- Treat generated context as reusable disk artifacts, but inject only the compact brief.

## prompt-architect

Useful patterns:

- Start with intent routing before choosing a framework.
- Evaluate quality across clarity, specificity, context, completeness, and structure.
- Ask targeted clarification questions rather than open-ended brainstorming.
- Use progressive disclosure: load detailed framework guidance only when needed.
- End with a clean handoff prompt the user can actually use.

What pre-vibe should not copy:

- Do not expose 27 generic prompt frameworks as the product core.
- Do not ask 3-5 questions by default for simple daily tasks.
- Do not present the full framework scaffold as formal agent context.

Adopted in v0.1.1:

- Added lightweight quality scoring over the same five dimensions.
- Added scenario-aware intake and budget routing.
- Added blocking-question logic with a `micro` mode that asks none.
- Kept skill guidance short and moved details into reference files.

## Product Implication

The right pre-vibe differentiation is:

```text
prompt optimizer: improve prompt text
prompt architect: choose and apply prompt frameworks
pre-vibe: prepare the minimum useful first-turn context for an agent workflow
```

This keeps the section 20 product point intact: pre-vibe is about environment/project/user information gaps in agent workflows, not just prettier prompt prose.
