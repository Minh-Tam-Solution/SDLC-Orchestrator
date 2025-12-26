"use strict";
/**
 * Blueprint Tree Data Provider
 *
 * Provides hierarchical view of App Blueprint structure
 * for the VS Code sidebar tree view.
 *
 * Sprint 53 Day 2 - Blueprint Provider Implementation
 * @version 1.0.0
 */
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.BlueprintProvider = exports.BlueprintTreeItem = void 0;
exports.registerBlueprintCommands = registerBlueprintCommands;
const vscode = __importStar(require("vscode"));
const logger_1 = require("../utils/logger");
/**
 * Blueprint tree item
 */
class BlueprintTreeItem extends vscode.TreeItem {
    label;
    collapsibleState;
    nodeType;
    data;
    parent;
    constructor(label, collapsibleState, nodeType, data, parent) {
        super(label, collapsibleState);
        this.label = label;
        this.collapsibleState = collapsibleState;
        this.nodeType = nodeType;
        this.data = data;
        this.parent = parent;
        this.contextValue = nodeType;
        this.iconPath = this.getIconForType(nodeType);
        this.tooltip = this.getTooltipForType(nodeType);
    }
    /**
     * Get icon for node type
     */
    getIconForType(nodeType) {
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
    getTooltipForType(nodeType) {
        switch (nodeType) {
            case 'blueprint':
                const bp = this.data;
                return bp ? `${bp.name} v${bp.version}\n${bp.description || ''}` : 'App Blueprint';
            case 'module':
                const mod = this.data;
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
exports.BlueprintTreeItem = BlueprintTreeItem;
/**
 * Blueprint Tree Data Provider
 *
 * Manages the hierarchical tree view of the App Blueprint structure.
 */
class BlueprintProvider {
    _onDidChangeTreeData = new vscode.EventEmitter();
    onDidChangeTreeData = this._onDidChangeTreeData.event;
    _blueprint;
    _isLocked = false;
    constructor() {
        logger_1.Logger.info('BlueprintProvider initialized');
    }
    /**
     * Set the current blueprint
     */
    setBlueprint(blueprint) {
        this._blueprint = blueprint;
        this.refresh();
    }
    /**
     * Get the current blueprint
     */
    getBlueprint() {
        return this._blueprint;
    }
    /**
     * Set lock status
     */
    setLocked(locked) {
        this._isLocked = locked;
        this.refresh();
    }
    /**
     * Check if blueprint is locked
     */
    isLocked() {
        return this._isLocked;
    }
    /**
     * Refresh the tree view
     */
    refresh() {
        this._onDidChangeTreeData.fire();
    }
    /**
     * Clear the tree view
     */
    clear() {
        this._blueprint = undefined;
        this._isLocked = false;
        this.refresh();
    }
    /**
     * Get tree item
     */
    getTreeItem(element) {
        return element;
    }
    /**
     * Get children for a tree item
     */
    getChildren(element) {
        if (!this._blueprint) {
            return Promise.resolve([
                new BlueprintTreeItem('No blueprint loaded', vscode.TreeItemCollapsibleState.None, 'metadata'),
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
    getParent(element) {
        return element.parent;
    }
    /**
     * Get root items (blueprint info)
     */
    getRootItems() {
        if (!this._blueprint) {
            return [];
        }
        const items = [];
        // Blueprint root node
        const blueprintNode = new BlueprintTreeItem(`${this._blueprint.name} ${this._isLocked ? '🔒' : ''}`, vscode.TreeItemCollapsibleState.Expanded, 'blueprint', this._blueprint);
        blueprintNode.description = `v${this._blueprint.version} | ${this._blueprint.business_domain}`;
        items.push(blueprintNode);
        return items;
    }
    /**
     * Get module items
     */
    getModuleItems(parent) {
        if (!this._blueprint) {
            return [];
        }
        return this._blueprint.modules.map(module => {
            const item = new BlueprintTreeItem(module.name, vscode.TreeItemCollapsibleState.Collapsed, 'module', module, parent);
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
    getEntityItems(parent) {
        const module = parent.data;
        if (!module || !module.entities) {
            return [];
        }
        return module.entities.map(entity => {
            const item = new BlueprintTreeItem(entity, vscode.TreeItemCollapsibleState.None, 'entity', entity, parent);
            return item;
        });
    }
    // ========================================
    // Blueprint Modification Methods
    // ========================================
    /**
     * Add a new module to the blueprint
     */
    addModule(name, description) {
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
    removeModule(moduleName) {
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
    addEntity(moduleName, entityName) {
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
    removeEntity(moduleName, entityName) {
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
    renameModule(oldName, newName) {
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
    renameEntity(moduleName, oldName, newName) {
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
    updateMetadata(updates) {
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
exports.BlueprintProvider = BlueprintProvider;
/**
 * Register blueprint tree view commands
 */
function registerBlueprintCommands(context, provider) {
    // Add module command
    context.subscriptions.push(vscode.commands.registerCommand('sdlc.blueprint.addModule', async () => {
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
            }
            else {
                void vscode.window.showErrorMessage(`Failed to add module "${name}"`);
            }
        }
    }));
    // Remove module command
    context.subscriptions.push(vscode.commands.registerCommand('sdlc.blueprint.removeModule', async (item) => {
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
            const selected = await vscode.window.showQuickPick(blueprint.modules.map(m => m.name), { placeHolder: 'Select module to remove' });
            moduleName = selected;
        }
        if (moduleName) {
            const confirm = await vscode.window.showWarningMessage(`Remove module "${moduleName}" and all its entities?`, { modal: true }, 'Remove', 'Cancel');
            if (confirm === 'Remove') {
                if (provider.removeModule(moduleName)) {
                    void vscode.window.showInformationMessage(`Module "${moduleName}" removed`);
                }
                else {
                    void vscode.window.showErrorMessage(`Failed to remove module "${moduleName}"`);
                }
            }
        }
    }));
    // Add entity command
    context.subscriptions.push(vscode.commands.registerCommand('sdlc.blueprint.addEntity', async (item) => {
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
            const selected = await vscode.window.showQuickPick(blueprint.modules.map(m => m.name), { placeHolder: 'Select module to add entity to' });
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
                }
                else {
                    void vscode.window.showErrorMessage(`Failed to add entity "${entityName}"`);
                }
            }
        }
    }));
    // Remove entity command
    context.subscriptions.push(vscode.commands.registerCommand('sdlc.blueprint.removeEntity', async (item) => {
        if (provider.isLocked()) {
            void vscode.window.showWarningMessage('Blueprint is locked. Unlock to make changes.');
            return;
        }
        if (item?.nodeType === 'entity' && item.parent?.nodeType === 'module') {
            const moduleName = item.parent.label;
            const entityName = item.label;
            const confirm = await vscode.window.showWarningMessage(`Remove entity "${entityName}" from "${moduleName}"?`, { modal: true }, 'Remove', 'Cancel');
            if (confirm === 'Remove') {
                if (provider.removeEntity(moduleName, entityName)) {
                    void vscode.window.showInformationMessage(`Entity "${entityName}" removed`);
                }
                else {
                    void vscode.window.showErrorMessage(`Failed to remove entity "${entityName}"`);
                }
            }
        }
    }));
    // Edit blueprint metadata command
    context.subscriptions.push(vscode.commands.registerCommand('sdlc.blueprint.editMetadata', async () => {
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
    }));
    logger_1.Logger.info('Blueprint commands registered');
}
//# sourceMappingURL=blueprintProvider.js.map