# OpenSpec: User Authentication Module

**Version**: 2.0
**Author**: Legacy System
**Date**: 2026-01-30

## Description

This document uses OpenSpec format, which is different from SDLC 6.0.5.

## Specification

### Data Model

- User: id, email, password_hash, created_at
- Session: id, user_id, token, expires_at

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /auth/login | User login |
| POST | /auth/logout | User logout |
| GET | /auth/me | Current user |

### Business Rules

1. Password must be at least 12 characters
2. Sessions expire after 24 hours
3. Maximum 5 failed login attempts

## Notes

This format should be detected as non-SDLC 6.0.5 and can be converted using:
- CLI: `sdlcctl spec convert openspec_format.md`
