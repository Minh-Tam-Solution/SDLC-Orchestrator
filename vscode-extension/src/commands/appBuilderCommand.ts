/**
 * App Builder Command - Open App Builder Panel
 *
 * Implements the sdlc.openAppBuilder command for opening
 * the main App Builder webview panel.
 *
 * Sprint 53 Day 1 - App Builder Command Implementation
 * @version 1.0.0
 */

import * as vscode from 'vscode';
import { Logger } from '../utils/logger';
import type { CodegenApiService } from '../services/codegenApi';

/**
 * App Builder Panel singleton
 */
let appBuilderPanel: vscode.WebviewPanel | undefined;

/**
 * Register the app builder command
 */
export function registerAppBuilderCommand(
    context: vscode.ExtensionContext,
    codegenApi: CodegenApiService
): void {
    const command = vscode.commands.registerCommand(
        'sdlc.openAppBuilder',
        async () => {
            await openAppBuilder(context, codegenApi);
        }
    );
    context.subscriptions.push(command);
    Logger.info('App Builder command registered');
}

/**
 * Open the App Builder panel
 */
async function openAppBuilder(
    context: vscode.ExtensionContext,
    codegenApi: CodegenApiService
): Promise<void> {
    // If panel exists, reveal it
    if (appBuilderPanel) {
        appBuilderPanel.reveal(vscode.ViewColumn.One);
        return;
    }

    // Create new panel
    appBuilderPanel = vscode.window.createWebviewPanel(
        'sdlc.appBuilder',
        '🏗️ SDLC App Builder',
        vscode.ViewColumn.One,
        {
            enableScripts: true,
            retainContextWhenHidden: true,
            localResourceRoots: [
                vscode.Uri.joinPath(context.extensionUri, 'media'),
            ],
        }
    );

    // Set icon
    appBuilderPanel.iconPath = {
        light: vscode.Uri.joinPath(context.extensionUri, 'media', 'sdlc-icon.svg'),
        dark: vscode.Uri.joinPath(context.extensionUri, 'media', 'sdlc-icon.svg'),
    };

    // Set HTML content
    appBuilderPanel.webview.html = getAppBuilderHtml(appBuilderPanel.webview, context.extensionUri);

    // Handle panel disposal
    appBuilderPanel.onDidDispose(() => {
        appBuilderPanel = undefined;
    });

    // Handle messages from webview
    appBuilderPanel.webview.onDidReceiveMessage(
        async (message: { command: string; payload?: unknown }) => {
            switch (message.command) {
                case 'generate':
                    await vscode.commands.executeCommand('sdlc.generate');
                    break;
                case 'magic':
                    await vscode.commands.executeCommand('sdlc.magic');
                    break;
                case 'preview':
                    await vscode.commands.executeCommand('sdlc.preview', message.payload);
                    break;
                case 'lock':
                    await vscode.commands.executeCommand('sdlc.lock', message.payload);
                    break;
                case 'unlock':
                    await vscode.commands.executeCommand('sdlc.unlock', message.payload);
                    break;
                case 'loadDomains':
                    await loadDomainTemplates(codegenApi, appBuilderPanel!);
                    break;
                case 'showInfo':
                    void vscode.window.showInformationMessage(message.payload as string);
                    break;
            }
        },
        undefined,
        context.subscriptions
    );

    // Load initial data
    await loadDomainTemplates(codegenApi, appBuilderPanel);
}

/**
 * Load domain templates
 */
async function loadDomainTemplates(
    codegenApi: CodegenApiService,
    panel: vscode.WebviewPanel
): Promise<void> {
    try {
        const templates = await codegenApi.getDomainTemplates();
        panel.webview.postMessage({
            command: 'domainsLoaded',
            payload: templates.domains,
        });
    } catch (error) {
        Logger.warn(`Failed to load domain templates: ${error}`);
        // Send default templates
        panel.webview.postMessage({
            command: 'domainsLoaded',
            payload: getDefaultDomains(),
        });
    }
}

/**
 * Get default domain templates
 */
function getDefaultDomains(): Array<{ id: string; name: string; description: string; modules: string[] }> {
    return [
        {
            id: 'ecommerce',
            name: 'E-commerce',
            description: 'Online store with products, orders, payments',
            modules: ['catalog', 'orders', 'customers', 'payments'],
        },
        {
            id: 'hrm',
            name: 'HRM',
            description: 'Human Resource Management system',
            modules: ['employees', 'attendance', 'payroll', 'recruitment'],
        },
        {
            id: 'crm',
            name: 'CRM',
            description: 'Customer Relationship Management',
            modules: ['contacts', 'deals', 'activities', 'reports'],
        },
        {
            id: 'lms',
            name: 'LMS',
            description: 'Learning Management System',
            modules: ['courses', 'students', 'assessments', 'certificates'],
        },
    ];
}

/**
 * Generate App Builder HTML
 */
function getAppBuilderHtml(webview: vscode.Webview, _extensionUri: vscode.Uri): string {
    const nonce = getNonce();

    return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src ${webview.cspSource} 'unsafe-inline'; script-src 'nonce-${nonce}';">
    <title>SDLC App Builder</title>
    <style>
        * {
            box-sizing: border-box;
        }
        body {
            font-family: var(--vscode-font-family);
            padding: 0;
            margin: 0;
            color: var(--vscode-foreground);
            background-color: var(--vscode-editor-background);
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        .header {
            text-align: center;
            padding: 30px 0;
            border-bottom: 1px solid var(--vscode-panel-border);
            margin-bottom: 30px;
        }
        .header h1 {
            font-size: 28px;
            margin: 0 0 10px 0;
        }
        .header p {
            color: var(--vscode-descriptionForeground);
            margin: 0;
        }
        .actions {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        .action-card {
            background-color: var(--vscode-editor-inactiveSelectionBackground);
            border: 1px solid var(--vscode-panel-border);
            border-radius: 8px;
            padding: 20px;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .action-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
            border-color: var(--vscode-focusBorder);
        }
        .action-card .icon {
            font-size: 32px;
            margin-bottom: 10px;
        }
        .action-card h3 {
            margin: 0 0 8px 0;
            font-size: 16px;
        }
        .action-card p {
            margin: 0;
            color: var(--vscode-descriptionForeground);
            font-size: 13px;
        }
        .action-card .shortcut {
            margin-top: 10px;
            font-size: 11px;
            color: var(--vscode-textLink-foreground);
        }
        .section-title {
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .domains {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 40px;
        }
        .domain-card {
            background-color: var(--vscode-textBlockQuote-background);
            border: 1px solid var(--vscode-panel-border);
            border-radius: 6px;
            padding: 15px;
            cursor: pointer;
        }
        .domain-card:hover {
            border-color: var(--vscode-focusBorder);
        }
        .domain-card.selected {
            border-color: var(--vscode-button-background);
            background-color: var(--vscode-editor-selectionBackground);
        }
        .domain-card h4 {
            margin: 0 0 5px 0;
            font-size: 14px;
        }
        .domain-card p {
            margin: 0;
            font-size: 12px;
            color: var(--vscode-descriptionForeground);
        }
        .domain-card .modules {
            margin-top: 8px;
            display: flex;
            flex-wrap: wrap;
            gap: 4px;
        }
        .domain-card .module-tag {
            background-color: var(--vscode-badge-background);
            color: var(--vscode-badge-foreground);
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 10px;
        }
        .quick-start {
            background-color: var(--vscode-textBlockQuote-background);
            border-radius: 8px;
            padding: 20px;
        }
        .quick-start h3 {
            margin: 0 0 15px 0;
        }
        .quick-start ol {
            margin: 0;
            padding-left: 20px;
        }
        .quick-start li {
            margin-bottom: 8px;
        }
        .footer {
            text-align: center;
            padding: 20px 0;
            color: var(--vscode-descriptionForeground);
            font-size: 12px;
            border-top: 1px solid var(--vscode-panel-border);
            margin-top: 40px;
        }
        .loading {
            text-align: center;
            padding: 20px;
            color: var(--vscode-descriptionForeground);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏗️ SDLC App Builder</h1>
            <p>Generate production-ready code from blueprints or natural language</p>
        </div>

        <div class="actions">
            <div class="action-card" id="btn-magic">
                <div class="icon">✨</div>
                <h3>Magic Mode</h3>
                <p>Describe your app in Vietnamese or English, AI generates the code</p>
                <div class="shortcut">Ctrl+Shift+M</div>
            </div>
            <div class="action-card" id="btn-generate">
                <div class="icon">📦</div>
                <h3>From Blueprint</h3>
                <p>Generate code from a structured JSON blueprint</p>
                <div class="shortcut">Ctrl+Shift+G</div>
            </div>
            <div class="action-card" id="btn-preview">
                <div class="icon">👁️</div>
                <h3>Preview</h3>
                <p>Preview generated code before saving to disk</p>
                <div class="shortcut">Ctrl+Shift+P</div>
            </div>
            <div class="action-card" id="btn-lock">
                <div class="icon">🔒</div>
                <h3>Lock Contract</h3>
                <p>Lock specification to prevent modifications</p>
                <div class="shortcut">Ctrl+Shift+L</div>
            </div>
        </div>

        <div class="section-title">📂 Domain Templates</div>
        <div class="domains" id="domains-container">
            <div class="loading">Loading templates...</div>
        </div>

        <div class="quick-start">
            <h3>🚀 Quick Start</h3>
            <ol>
                <li><strong>Magic Mode:</strong> Click "Magic Mode" and describe your app in plain language</li>
                <li><strong>Review:</strong> Check the detected domain and generated blueprint</li>
                <li><strong>Generate:</strong> Watch as code is generated in real-time with quality gates</li>
                <li><strong>Lock:</strong> Lock the contract spec when satisfied with the design</li>
            </ol>
        </div>

        <div class="footer">
            SDLC Orchestrator v1.0.0 | EP-06 Codegen Engine | Sprint 53
        </div>
    </div>

    <script nonce="${nonce}">
        const vscode = acquireVsCodeApi();

        // Action buttons
        document.getElementById('btn-magic').addEventListener('click', () => {
            vscode.postMessage({ command: 'magic' });
        });

        document.getElementById('btn-generate').addEventListener('click', () => {
            vscode.postMessage({ command: 'generate' });
        });

        document.getElementById('btn-preview').addEventListener('click', () => {
            vscode.postMessage({ command: 'preview' });
        });

        document.getElementById('btn-lock').addEventListener('click', () => {
            vscode.postMessage({ command: 'lock' });
        });

        // Handle messages from extension
        window.addEventListener('message', event => {
            const message = event.data;
            switch (message.command) {
                case 'domainsLoaded':
                    renderDomains(message.payload);
                    break;
            }
        });

        // Render domain templates
        function renderDomains(domains) {
            const container = document.getElementById('domains-container');
            container.innerHTML = domains.map(domain => \`
                <div class="domain-card" data-id="\${domain.id}">
                    <h4>\${domain.name}</h4>
                    <p>\${domain.description}</p>
                    <div class="modules">
                        \${domain.modules.map(m => \`<span class="module-tag">\${m}</span>\`).join('')}
                    </div>
                </div>
            \`).join('');

            // Add click handlers
            container.querySelectorAll('.domain-card').forEach(card => {
                card.addEventListener('click', () => {
                    const domainId = card.getAttribute('data-id');
                    vscode.postMessage({
                        command: 'showInfo',
                        payload: \`Selected domain: \${domainId}. Use Magic Mode or Generate to create an app.\`
                    });
                });
            });
        }

        // Request initial data
        vscode.postMessage({ command: 'loadDomains' });
    </script>
</body>
</html>`;
}

/**
 * Generate nonce for CSP
 */
function getNonce(): string {
    let text = '';
    const possible = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    for (let i = 0; i < 32; i++) {
        text += possible.charAt(Math.floor(Math.random() * possible.length));
    }
    return text;
}
