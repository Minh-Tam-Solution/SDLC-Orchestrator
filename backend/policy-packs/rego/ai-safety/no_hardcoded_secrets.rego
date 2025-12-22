# No Hardcoded Secrets Policy
#
# SDLC Stage: 04 - BUILD
# Sprint: 43 - Policy Guards & Evidence UI
# Framework: SDLC 5.1.1
#
# Purpose:
# Detect hardcoded passwords, API keys, tokens, and other secrets in code.
# This is a CRITICAL security policy that blocks merge when violations found.
#
# Patterns detected:
# - password = "..."
# - api_key = "..."
# - secret = "..."
# - token = "..." (with sufficient entropy)
# - AWS credentials (Access Key ID, Secret Access Key)
#
# Exclusions:
# - Test files (/tests/)
# - Example files (.example, .sample)
# - Environment templates (.env.example)

package ai_safety.no_hardcoded_secrets

import future.keywords.in

default allow = true

# Deny if hardcoded secrets detected
allow = false {
    count(violations) > 0
}

# Find violations in file content
violations[violation] {
    some file in input.files
    not is_excluded_file(file.path)
    some i, line in split(file.content, "\n")
    contains_secret(line)
    violation := {
        "file": file.path,
        "line": i + 1,
        "pattern": "hardcoded secret",
        "message": "Potential hardcoded secret detected",
    }
}

# Secret detection patterns
contains_secret(line) {
    # Password patterns
    regex.match(`(?i)password\s*[=:]\s*["'][^"']+["']`, line)
}

contains_secret(line) {
    # API key patterns
    regex.match(`(?i)api[_-]?key\s*[=:]\s*["'][^"']+["']`, line)
}

contains_secret(line) {
    # Secret patterns
    regex.match(`(?i)secret\s*[=:]\s*["'][^"']+["']`, line)
}

contains_secret(line) {
    # Token patterns (with length check for entropy)
    regex.match(`(?i)token\s*[=:]\s*["'][A-Za-z0-9+/=]{20,}["']`, line)
}

contains_secret(line) {
    # AWS Access Key ID
    regex.match(`(?i)AWS_ACCESS_KEY_ID\s*[=:]\s*["'][A-Z0-9]{20}["']`, line)
}

contains_secret(line) {
    # AWS Secret Access Key
    regex.match(`(?i)AWS_SECRET_ACCESS_KEY\s*[=:]\s*["'][A-Za-z0-9+/]{40}["']`, line)
}

contains_secret(line) {
    # Private key block start
    contains(line, "-----BEGIN PRIVATE KEY-----")
}

contains_secret(line) {
    # Private key block start (RSA)
    contains(line, "-----BEGIN RSA PRIVATE KEY-----")
}

# File exclusion rules
is_excluded_file(path) {
    contains(path, "/tests/")
}

is_excluded_file(path) {
    contains(path, "/test/")
}

is_excluded_file(path) {
    endswith(path, ".example")
}

is_excluded_file(path) {
    endswith(path, ".sample")
}

is_excluded_file(path) {
    endswith(path, ".template")
}

is_excluded_file(path) {
    endswith(path, ".env.example")
}

is_excluded_file(path) {
    contains(path, "/fixtures/")
}

is_excluded_file(path) {
    contains(path, "/mocks/")
}
