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
import type { AppBlueprint, BlueprintModule } from '../types/codegen';
/**
 * Blueprint tree item types
 */
export type BlueprintNodeType = 'blueprint' | 'module' | 'entity' | 'metadata';
/**
 * Blueprint tree item
 */
export declare class BlueprintTreeItem extends vscode.TreeItem {
    readonly label: string;
    readonly collapsibleState: vscode.TreeItemCollapsibleState;
    readonly nodeType: BlueprintNodeType;
    readonly data?: (AppBlueprint | BlueprintModule | string) | undefined;
    readonly parent?: BlueprintTreeItem | undefined;
    constructor(label: string, collapsibleState: vscode.TreeItemCollapsibleState, nodeType: BlueprintNodeType, data?: (AppBlueprint | BlueprintModule | string) | undefined, parent?: BlueprintTreeItem | undefined);
    /**
     * Get icon for node type
     */
    private getIconForType;
    /**
     * Get tooltip for node type
     */
    private getTooltipForType;
}
/**
 * Blueprint Tree Data Provider
 *
 * Manages the hierarchical tree view of the App Blueprint structure.
 */
export declare class BlueprintProvider implements vscode.TreeDataProvider<BlueprintTreeItem> {
    private _onDidChangeTreeData;
    readonly onDidChangeTreeData: vscode.Event<void | BlueprintTreeItem | null | undefined>;
    private _blueprint;
    private _isLocked;
    constructor();
    /**
     * Set the current blueprint
     */
    setBlueprint(blueprint: AppBlueprint | undefined): void;
    /**
     * Get the current blueprint
     */
    getBlueprint(): AppBlueprint | undefined;
    /**
     * Set lock status
     */
    setLocked(locked: boolean): void;
    /**
     * Check if blueprint is locked
     */
    isLocked(): boolean;
    /**
     * Refresh the tree view
     */
    refresh(): void;
    /**
     * Clear the tree view
     */
    clear(): void;
    /**
     * Get tree item
     */
    getTreeItem(element: BlueprintTreeItem): vscode.TreeItem;
    /**
     * Get children for a tree item
     */
    getChildren(element?: BlueprintTreeItem): Thenable<BlueprintTreeItem[]>;
    /**
     * Get parent of a tree item
     */
    getParent(element: BlueprintTreeItem): vscode.ProviderResult<BlueprintTreeItem>;
    /**
     * Get root items (blueprint info)
     */
    private getRootItems;
    /**
     * Get module items
     */
    private getModuleItems;
    /**
     * Get entity items for a module
     */
    private getEntityItems;
    /**
     * Add a new module to the blueprint
     */
    addModule(name: string, description?: string): boolean;
    /**
     * Remove a module from the blueprint
     */
    removeModule(moduleName: string): boolean;
    /**
     * Add an entity to a module
     */
    addEntity(moduleName: string, entityName: string): boolean;
    /**
     * Remove an entity from a module
     */
    removeEntity(moduleName: string, entityName: string): boolean;
    /**
     * Rename a module
     */
    renameModule(oldName: string, newName: string): boolean;
    /**
     * Rename an entity
     */
    renameEntity(moduleName: string, oldName: string, newName: string): boolean;
    /**
     * Update blueprint metadata
     */
    updateMetadata(updates: Partial<Pick<AppBlueprint, 'name' | 'version' | 'description' | 'business_domain'>>): boolean;
}
/**
 * Register blueprint tree view commands
 */
export declare function registerBlueprintCommands(context: vscode.ExtensionContext, provider: BlueprintProvider): void;
//# sourceMappingURL=blueprintProvider.d.ts.map