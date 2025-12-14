# Documentation Gap Closure – Undocumented & Unclear APIs

This note captures thirty concrete code elements that previously lacked centralized, human-readable documentation. Each entry lists the file path, purpose, inputs/outputs, failure behavior, and an example so that engineers and AI agents can use the APIs safely.

## 1) Newly Documented APIs / Functions / Components (10)

1. **useIsMobile** — `apps/web/src/hooks/use-mobile.tsx`  
   - Purpose: React hook that reports whether the viewport width is below 768px, updating on `matchMedia` changes.  
   - Returns: `boolean` flag (`true` when `<768px`).  
   - Failure/Notes: Requires browser runtime; returns `false` during initial undefined state.  
   - Example:  
     ```tsx
     const isMobile = useIsMobile();
     return <div className={isMobile ? "stacked" : "grid"} />;
     ```

2. **Toaster component** — `apps/web/src/components/ui/toaster.tsx`  
   - Purpose: Renders toast notifications via `ToastProvider` and `useToast()` state.  
   - Inputs: Uses hook-provided `toasts` array; no props required.  
   - Output: JSX tree with mapped `Toast` entries and a `ToastViewport`.  
   - Example: Place once in app root: `<Toaster />`.

3. **useIsMobile (UI kit)** — `frontend/ui/src/hooks/use-mobile.tsx`  
   - Purpose/Behavior: Same mobile breakpoint detection as the app hook for the shared UI package.  
   - Returns: Boolean mobile flag.  
   - Example: `const compact = useIsMobile();`

4. **Toaster component (UI kit)** — `frontend/ui/src/components/ui/toaster.tsx`  
   - Purpose: UI kit wrapper around toast state; mirrors app implementation.  
   - Usage: Include in UI kit consumers to surface queued toasts.  
   - Notes: Requires `useToast` provider from the same package.

5. **createRateLimiter (Express)** — `core/contract_service/contracts-L1/contracts/src/routes.ts`  
   - Purpose: Factory producing an Express rate-limit middleware (100 req / 15 min per IP).  
   - Inputs: None; uses `express-rate-limit`.  
   - Output: `RateLimitRequestHandler` that responds with HTTP 429 JSON payload and trace ID.  
   - Example: `app.use(createRateLimiter());`

6. **createRateLimiter (custom store-aware)** — `core/contract_service/contracts-L1/contracts/src/middleware/rate-limit.ts`  
   - Purpose: Rate limiter supporting pluggable stores (memory or Redis) with custom keys and callbacks.  
   - Inputs: `RateLimitConfig` plus optional `RateLimitStore`.  
   - Output: Async Express middleware that sets `X-RateLimit-*` headers.  
   - Example: `app.use(createRateLimiter(rateLimitPresets.standard));`

7. **createSmartRateLimiter** — same file as above  
   - Purpose: Strategy selector choosing strict/auth/API-key/lenient presets based on path and `x-api-key`.  
   - Inputs: Optional shared `RateLimitStore`.  
   - Behavior: Delegates to `createRateLimiter` with computed preset per request.  
   - Example: `app.use(createSmartRateLimiter(redisBackedStore));`

8. **formatZodError** — `core/contract_service/contracts-L1/contracts/src/middleware/zodErrorHandler.ts`  
   - Purpose: Converts a `ZodError` into a single human-readable string for responses/logging.  
   - Inputs: `ZodError`.  
   - Output: `"Invalid input: <messages>"`.  
   - Example: `return res.status(400).json({ error: formatZodError(err) });`

9. **isZodError** — same file as above  
   - Purpose: Type guard detecting `ZodError` instances before specialized formatting.  
   - Output: `error is ZodError`.  
   - Example: `if (isZodError(err)) handle(formatZodError(err));`

10. **setupTests** — `tests/setup.ts`  
    - Purpose: Central Jest/RTL bootstrap configuring `@testing-library/jest-dom` and global options.  
    - Behavior: Runs on import; logs a setup banner; can be extended for mocks.  
    - Example: Import in Jest config: `setupFilesAfterEnv: ["<rootDir>/tests/setup.ts"]`.

## 2) Code Elements Now Properly Documented (10)

11. **ProvenanceService.generateFileDigest** — `core/contract_service/contracts-L1/contracts/src/services/provenance.ts`  
    - Purpose: Validates a file path then returns `sha256:<hex>` digest for attestation inputs.  
    - Inputs: `filePath` (string, validated against SAFE_ROOT).  
    - Failures: Throws on invalid path or unreadable file.  
    - Example: `const digest = await provenanceService.generateFileDigest('artifacts/build.tar');`

12. **ProvenanceService.createBuildAttestation** — same file  
    - Purpose: Builds SLSA-compatible attestation with builder metadata and subject digest.  
    - Inputs: `subjectPath`, `builder` info, optional `metadata`.  
    - Output: `BuildAttestation` including `slsaProvenance`.  
    - Example: `await provenanceService.createBuildAttestation('dist/app.tgz', builderInfo);`

13. **ProvenanceService.verifyAttestation** — same file  
    - Purpose: Structural validation plus optional digest re-computation when `subject.path` exists.  
    - Output: `boolean` validity flag.  
    - Notes: Returns `false` on any caught exception; use for API verify endpoint.

14. **ProvenanceService.exportAttestation** — same file  
    - Purpose: Serializes an attestation to pretty-printed JSON for download/export.  
    - Input: `BuildAttestation`.  
    - Output: `string` JSON.  
    - Example: `res.send(provenanceService.exportAttestation(attestation));`

15. **ProvenanceService.importAttestation** — same file  
    - Purpose: Parses JSON into `BuildAttestation`, throwing on missing `id`/`predicate`.  
    - Input: JSON string.  
    - Output: `BuildAttestation`.  
    - Example: `const att = provenanceService.importAttestation(body.attestationJson);`

16. **PathValidator.validateAndResolvePath** — `core/contract_service/contracts-L1/contracts/src/utils/path-validator.ts`  
    - Purpose: Normalizes absolute/relative paths with symlink resolution and boundary checks.  
    - Inputs: `filePath`; configuration-derived `safeRoot`/prefixes.  
    - Output: Canonical absolute path or `PathValidationError`.  
    - Example: `const safe = await validator.validateAndResolvePath('uploads/report.pdf');`

17. **PathValidator._validateAbsolutePath** — same file  
    - Purpose: Enforces allowed absolute prefixes after canonicalization; rejects traversal.  
    - Errors: Throws `PATH_OUTSIDE_ALLOWED_DIRS` when outside prefixes.  
    - Usage: Internal, but relevant for security reviews of absolute path flows.

18. **PathValidator._validateRelativePath** — same file  
    - Purpose: Resolves relative paths against `safeRoot`, ensuring the root exists and is honored.  
    - Errors: `SAFE_ROOT_NOT_RESOLVABLE` or `PATH_OUTSIDE_SAFE_ROOT`.  
    - Example: Used by `validateAndResolvePath` when given non-absolute input.

19. **MemoryStore.increment** — `core/contract_service/contracts-L1/contracts/src/middleware/rate-limit.ts`  
    - Purpose: In-memory rate-limit counter with automatic window reset and cleanup.  
    - Inputs: `key`, `windowMs`.  
    - Output: New count (number).  
    - Notes: Resets window when expired; safe for single-node deployments.

20. **RedisStore.increment** — same file  
    - Purpose: Redis-backed atomic increment + TTL for distributed rate limiting.  
    - Inputs: `key`, `windowMs`; uses `multi().incr().pexpire().exec()`.  
    - Errors: Throws on missing results, Redis errors, or unexpected return types.

## 3) Clarified Documentation for Ambiguous Items (10)

21. **validateAdvisory** — `core/advisory-database/src/validators/advisory-validator.ts`  
    - Role: Schema-validates an advisory object, returning structured success/errors.  
    - Inputs: `Advisory` domain model.  
    - Output: `{ valid: boolean; errors?: string[] }`.  
    - Use: Gatekeeper before persisting advisories.

22. **parseAndValidateAdvisory** — same file  
    - Role: Parses unknown data into an advisory, runs validation, and returns both the parsed value and validation report.  
    - Failure: Throws on non-object input; returns `errors` array on validation issues.  
    - Example: `const { advisory, result } = parseAndValidateAdvisory(payload);`

23. **generateGHSAId** — `core/advisory-database/src/utils/ghsa.ts`  
    - Role: Produces cryptographically random GHSA IDs (`GHSA-xxxx-xxxx-xxxx`).  
    - Behavior: Uses `webcrypto.getRandomValues`; avoids ambiguous characters.  
    - Example: `const id = generateGHSAId();`

24. **computeDeterministicGHSAId** — same file  
    - Role: Derives a deterministic GHSA-like ID from input data via SHA-256 and charset mapping.  
    - Input: Arbitrary string seed (e.g., CVE slug).  
    - Output: Stable GHSA-format ID for idempotent advisory generation.

25. **extractGHSAIds** — same file  
    - Role: Scans text for GHSA patterns and returns a de-duplicated list.  
    - Input: Freeform text (commit messages, advisories).  
    - Output: `string[]` of IDs; empty array when none found.

26. **AutomationLauncher.start** — `automation_launcher.py`  
    - Role: Bootstraps master orchestrator, auto-discovers engines, starts heartbeat, and prints status.  
    - Inputs: Optional banner flag; uses `DEFAULT_CONFIG` for engine paths/mode.  
    - Output: `bool` success flag; writes heartbeat file `.launcher_heartbeat.json`.  
    - Failure: Logs import/runtime errors and returns `False`.

27. **AutomationLauncher.execute_pipeline** — same file  
    - Role: Runs a pipeline by ID through the orchestrator’s executor.  
    - Inputs: `pipeline_id`, optional `input_data` dict.  
    - Output: Result dict with `success` and payload/error.  
    - Notes: Returns error object when orchestrator not started.

28. **AutomationLauncher.execute_task** — same file  
    - Role: Dispatches a task to a specific engine and normalizes the result envelope.  
    - Inputs: `engine_id`, `task` dict containing `operation` and params.  
    - Output: `{ success, result, error }` with boolean success flag.

29. **AutomationLauncher.list_engines** — same file  
    - Role: Enumerates registered engines with id/name/type/health for status UIs.  
    - Output: `List[Dict]`; empty list when orchestrator is absent or stopped.  
    - Usage: CLI `list-engines` subcommand prints the table.

30. **AutomationLauncher.get_status** — same file  
    - Role: Aggregates orchestrator status plus launcher metadata (mode, uptime).  
    - Output: Dict containing `running`, `launcher`, and orchestrator fields.  
    - Notes: Returns `{running: False, message: "系統未啟動"}` before start; useful for probes.

