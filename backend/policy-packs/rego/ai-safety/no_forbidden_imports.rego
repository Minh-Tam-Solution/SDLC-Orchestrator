# No Forbidden Imports Policy
#
# SDLC Stage: 04 - BUILD
# Sprint: 43 - Policy Guards & Evidence UI
# Framework: SDLC 5.1.1
#
# Purpose:
# Prevent importing forbidden packages to ensure legal compliance (AGPL)
# and prevent usage of deprecated/insecure libraries.
#
# Default Forbidden:
# - minio (AGPL v3 - network-only access required)
# - grafana_sdk (AGPL v3 - iframe embed only)
# - grafana_client (AGPL v3)
#
# Custom forbidden imports can be configured via input.config.forbidden_imports

package ai_safety.no_forbidden_imports

import future.keywords.in

default allow = true

# Deny if forbidden imports detected
allow = false {
    count(violations) > 0
}

# Find forbidden import violations
violations[violation] {
    some file in input.files
    some import_stmt in file.imports
    is_forbidden_import(import_stmt)
    violation := {
        "file": file.path,
        "import": import_stmt,
        "message": sprintf("Forbidden import: %s. Use network-only access via HTTP/REST API instead.", [import_stmt]),
    }
}

# Check against custom forbidden imports from config
is_forbidden_import(import_stmt) {
    some forbidden in input.config.forbidden_imports
    startswith(import_stmt, forbidden)
}

# Default AGPL libraries (always forbidden)
is_forbidden_import(import_stmt) {
    agpl_packages := [
        "minio",
        "grafana_sdk",
        "grafana_client",
        "grafana_api",
    ]
    some pkg in agpl_packages
    startswith(import_stmt, pkg)
}

# Deprecated/insecure packages
is_forbidden_import(import_stmt) {
    deprecated_packages := [
        "pickle",     # Security risk
        "cPickle",    # Security risk
        "marshal",    # Security risk
        "telnetlib",  # Insecure protocol
    ]
    some pkg in deprecated_packages
    import_stmt == pkg
}

# Additional check: from X import pattern
violations[violation] {
    some file in input.files
    contains(file.content, "from minio import")
    violation := {
        "file": file.path,
        "message": "Direct MinIO SDK import forbidden. Use S3 REST API via requests/httpx.",
    }
}

violations[violation] {
    some file in input.files
    contains(file.content, "from grafana")
    violation := {
        "file": file.path,
        "message": "Direct Grafana SDK import forbidden. Use iframe embedding or Grafana HTTP API.",
    }
}
