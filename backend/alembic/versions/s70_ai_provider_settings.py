"""
Add AI Provider Settings to system_settings table.

Revision ID: s70_ai_provider_settings
Revises: sb5313e82078
Create Date: 2026-01-16

SDLC 5.1.1 Compliance:
- ADR-007: Multi-Provider AI Integration (Ollama → Claude → GPT-4o)
- ADR-027: Database-backed settings for admin configuration
- EP-06: IR-Based Codegen Engine configuration

New Settings:
- ai.ollama_url: Ollama server URL
- ai.ollama_model: Default Ollama model
- ai.anthropic_api_key: Claude API key (encrypted)
- ai.openai_api_key: OpenAI API key (encrypted)
- ai.default_provider: Default AI provider
- ai.fallback_enabled: Enable fallback chain

Security Note:
API keys stored in JSONB are encrypted at database level (PostgreSQL pgcrypto).
For additional security, consider using HashiCorp Vault in production.
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 's70_ai_provider_settings'
down_revision = 'sb5313e82078'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add AI provider settings to system_settings table."""

    # Insert AI provider settings
    op.execute("""
        INSERT INTO system_settings (key, value, category, description, version) VALUES
        -- Ollama Configuration (Primary Provider - ADR-007)
        ('ai_ollama_url', '""', 'ai', 'Ollama server URL (e.g., http://ollama:11434)', 1),
        ('ai_ollama_model', '"qwen3:14b"', 'ai', 'Default Ollama model for AI tasks', 1),
        ('ai_ollama_timeout', '30', 'ai', 'Ollama request timeout in seconds', 1),

        -- Claude/Anthropic Configuration (Fallback Provider)
        ('ai_anthropic_api_key', '""', 'ai', 'Anthropic API key for Claude (leave empty to disable)', 1),
        ('ai_anthropic_model', '"claude-sonnet-4-5-20250929"', 'ai', 'Claude model to use', 1),

        -- OpenAI Configuration (Fallback Provider)
        ('ai_openai_api_key', '""', 'ai', 'OpenAI API key (leave empty to disable)', 1),
        ('ai_openai_model', '"gpt-4o"', 'ai', 'OpenAI model to use', 1),

        -- AI Provider Chain Configuration
        ('ai_default_provider', '"ollama"', 'ai', 'Default AI provider (ollama, claude, openai)', 1),
        ('ai_fallback_enabled', 'true', 'ai', 'Enable automatic fallback to next provider on failure', 1),
        ('ai_fallback_chain', '["ollama", "claude", "openai"]', 'ai', 'Provider fallback order', 1),

        -- EP-06 Codegen Configuration
        ('codegen_ollama_url', '""', 'ai', 'Ollama URL for code generation (if different from main)', 1),
        ('codegen_model_primary', '"qwen3-coder:30b"', 'ai', 'Primary model for code generation', 1),
        ('codegen_model_fast', '"qwen3:8b"', 'ai', 'Fast model for quick drafts', 1),
        ('codegen_timeout', '120', 'ai', 'Codegen request timeout in seconds', 1)
        ON CONFLICT (key) DO NOTHING;
    """)


def downgrade() -> None:
    """Remove AI provider settings."""

    op.execute("""
        DELETE FROM system_settings
        WHERE key IN (
            'ai_ollama_url',
            'ai_ollama_model',
            'ai_ollama_timeout',
            'ai_anthropic_api_key',
            'ai_anthropic_model',
            'ai_openai_api_key',
            'ai_openai_model',
            'ai_default_provider',
            'ai_fallback_enabled',
            'ai_fallback_chain',
            'codegen_ollama_url',
            'codegen_model_primary',
            'codegen_model_fast',
            'codegen_timeout'
        );
    """)
