# Architecture Boundaries Policy
#
# SDLC Stage: 04 - BUILD
# Sprint: 43 - Policy Guards & Evidence UI
# Framework: SDLC 5.1.1
#
# Purpose:
# Enforce 4-layer architecture by preventing cross-layer imports.
# Ensures proper separation of concerns and maintainability.
#
# 4-Layer Architecture:
# 1. Presentation (API routes, controllers) - Top layer
# 2. Business (Services, use cases) - Middle layer
# 3. Data (Repositories, database) - Bottom layer
# 4. Domain (Models, schemas) - Cross-cutting
#
# Rules:
# - Presentation cannot directly import from Data layer
# - Business can import from Data layer
# - Domain is accessible from all layers

package ai_safety.architecture_boundaries

import future.keywords.in

default allow = true

# Deny if layer violations detected
allow = false {
    count(violations) > 0
}

# Find architecture violations
violations[violation] {
    some file in input.files
    file.layer == "presentation"
    some import_stmt in file.imports
    is_data_layer_import(import_stmt)
    violation := {
        "file": file.path,
        "import": import_stmt,
        "message": "Presentation layer cannot directly import from data layer. Use service layer instead.",
    }
}

# Data layer package patterns
is_data_layer_import(import_stmt) {
    data_layer_packages := [
        "app.db",
        "app.database",
        "app.repositories",
        "sqlalchemy",
        "databases",
        "asyncpg",
        "psycopg",
        "pymysql",
        "sqlite3",
    ]
    some pkg in data_layer_packages
    startswith(import_stmt, pkg)
}

# Additional violations: Direct database connection in presentation
violations[violation] {
    some file in input.files
    file.layer == "presentation"
    contains(file.content, "create_engine")
    violation := {
        "file": file.path,
        "message": "Direct database engine creation in presentation layer is forbidden",
    }
}

violations[violation] {
    some file in input.files
    file.layer == "presentation"
    contains(file.content, "AsyncSession")
    not contains(file.path, "dependencies")  # Allow in deps for DI
    violation := {
        "file": file.path,
        "message": "Direct AsyncSession usage in presentation layer. Use dependency injection.",
    }
}
