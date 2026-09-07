# Frontend

The Next.js and TypeScript application provides the authenticated Command Centre, Investigation Queue, evidence review and filtered CSV download.

```powershell
npm ci
npm run dev -- --hostname 127.0.0.1 --port 3000
```

Quality checks:

```powershell
npm run lint
npm run build
npm run test:e2e
```

The browser-test suite uses an explicitly synthetic API and runs Chromium, Firefox and WebKit. It does not write to the official development database.

Required server-side variables are documented in [Investigation Queue setup](../docs/investigation-queue.md). Do not prefix secrets with `NEXT_PUBLIC_`. This application requires a running Node.js server and cannot be deployed as a static export. See [deployment readiness](../docs/deployment.md).
