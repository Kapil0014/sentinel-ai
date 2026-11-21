# Demo site

A small static shop used as Sentinel AI's controlled test target.

**Current state (Week 1): clean skeleton, no seeded defects yet.**
Pages: home, products, login, contact, about. A `/healthz` endpoint is used by Docker health checks.

## Planned in Week 2

Seven intentional defects plus a `ground-truth.json` labelling each one, so detection can be
verified honestly:

1. Broken internal link (404)
2. Incorrect form validation (accepts an invalid email)
3. Missing image
4. JavaScript console error
5. Incorrect button behaviour
6. Visual layout difference (**post-MVP**: needs the visual-regression engine)
7. Incorrect navigation (link goes to the wrong page)

Also a page containing prompt-injection text, to test that page content can never change the
agent's allowed actions.

## Access

- From your browser: <http://localhost:8080>
- From inside Docker Compose (what the worker tests): `http://demo-site` (allowed via
  `ALLOWED_PRIVATE_HOSTS=demo-site`, development only).
