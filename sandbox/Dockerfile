# Minimal, locked-down image for executing untrusted Boku-nano candidate
# `solve(xs, k)` code (see ../homework.md and ../task_list.md).
#
# This image ships NO extra Python packages and has no network access at
# runtime (enforced by the host's `docker run --network none`). It runs as
# a non-root user, and process-level CPU/memory/pid limits are applied by
# the host via `docker run --memory/--cpus/--pids-limit` (see client.py),
# with runner.py applying a second, independent set of limits via
# `resource.setrlimit` from inside the container.
FROM python:3.11-slim

RUN useradd --no-create-home --shell /usr/sbin/nologin --uid 10001 sandbox

WORKDIR /sandbox
COPY ast_safety.py runner.py ./
RUN chown -R sandbox:sandbox /sandbox

USER sandbox

# No command-line arguments are trusted. Candidate code + tests arrive as a
# single JSON document on stdin (see client.py) and the verdict is written
# as a single JSON document on stdout.
# -I: isolated mode (ignore PYTHON* env vars, no user site dir)
# -S: skip importing the `site` module (no site-packages, faster start)
ENTRYPOINT ["python3", "-I", "-S", "runner.py"]
