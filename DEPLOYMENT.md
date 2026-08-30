# Render deployment

This project packages both the Remote UI and its Java/WebSocket backend in one
container. It is not suitable for GitHub Pages or Vercel's static hosting.

## Deploy from GitHub

1. Push this project to a GitHub repository. Do not commit `.mewcode/config.yaml`.
2. In Render, select **New > Blueprint** and choose the repository. Render reads
   `render.yaml` and creates the `mewcode-remote` web service.
3. Set these secret environment variables in the service settings:
   - `OPENAI_API_KEY`: your DeepSeek API key (used by the `openai-compat` provider).
   - `REMOTE_UI_USERNAME`: a username shared only with approved reviewers.
   - `REMOTE_UI_PASSWORD`: a strong, unique password.
   - `DEMO_MODE=true`: enables server-side public-demo limits.
4. Deploy. The service uses Render's assigned `PORT` automatically. Open the
   generated `https://*.onrender.com` URL and sign in with the credentials above.

## Important security note

The Remote UI can ask the server-side agent to use tools. Keep the URL protected
by the required Basic Authentication. Do not place an API key in Git, source
files, or `deploy/config.yaml`.

With `DEMO_MODE=true`, the server limits input size, requests per IP, global
daily requests, output size, LLM iterations, and a conservative daily Token
reservation. It exposes only `ReadFile`, `Glob`, and `Grep`; command execution,
file writes, sub-agents, MCP, hooks, and most slash commands are unavailable.
The defaults can be changed with the `DEMO_*` variables in `render.yaml`.

These counters are held in process memory. Render Free restarts and sleep cycles
reset them, so use a dedicated DeepSeek key with a small account balance as the
provider-side hard spending ceiling. A persistent datastore is required for a
strict daily budget across restarts.

The Render Free plan is suitable for a portfolio preview only: it can sleep after
idle time, has cold starts, and has no persistent local filesystem. For an
interviewer-facing public project page, link to this protected live demo plus a
short screen recording and the source repository.
