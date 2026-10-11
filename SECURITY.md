# Security Policy

Iterduca handles network-routing configuration, subscription content, local controller credentials, proxy endpoints, and operating-system proxy settings. Treat these values as sensitive.

## Supported versions

Security fixes are applied to the latest published release and the current `main` branch. Older releases may not receive backports.

## Reporting a vulnerability

Prefer GitHub private vulnerability reporting when it is available for this repository.

Do not publish subscription URLs, proxy credentials, controller secrets, access tokens, private traffic records, or other sensitive material in a public issue. If private reporting is unavailable, open a minimal public issue requesting a private contact path without including exploit details or secrets.

A useful report should include:

- the affected Iterduca version or commit;
- the affected component;
- reproduction steps that do not expose real credentials;
- the expected and observed behavior;
- the security impact.

## Security boundaries

Iterduca uses Mihomo as an external routing core. Mihomo vulnerabilities should be reported to the Mihomo project when the issue is specific to that core.

Iterduca does not require users to commit personal profiles or subscription files to the repository. Test fixtures and screenshots must use synthetic or sanitized data.

When a credential or subscription URL is exposed, revoke or rotate it. Removing it from the latest Git commit is not sufficient if it remains in repository history.
