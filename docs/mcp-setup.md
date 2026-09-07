# MCP setup

This project uses project-scoped Codex MCP configuration in `.codex/config.toml`. Codex loads project-scoped configuration only for trusted projects. Restart Codex or open a new session after changing the file.

The local Playwright package version is pinned so every team member receives the same server version. Review and update the pin deliberately rather than using `@latest`. Context7 and Stitch use their maintained remote endpoints.

## Context7

- **Purpose:** Fetch current, version-specific documentation for frameworks, libraries, SDKs and APIs.
- **Configuration:** Remote Streamable HTTP server at `https://mcp.context7.com/mcp`.
- **Permissions:** Network access to Context7. It has no project write permission through its MCP tools.
- **Secrets:** None required. `CONTEXT7_API_KEY` is optional and may provide higher limits. Set it in the shell environment, never in the repository.
- **Verify:** Run `codex mcp get context7_docs`, then ask Codex to resolve a library and fetch its current documentation.
- **Use when:** Important implementation depends on current or version-specific syntax, behaviour, SDKs or APIs.
- **Do not use when:** The code is trivial or current documentation cannot affect correctness.
- **Known limitations:** Coverage and freshness depend on Context7's index. Confirm consequential claims against official project documentation. Network access is required and anonymous use may be rate-limited.

## Playwright MCP

- **Purpose:** Browser-driven QA and interaction testing of the Next.js application.
- **Configuration:** Local isolated STDIO server started with `npx -y @playwright/mcp@0.0.80 --isolated --browser=chrome`. Chrome provides the Chromium-engine check. Browser requests are limited to the local frontend and backend origins on ports 3000 and 8000.
- **Permissions:** Starts and controls an isolated local browser. It may navigate, click, type, resize viewports, inspect accessibility state, upload test files when requested, and capture screenshots. It is not given unrestricted file access. The RCE-equivalent `browser_run_code_unsafe` tool is disabled.
- **Secrets:** None. Do not place credentials in prompts, storage-state files or committed test fixtures.
- **Verify:** Run `codex mcp get playwright`. Start the frontend, then ask Playwright MCP to open `http://localhost:3000`, report the page title, exercise the visible controls and close the browser.
- **Use when:** Verifying every implemented route, control, form, filter, search flow, navigation path, modal, pagination state, responsive layout, keyboard path, and applicable loading, empty, error and success state.
- **Do not use when:** A unit or API test is the smaller and more reliable check, or the target is outside the approved local origins.
- **Known limitations:** One configured MCP instance uses Chrome's Chromium engine. For cross-browser checks, use the repository-local Playwright suite or deliberately change the MCP browser and restart Codex. Browser binaries may need a one-time installation. The configured allowed origins reject unlisted ports with `net::ERR_BLOCKED_BY_CLIENT`; use the documented frontend origin on port 3000 instead of weakening the origin list. On 7 September 2026 the Investigation Queue passed MCP interaction checks at `http://localhost:3000`, while the local suite supplied Chromium, Firefox and WebKit coverage.

## Google Stitch

- **Purpose:** UI/UX exploration, layout generation and design references only.
- **Configuration:** Direct Streamable HTTP connection to `https://stitch.googleapis.com/mcp`. The API key is read from `STITCH_API_KEY` and sent as the `X-Goog-Api-Key` header. The server is committed as `enabled = false` so a fresh checkout does not fail or make remote changes before a team member supplies credentials and deliberately enables it.
- **Permissions:** Network access to Google Stitch. Write-capable tools require approval because `default_tools_approval_mode = "writes"`, and project deletion is disabled entirely.
- **Secrets:** `STITCH_API_KEY` is required. Keep it in the shell environment or an OS secret store. Never put it in `.codex/config.toml`, `.env.example`, source files or Git.
- **Verify:** Set `STITCH_API_KEY`, change `enabled = false` to `enabled = true`, restart Codex, run `codex mcp get stitch_design`, then list accessible Stitch projects. Do not create or modify a project merely as a connectivity test.
- **Use when:** Exploring layout directions or producing a design reference before implementing the accessible, responsive UI in the project's own design system.
- **Do not use when:** Implementing production code, creating risk flags, changing data, or when a straightforward design can be built directly.
- **Known limitations:** Stitch is a generative design aid, not a production-code source. Output quality varies. Authentication and service availability depend on the Google account and project. Enabling it changes one tracked configuration line, so do not commit that personal enablement change unless the team agrees.

## GitHub MCP, deferred

- **Purpose:** Later repository inspection, issues, pull requests, branches and CI visibility.
- **Configuration:** The project-specific GitHub MCP entry remains unconfigured. The local Git origin is now `https://github.com/AdarshXtech/MPLADS-RISK-INTELLIGENT-.git`; linking that remote did not commit or push files or configure this MCP entry. If a separate project-specific MCP connection is needed, review permissions and start with the official read-only server:

  ```toml
  [mcp_servers.github]
  url = "https://api.githubcopilot.com/mcp/readonly"
  bearer_token_env_var = "GITHUB_PAT_TOKEN"
  http_headers = { "X-MCP-Toolsets" = "context,repos,issues,pull_requests,actions" }
  default_tools_approval_mode = "writes"
  ```

- **Permissions:** Initially read-only, limited to the listed toolsets. Use a fine-grained token restricted to the new repository. Agree any later write scopes with the team lead and keep write tools approval-gated.
- **Secrets:** `GITHUB_PAT_TOKEN` will be required after configuration. Keep it in the launching shell or an approved secret store.
- **Verify:** Before adding it, run `git remote -v`, review the current official GitHub MCP server documentation, and agree token permissions with the team lead. Then run `codex mcp get github` and request read-only repository metadata.
- **Use when:** The repository exists and the task genuinely needs remote repository, issue, pull request, branch or CI context.
- **Do not use when:** Local Git is sufficient, no repository exists, or the requested operation is destructive and lacks explicit approval. Never force-push, delete branches, close issues or merge pull requests automatically.
- **Known limitations:** GitHub API rate limits, organisation policy, token expiry and token scopes affect access. Read-only mode intentionally cannot create or modify issues, branches or pull requests. Changing to the non-read-only endpoint is a separate security decision.

## Environment setup

PowerShell examples for the current terminal:

```powershell
$env:CONTEXT7_API_KEY = "<optional-context7-key>"
$env:STITCH_API_KEY = "<stitch-key>"
```

Use persistent user-level environment variables or an approved secret manager if needed. Do not use `setx` on a shared machine without understanding that it persists the secret in the user environment.

The checked-in `.env.example` lists variable names only. Codex MCP servers do not automatically load `.env` files, so export variables into the process that launches Codex.

## General verification

From the repository root:

```powershell
codex mcp list
codex mcp get context7_docs
codex mcp get playwright
codex mcp get stitch_design
```

The project entries should show `context7_docs` and Playwright enabled, `stitch_design` disabled, and no project GitHub server. User-level MCPs may also appear because Codex merges project and user configuration. A configured server is not added to an already-running Codex session's tool inventory; restart the local Codex client after configuration changes.
