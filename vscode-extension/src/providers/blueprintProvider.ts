/**
 * Blueprint Tree Data Provider
 *
 * Provides hierarchical view of App Blueprint structure
 * for the VS Code sidebar tree view.
 *
 * Sprint 53 Day 2 - Blueprint Provider Implementation
 * @version 1.0.0
 */

import * as vscode from 'vscode';
import { Logger } from '../utils/logger';
import type { AppBlueprint, BlueprintModule } from '../types/codegen';

/**
 * Blueprint tree item types
 */
export type BlueprintNodeType = 'blueprint' | 'module' | 'entity' | 'metadata';

/**
 * Blueprint tree item
 */
export class BlueprintTreeItem extends vscode.TreeItem {
    constructor(
        public readonly label: string,
        public readonly collapsibleState: vscode.TreeItemCollapsibleState,
        public readonly nodeType: BlueprintNodeType,
        public readonly data?: AppBlueprint | BlueprintModule | string,
        public readonly parent?: BlueprintTreeItem
    ) {
        super(label, collapsibleState);

        this.contextValue = nodeType;
        this.iconPath = this.getIconForType(nodeType);
        this.tooltip = this.getTooltipForType(nodeType);
    }

    /**
     * Get icon for node type
     */
    private getIconForType(nodeType: BlueprintNodeType): vscode.ThemeIcon {
        switch (nodeType) {
            case 'blueprint':
                return new vscode.ThemeIcon('package', new vscode.ThemeColor('charts.blue'));
            case 'module':
                return new vscode.ThemeIcon('folder', new vscode.ThemeColor('charts.yellow'));
            case 'entity':
                return new vscode.ThemeIcon('symbol-class', new vscode.ThemeColor('charts.green'));
            case 'metadata':
                return new vscode.ThemeIcon('info', new vscode.ThemeColor('charts.gray'));
            default:
                return new vscode.ThemeIcon('circle-outline');
        }
    }

    /**
     * Get tooltip for node type
     */
    private getTooltipForType(nodeType: BlueprintNodeType): string {
        switch (nodeType) {
            case 'blueprint':
                const bp = this.data as AppBlueprint;
                return bp ? `${bp.name} v${bp.version}\n${bp.description || ''}` : 'App Blueprint';
            case 'module':
                const mod = this.data as BlueprintModule;
                return mod ? `Module: ${mod.name}\nEntities: ${mod.entities.length}` : 'Module';
            case 'entity':
                return `Entity: ${this.label}`;
            case 'metadata':
                return `Metadata: ${this.label}`;
            default:
                return this.label;
        }
    }
}

/**
 * Blueprint Tree Data Provider
 *
 * Manages the hierarchical tree view of the App Blueprint structure.
 */
export class BlueprintProvider implements vscode.TreeDataProvider<BlueprintTreeItem> {
    private _onDidChangeTreeData = new vscode.EventEmitter<BlueprintTreeItem | undefined | null | void>();
    readonly onDidChangeTreeData = this._onDidChangeTreeData.event;

    private _blueprint: AppBlueprint | undefined;
    private _isLocked = false;

    constructor() {
        Logger.info('BlueprintProvider initialized');
    }

    /**
     * Set the current blueprint
     */
    public setBlueprint(blueprint: AppBlueprint | undefined): void {
        this._blueprint = blueprint;
        this.refresh();
    }

    /**
     * Get the current blueprint
     */
    public getBlueprint(): AppBlueprint | undefined {
        return this._blueprint;
    }

    /**
     * Set lock status
     */
    public setLocked(locked: boolean): void {
        this._isLocked = locked;
        this.refresh();
    }

    /**
     * Check if blueprint is locked
     */
    public isLocked(): boolean {
        return this._isLocked;
    }

    /**
     * Refresh the tree view
     */
    public refresh(): void {
        this._onDidChangeTreeData.fire();
    }

    /**
     * Clear the tree view
     */
    public clear(): void {
        this._blueprint = undefined;
        this._isLocked = false;
        this.refresh();
    }

    /**
     * Get tree item
     */
    getTreeItem(element: BlueprintTreeItem): vscode.TreeItem {
        return element;
    }

    /**
     * Get children for a tree item
     */
    getChildren(element?: BlueprintTreeItem): Thenable<BlueprintTreeItem[]> {
        if (!this._blueprint) {
            return Promise.resolve([
                new BlueprintTreeItem(
                    'No blueprint loaded',
                    vscode.TreeItemCollapsibleState.None,
                    'metadata'
                ),
            ]);
        }

        if (!element) {
            // Root level - show blueprint
            return Promise.resolve(this.getRootItems());
        }

        // Get children based on node type
        switch (element.nodeType) {
            case 'blueprint':
                return Promise.resolve(this.getModuleItems(element));
            case 'module':
                return Promise.resolve(this.getEntityItems(element));
            default:
                return Promise.resolve([]);
        }
    }

    /**
     * Get parent of a tree item
     */
    getParent(element: BlueprintTreeItem): vscode.ProviderResult<BlueprintTreeItem> {
        return element.parent;
    }

    /**
     * Get root items (blueprint info)
     */
    private getRootItems(): BlueprintTreeItem[] {
        if (!this._blueprint) {
            return [];
        }

        const items: BlueprintTreeItem[] = [];

        // Blueprint root node
        const blueprintNode = new BlueprintTreeItem(
            `${this._blueprint.name} ${this._isLocked ? '🔒' : ''}`,
            vscode.TreeItemCollapsibleState.Expanded,
            'blueprint',
            this._blueprint
        );
        blueprintNode.description = `v${this._blueprint.version} | ${this._blueprint.business_domain}`;
        items.push(blueprintNode);

        return items;
    }

    /**
     * Get module items
     */
    private getModuleItems(parent: BlueprintTreeItem): BlueprintTreeItem[] {
        if (!this._blueprint) {
            return [];
        }

        return this._blueprint.modules.map(module => {
            const item = new BlueprintTreeItem(
                module.name,
                vscode.TreeItemCollapsibleState.Collapsed,
                'module',
                module,
                parent
            );
            item.description = `${module.entities.length} entities`;
            if (module.description) {
                item.tooltip = `${module.name}\n${module.description}\nEntities: ${module.entities.join(', ')}`;
            }
            return item;
        });
    }

    /**
     * Get entity items for a module
     */
    private getEntityItems(parent: BlueprintTreeItem): BlueprintTreeItem[] {
        const module = parent.data as BlueprintModule;
        if (!module || !module.entities) {
            return [];
        }

        return module.entities.map(entity => {
            const item = new BlueprintTreeItem(
                entity,
                vscode.TreeItemCollapsibleState.None,
                'entity',
                entity,
                parent
            );
            return item;
        });
    }

    // ========================================
    // Blueprint Modification Methods
    // ========================================

    /**
     * Add a new module to the blueprint
     */
    public addModule(name: string, description?: string): boolean {
        if (!this._blueprint || this._isLocked) {
            return false;
        }

        // Check for duplicate
        if (this._blueprint.modules.some(m => m.name === name)) {
            return false;
        }

        this._blueprint.modules.push({
            name,
            entities: [],
            description: description || '',
        });

        this.refresh();
        return true;
    }

    /**
     * Remove a module from the blueprint
     */
    public removeModule(moduleName: string): boolean {
        if (!this._blueprint || this._isLocked) {
            return false;
        }

        const index = this._blueprint.modules.findIndex(m => m.name === moduleName);
        if (index === -1) {
            return false;
        }

        this._blueprint.modules.splice(index, 1);
        this.refresh();
        return true;
    }

    /**
     * Add an entity to a module
     */
    public addEntity(moduleName: string, entityName: string): boolean {
        if (!this._blueprint || this._isLocked) {
            return false;
        }

        const module = this._blueprint.modules.find(m => m.name === moduleName);
        if (!module) {
            return false;
        }

        // Check for duplicate
        if (module.entities.includes(entityName)) {
            return false;
        }

        module.entities.push(entityName);
        this.refresh();
        return true;
    }

    /**
     * Remove an entity from a module
     */
    public removeEntity(moduleName: string, entityName: string): boolean {
        if (!this._blueprint || this._isLocked) {
            return false;
        }

        const module = this._blueprint.modules.find(m => m.name === moduleName);
        if (!module) {
            return false;
        }

        const index = module.entities.indexOf(entityName);
        if (index === -1) {
            return false;
        }

        module.entities.splice(index, 1);
        this.refresh();
        return true;
    }

    /**
     * Rename a module
     */
    public renameModule(oldName: string, newName: string): boolean {
        if (!this._blueprint || this._isLocked) {
            return false;
        }

        const module = this._blueprint.modules.find(m => m.name === oldName);
        if (!module) {
            return false;
        }

        // Check for duplicate
        if (this._blueprint.modules.some(m => m.name === newName)) {
            return false;
        }

        module.name = newName;
        this.refresh();
        return true;
    }

    /**
     * Rename an entity
     */
    public renameEntity(moduleName: string, oldName: string, newName: string): boolean {
        if (!this._blueprint || this._isLocked) {
            return false;
        }

        const module = this._blueprint.modules.find(m => m.name === moduleName);
        if (!module) {
            return false;
        }

        const index = module.entities.indexOf(oldName);
        if (index === -1) {
            return false;
        }

        // Check for duplicate
        if (module.entities.includes(newName)) {
            return false;
        }

        module.entities[index] = newName;
        this.refresh();
        return true;
    }

    /**
     * Update blueprint metadata
     */
    public updateMetadata(updates: Partial<Pick<AppBlueprint, 'name' | 'version' | 'description' | 'business_domain'>>): boolean {
        if (!this._blueprint || this._isLocked) {
            return false;
        }

        if (updates.name !== undefined) {
            this._blueprint.name = updates.name;
        }
        if (updates.version !== undefined) {
            this._blueprint.version = updates.version;
        }
        if (updates.description !== undefined) {
            this._blueprint.description = updates.description;
        }
        if (updates.business_domain !== undefined) {
            this._blueprint.business_domain = updates.business_domain;
        }

        this.refresh();
        return true;
    }
}

/**
 * Register blueprint tree view commands
 */
export function registerBlueprintCommands(
    context: vscode.ExtensionContext,
    provider: BlueprintProvider
): void {
    // Add module command
    context.subscriptions.push(
        vscode.commands.registerCommand('sdlc.blueprint.addModule', async () => {
            if (provider.isLocked()) {
                void vscode.window.showWarningMessage('Blueprint is locked. Unlock to make changes.');
                return;
            }

            const name = await vscode.window.showInputBox({
                prompt: 'Enter module name',
                placeHolder: 'e.g., users, products, orders',
                validateInput: (value) => {
                    if (!value || value.trim().length === 0) {
                        return 'Module name is required';
                    }
                    if (!/^[a-z][a-z0-9_]*$/.test(value.trim())) {
                        return 'Module name must be lowercase with underscores only';
                    }
                    return null;
                },
            });

            if (name) {
                const description = await vscode.window.showInputBox({
                    prompt: 'Enter module description (optional)',
                    placeHolder: 'e.g., User management module',
                });

                if (provider.addModule(name.trim(), description?.trim())) {
                    void vscode.window.showInformationMessage(`Module "${name}" added`);
                } else {
                    void vscode.window.showErrorMessage(`Failed to add module "${name}"`);
                }
            }
        })
    );

    // Remove module command
    context.subscriptions.push(
        vscode.commands.registerCommand('sdlc.blueprint.removeModule', async (item?: BlueprintTreeItem) => {
            if (provider.isLocked()) {
                void vscode.window.showWarningMessage('Blueprint is locked. Unlock to make changes.');
                return;
            }

            let moduleName = item?.nodeType === 'module' ? item.label : undefined;

            if (!moduleName) {
                const blueprint = provider.getBlueprint();
                if (!blueprint || blueprint.modules.length === 0) {
                    void vscode.window.showInformationMessage('No modules to remove');
                    return;
                }

                const selected = await vscode.window.showQuickPick(
                    blueprint.modules.map(m => m.name),
                    { placeHolder: 'Select module to remove' }
                );
                moduleName = selected;
            }

            if (moduleName) {
                const confirm = await vscode.window.showWarningMessage(
                    `Remove module "${moduleName}" and all its entities?`,
                    { modal: true },
                    'Remove',
                    'Cancel'
                );

                if (confirm === 'Remove') {
                    if (provider.removeModule(moduleName)) {
                        void vscode.window.showInformationMessage(`Module "${moduleName}" removed`);
                    } else {
                        void vscode.window.showErrorMessage(`Failed to remove module "${moduleName}"`);
                    }
                }
            }
        })
    );

    // Add entity command
    context.subscriptions.push(
        vscode.commands.registerCommand('sdlc.blueprint.addEntity', async (item?: BlueprintTreeItem) => {
            if (provider.isLocked()) {
                void vscode.window.showWarningMessage('Blueprint is locked. Unlock to make changes.');
                return;
            }

            let moduleName = item?.nodeType === 'module' ? item.label : undefined;

            if (!moduleName) {
                const blueprint = provider.getBlueprint();
                if (!blueprint || blueprint.modules.length === 0) {
                    void vscode.window.showInformationMessage('No modules available. Add a module first.');
                    return;
                }

                const selected = await vscode.window.showQuickPick(
                    blueprint.modules.map(m => m.name),
                    { placeHolder: 'Select module to add entity to' }
                );
                moduleName = selected;
            }

            if (moduleName) {
                const entityName = await vscode.window.showInputBox({
                    prompt: `Enter entity name for module "${moduleName}"`,
                    placeHolder: 'e.g., User, Product, Order',
                    validateInput: (value) => {
                        if (!value || value.trim().length === 0) {
                            return 'Entity name is required';
                        }
                        if (!/^[A-Z][a-zA-Z0-9]*$/.test(value.trim())) {
                            return 'Entity name must be PascalCase';
                        }
                        return null;
                    },
                });

                if (entityName) {
                    if (provider.addEntity(moduleName, entityName.trim())) {
                        void vscode.window.showInformationMessage(`Entity "${entityName}" added to "${moduleName}"`);
                    } else {
                        void vscode.window.showErrorMessage(`Failed to add entity "${entityName}"`);
                    }
                }
            }
        })
    );

    // Remove entity command
    context.subscriptions.push(
        vscode.commands.registerCommand('sdlc.blueprint.removeEntity', async (item?: BlueprintTreeItem) => {
            if (provider.isLocked()) {
                void vscode.window.showWarningMessage('Blueprint is locked. Unlock to make changes.');
                return;
            }

            if (item?.nodeType === 'entity' && item.parent?.nodeType === 'module') {
                const moduleName = item.parent.label;
                const entityName = item.label;

                const confirm = await vscode.window.showWarningMessage(
                    `Remove entity "${entityName}" from "${moduleName}"?`,
                    { modal: true },
                    'Remove',
                    'Cancel'
                );

                if (confirm === 'Remove') {
                    if (provider.removeEntity(moduleName, entityName)) {
                        void vscode.window.showInformationMessage(`Entity "${entityName}" removed`);
                    } else {
                        void vscode.window.showErrorMessage(`Failed to remove entity "${entityName}"`);
                    }
                }
            }
        })
    );

    // Edit blueprint metadata command
    context.subscriptions.push(
        vscode.commands.registerCommand('sdlc.blueprint.editMetadata', async () => {
            if (provider.isLocked()) {
                void vscode.window.showWarningMessage('Blueprint is locked. Unlock to make changes.');
                return;
            }

            const blueprint = provider.getBlueprint();
            if (!blueprint) {
                void vscode.window.showInformationMessage('No blueprint loaded');
                return;
            }

            const name = await vscode.window.showInputBox({
                prompt: 'Enter application name',
                value: blueprint.name,
                validateInput: (value) => {
                    if (!value || value.trim().length === 0) {
                        return 'Name is required';
                    }
                    return null;
                },
            });

            if (name !== undefined) {
                const version = await vscode.window.showInputBox({
                    prompt: 'Enter version',
                    value: blueprint.version,
                    validateInput: (value) => {
                        if (!value || !/^\d+\.\d+\.\d+$/.test(value.trim())) {
                            return 'Version must be in format X.Y.Z';
                        }
                        return null;
                    },
                });

                if (version !== undefined) {
                    const description = await vscode.window.showInputBox({
                        prompt: 'Enter description',
                        value: blueprint.description,
                    });

                    if (description !== undefined) {
                        provider.updateMetadata({
                            name: name.trim(),
                            version: version.trim(),
                            description: description.trim(),
                        });
                        void vscode.window.showInformationMessage('Blueprint metadata updated');
                    }
                }
            }
        })
    );

    Logger.info('Blueprint commands registered');
}
