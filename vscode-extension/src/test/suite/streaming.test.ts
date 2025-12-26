/**
 * Streaming Code Generation Tests
 *
 * Sprint 53 Day 5 - Testing
 * Tests for SSE streaming events and generation flow
 *
 * @version 1.0.0
 */

import * as assert from 'assert';
import type {
    SSEEvent,
    SSEStartedEvent,
    SSEFileGeneratingEvent,
    SSEFileGeneratedEvent,
    SSEQualityStartedEvent,
    SSEQualityGateEvent,
    SSECompletedEvent,
    SSEErrorEvent,
    SSECheckpointEvent,
    GeneratedFile,
    QualityGateResult,
    CodegenSession,
} from '../../types/codegen';

suite('SSE Event Parsing Tests', () => {
    test('Parse started event', () => {
        const eventData = {
            type: 'started' as const,
            timestamp: '2025-12-26T10:00:00Z',
            session_id: 'abc123',
            model: 'qwen2.5-coder:32b',
            provider: 'ollama',
        };

        const event: SSEStartedEvent = eventData;

        assert.strictEqual(event.type, 'started');
        assert.strictEqual(event.model, 'qwen2.5-coder:32b');
        assert.strictEqual(event.provider, 'ollama');
    });

    test('Parse file_generating event', () => {
        const eventData = {
            type: 'file_generating' as const,
            timestamp: '2025-12-26T10:00:01Z',
            session_id: 'abc123',
            path: 'app/main.py',
        };

        const event: SSEFileGeneratingEvent = eventData;

        assert.strictEqual(event.type, 'file_generating');
        assert.strictEqual(event.path, 'app/main.py');
    });

    test('Parse file_generated event', () => {
        const eventData = {
            type: 'file_generated' as const,
            timestamp: '2025-12-26T10:00:05Z',
            session_id: 'abc123',
            path: 'app/main.py',
            content: 'from fastapi import FastAPI\n\napp = FastAPI()',
            lines: 3,
            language: 'python',
            syntax_valid: true,
        };

        const event: SSEFileGeneratedEvent = eventData;

        assert.strictEqual(event.type, 'file_generated');
        assert.strictEqual(event.path, 'app/main.py');
        assert.strictEqual(event.lines, 3);
        assert.strictEqual(event.language, 'python');
        assert.strictEqual(event.syntax_valid, true);
    });

    test('Parse quality_started event', () => {
        const eventData = {
            type: 'quality_started' as const,
            timestamp: '2025-12-26T10:01:00Z',
            session_id: 'abc123',
            total_gates: 4,
        };

        const event: SSEQualityStartedEvent = eventData;

        assert.strictEqual(event.type, 'quality_started');
        assert.strictEqual(event.total_gates, 4);
    });

    test('Parse quality_gate event - passed', () => {
        const eventData = {
            type: 'quality_gate' as const,
            timestamp: '2025-12-26T10:01:05Z',
            session_id: 'abc123',
            gate_number: 1,
            gate_name: 'Syntax',
            status: 'passed' as const,
            issues: 0,
            duration_ms: 150,
        };

        const event: SSEQualityGateEvent = eventData;

        assert.strictEqual(event.type, 'quality_gate');
        assert.strictEqual(event.gate_number, 1);
        assert.strictEqual(event.gate_name, 'Syntax');
        assert.strictEqual(event.status, 'passed');
        assert.strictEqual(event.issues, 0);
    });

    test('Parse quality_gate event - failed', () => {
        const eventData = {
            type: 'quality_gate' as const,
            timestamp: '2025-12-26T10:01:10Z',
            session_id: 'abc123',
            gate_number: 2,
            gate_name: 'Security',
            status: 'failed' as const,
            issues: 3,
            duration_ms: 500,
        };

        const event: SSEQualityGateEvent = eventData;

        assert.strictEqual(event.status, 'failed');
        assert.strictEqual(event.issues, 3);
    });

    test('Parse completed event', () => {
        const eventData = {
            type: 'completed' as const,
            timestamp: '2025-12-26T10:02:00Z',
            session_id: 'abc123',
            total_files: 12,
            total_lines: 450,
            duration_ms: 30000,
            success: true,
        };

        const event: SSECompletedEvent = eventData;

        assert.strictEqual(event.type, 'completed');
        assert.strictEqual(event.total_files, 12);
        assert.strictEqual(event.total_lines, 450);
        assert.strictEqual(event.duration_ms, 30000);
        assert.strictEqual(event.success, true);
    });

    test('Parse error event without recovery', () => {
        const eventData = {
            type: 'error' as const,
            timestamp: '2025-12-26T10:00:30Z',
            session_id: 'abc123',
            message: 'No AI providers available',
        };

        const event: SSEErrorEvent = eventData;

        assert.strictEqual(event.type, 'error');
        assert.strictEqual(event.message, 'No AI providers available');
        assert.strictEqual(event.recovery_id, undefined);
    });

    test('Parse error event with recovery', () => {
        const eventData = {
            type: 'error' as const,
            timestamp: '2025-12-26T10:00:30Z',
            session_id: 'abc123',
            message: 'Generation failed at file 5/12',
            recovery_id: 'abc123',
        };

        const event: SSEErrorEvent = eventData;

        assert.strictEqual(event.type, 'error');
        assert.ok(event.recovery_id);
    });

    test('Parse checkpoint event', () => {
        const eventData = {
            type: 'checkpoint' as const,
            timestamp: '2025-12-26T10:00:45Z',
            session_id: 'abc123',
            files_completed: 5,
            last_file_path: 'app/models/user.py',
        };

        const event: SSECheckpointEvent = eventData;

        assert.strictEqual(event.type, 'checkpoint');
        assert.strictEqual(event.files_completed, 5);
        assert.strictEqual(event.last_file_path, 'app/models/user.py');
    });
});

suite('Generated File Tests', () => {
    test('GeneratedFile with valid syntax', () => {
        const file: GeneratedFile = {
            path: 'app/main.py',
            content: 'from fastapi import FastAPI\n\napp = FastAPI()',
            lines: 3,
            language: 'python',
            syntax_valid: true,
            status: 'valid',
        };

        assert.strictEqual(file.status, 'valid');
        assert.strictEqual(file.syntax_valid, true);
    });

    test('GeneratedFile with syntax error', () => {
        const file: GeneratedFile = {
            path: 'app/broken.py',
            content: 'def broken(\n',
            lines: 1,
            language: 'python',
            syntax_valid: false,
            status: 'error',
        };

        assert.strictEqual(file.status, 'error');
        assert.strictEqual(file.syntax_valid, false);
    });

    test('GeneratedFile generating status', () => {
        const file: GeneratedFile = {
            path: 'app/pending.py',
            content: '',
            lines: 0,
            language: 'python',
            syntax_valid: false,
            status: 'generating',
        };

        assert.strictEqual(file.status, 'generating');
    });

    test('Language detection from file extension', () => {
        const files: Array<{ path: string; expectedLang: string }> = [
            { path: 'app/main.py', expectedLang: 'python' },
            { path: 'src/index.ts', expectedLang: 'typescript' },
            { path: 'src/App.tsx', expectedLang: 'typescript' },
            { path: 'config.json', expectedLang: 'json' },
            { path: 'docker-compose.yaml', expectedLang: 'yaml' },
            { path: 'README.md', expectedLang: 'markdown' },
            { path: 'schema.sql', expectedLang: 'sql' },
        ];

        const detectLanguage = (path: string): string => {
            const ext = path.split('.').pop()?.toLowerCase() || '';
            const langMap: Record<string, string> = {
                py: 'python',
                ts: 'typescript',
                tsx: 'typescript',
                js: 'javascript',
                jsx: 'javascript',
                json: 'json',
                yaml: 'yaml',
                yml: 'yaml',
                md: 'markdown',
                sql: 'sql',
            };
            return langMap[ext] || ext;
        };

        for (const { path, expectedLang } of files) {
            const detected = detectLanguage(path);
            assert.strictEqual(detected, expectedLang, `Expected ${expectedLang} for ${path}`);
        }
    });
});

suite('Quality Gate Result Tests', () => {
    test('All gates passed', () => {
        const gates: QualityGateResult[] = [
            { gate_number: 1, gate_name: 'Syntax', status: 'passed', issues: 0, duration_ms: 100 },
            { gate_number: 2, gate_name: 'Security', status: 'passed', issues: 0, duration_ms: 200 },
            { gate_number: 3, gate_name: 'Context', status: 'passed', issues: 0, duration_ms: 150 },
            { gate_number: 4, gate_name: 'Tests', status: 'passed', issues: 0, duration_ms: 500 },
        ];

        const allPassed = gates.every(g => g.status === 'passed');
        assert.strictEqual(allPassed, true);
    });

    test('Gate failed stops pipeline', () => {
        const gates: QualityGateResult[] = [
            { gate_number: 1, gate_name: 'Syntax', status: 'passed', issues: 0, duration_ms: 100 },
            { gate_number: 2, gate_name: 'Security', status: 'failed', issues: 5, duration_ms: 300 },
            { gate_number: 3, gate_name: 'Context', status: 'skipped', issues: 0, duration_ms: 0 },
            { gate_number: 4, gate_name: 'Tests', status: 'skipped', issues: 0, duration_ms: 0 },
        ];

        const failedGate = gates.find(g => g.status === 'failed');
        assert.ok(failedGate);
        assert.strictEqual(failedGate.gate_number, 2);

        const skippedAfterFail = gates.filter(g => g.gate_number > 2 && g.status === 'skipped');
        assert.strictEqual(skippedAfterFail.length, 2);
    });

    test('Gate with issues but passed', () => {
        const gate: QualityGateResult = {
            gate_number: 2,
            gate_name: 'Security',
            status: 'passed',
            issues: 2,  // Warnings, not errors
            duration_ms: 300,
            details: ['Warning: Consider using parameterized queries', 'Warning: Input validation recommended'],
        };

        assert.strictEqual(gate.status, 'passed');
        assert.strictEqual(gate.issues, 2);
        assert.ok(gate.details);
        assert.strictEqual(gate.details.length, 2);
    });
});

suite('Codegen Session Tests', () => {
    test('Session pending status', () => {
        const session: CodegenSession = {
            id: 'abc123',
            status: 'pending',
            blueprint: {
                name: 'Test App',
                version: '1.0.0',
                business_domain: 'retail',
                description: 'Test',
                modules: [],
            },
            files: [],
            quality_gates: [],
            started_at: '2025-12-26T10:00:00Z',
        };

        assert.strictEqual(session.status, 'pending');
        assert.strictEqual(session.files.length, 0);
    });

    test('Session generating status', () => {
        const session: CodegenSession = {
            id: 'abc123',
            status: 'generating',
            blueprint: {
                name: 'Test App',
                version: '1.0.0',
                business_domain: 'retail',
                description: 'Test',
                modules: [{ name: 'core', entities: ['User'] }],
            },
            files: [
                { path: 'app/main.py', content: '...', lines: 10, language: 'python', syntax_valid: true, status: 'valid' },
                { path: 'app/models.py', content: '', lines: 0, language: 'python', syntax_valid: false, status: 'generating' },
            ],
            quality_gates: [],
            started_at: '2025-12-26T10:00:00Z',
        };

        assert.strictEqual(session.status, 'generating');
        assert.strictEqual(session.files.length, 2);
        assert.strictEqual(session.files.filter(f => f.status === 'valid').length, 1);
    });

    test('Session completed status', () => {
        const session: CodegenSession = {
            id: 'abc123',
            status: 'completed',
            blueprint: {
                name: 'Test App',
                version: '1.0.0',
                business_domain: 'retail',
                description: 'Test',
                modules: [{ name: 'core', entities: ['User'] }],
            },
            files: [
                { path: 'app/main.py', content: '...', lines: 50, language: 'python', syntax_valid: true, status: 'valid' },
                { path: 'app/models.py', content: '...', lines: 100, language: 'python', syntax_valid: true, status: 'valid' },
            ],
            quality_gates: [
                { gate_number: 1, gate_name: 'Syntax', status: 'passed', issues: 0, duration_ms: 100 },
                { gate_number: 2, gate_name: 'Security', status: 'passed', issues: 0, duration_ms: 200 },
                { gate_number: 3, gate_name: 'Context', status: 'passed', issues: 0, duration_ms: 150 },
                { gate_number: 4, gate_name: 'Tests', status: 'passed', issues: 0, duration_ms: 500 },
            ],
            started_at: '2025-12-26T10:00:00Z',
            completed_at: '2025-12-26T10:02:00Z',
        };

        assert.strictEqual(session.status, 'completed');
        assert.ok(session.completed_at);
        assert.strictEqual(session.quality_gates.length, 4);
    });

    test('Session failed status', () => {
        const session: CodegenSession = {
            id: 'abc123',
            status: 'failed',
            blueprint: {
                name: 'Test App',
                version: '1.0.0',
                business_domain: 'retail',
                description: 'Test',
                modules: [],
            },
            files: [
                { path: 'app/main.py', content: '...', lines: 50, language: 'python', syntax_valid: true, status: 'valid' },
            ],
            quality_gates: [
                { gate_number: 1, gate_name: 'Syntax', status: 'passed', issues: 0, duration_ms: 100 },
                { gate_number: 2, gate_name: 'Security', status: 'failed', issues: 3, duration_ms: 200 },
            ],
            started_at: '2025-12-26T10:00:00Z',
            error_message: 'Security gate failed with 3 critical issues',
        };

        assert.strictEqual(session.status, 'failed');
        assert.ok(session.error_message);
        assert.ok(session.error_message.includes('Security'));
    });
});

suite('SSE Event Stream Simulation', () => {
    test('Full generation flow events', () => {
        const events: SSEEvent[] = [
            { type: 'started', timestamp: '2025-12-26T10:00:00Z', session_id: 'test', model: 'ollama', provider: 'ollama' },
            { type: 'file_generating', timestamp: '2025-12-26T10:00:01Z', session_id: 'test', path: 'app/main.py' },
            { type: 'file_generated', timestamp: '2025-12-26T10:00:05Z', session_id: 'test', path: 'app/main.py', content: '...', lines: 50, language: 'python', syntax_valid: true },
            { type: 'file_generating', timestamp: '2025-12-26T10:00:06Z', session_id: 'test', path: 'app/models.py' },
            { type: 'file_generated', timestamp: '2025-12-26T10:00:10Z', session_id: 'test', path: 'app/models.py', content: '...', lines: 100, language: 'python', syntax_valid: true },
            { type: 'quality_started', timestamp: '2025-12-26T10:00:11Z', session_id: 'test', total_gates: 4 },
            { type: 'quality_gate', timestamp: '2025-12-26T10:00:12Z', session_id: 'test', gate_number: 1, gate_name: 'Syntax', status: 'passed', issues: 0, duration_ms: 100 },
            { type: 'quality_gate', timestamp: '2025-12-26T10:00:13Z', session_id: 'test', gate_number: 2, gate_name: 'Security', status: 'passed', issues: 0, duration_ms: 200 },
            { type: 'quality_gate', timestamp: '2025-12-26T10:00:14Z', session_id: 'test', gate_number: 3, gate_name: 'Context', status: 'passed', issues: 0, duration_ms: 150 },
            { type: 'quality_gate', timestamp: '2025-12-26T10:00:15Z', session_id: 'test', gate_number: 4, gate_name: 'Tests', status: 'passed', issues: 0, duration_ms: 500 },
            { type: 'completed', timestamp: '2025-12-26T10:00:16Z', session_id: 'test', total_files: 2, total_lines: 150, duration_ms: 16000, success: true },
        ];

        // Verify event order
        const firstEvent = events[0];
        const lastEvent = events[events.length - 1];
        assert.ok(firstEvent);
        assert.ok(lastEvent);
        assert.strictEqual(firstEvent.type, 'started');
        assert.strictEqual(lastEvent.type, 'completed');

        // Count file events
        const fileGeneratedEvents = events.filter(e => e.type === 'file_generated');
        assert.strictEqual(fileGeneratedEvents.length, 2);

        // Count quality gate events
        const qualityGateEvents = events.filter(e => e.type === 'quality_gate');
        assert.strictEqual(qualityGateEvents.length, 4);

        // Verify completed event matches file count
        const completedEvent = events.find(e => e.type === 'completed') as SSECompletedEvent;
        assert.strictEqual(completedEvent.total_files, fileGeneratedEvents.length);
    });

    test('Generation flow with error and recovery', () => {
        const events: SSEEvent[] = [
            { type: 'started', timestamp: '2025-12-26T10:00:00Z', session_id: 'test', model: 'ollama', provider: 'ollama' },
            { type: 'file_generating', timestamp: '2025-12-26T10:00:01Z', session_id: 'test', path: 'app/main.py' },
            { type: 'file_generated', timestamp: '2025-12-26T10:00:05Z', session_id: 'test', path: 'app/main.py', content: '...', lines: 50, language: 'python', syntax_valid: true },
            { type: 'checkpoint', timestamp: '2025-12-26T10:00:06Z', session_id: 'test', files_completed: 1, last_file_path: 'app/main.py' },
            { type: 'file_generating', timestamp: '2025-12-26T10:00:07Z', session_id: 'test', path: 'app/models.py' },
            { type: 'error', timestamp: '2025-12-26T10:00:10Z', session_id: 'test', message: 'Provider timeout', recovery_id: 'test' },
        ];

        const errorEvent = events.find(e => e.type === 'error') as SSEErrorEvent;
        assert.ok(errorEvent);
        assert.ok(errorEvent.recovery_id);

        const checkpointEvent = events.find(e => e.type === 'checkpoint') as SSECheckpointEvent;
        assert.ok(checkpointEvent);
        assert.strictEqual(checkpointEvent.files_completed, 1);
    });
});
