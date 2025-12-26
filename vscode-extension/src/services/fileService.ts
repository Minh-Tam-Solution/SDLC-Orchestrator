/**
 * File Service - Generated Code File Operations
 *
 * Handles file system operations for generated code:
 * - Writing files to disk
 * - Creating directory structures
 * - Opening files in editor
 * - File watching and change detection
 *
 * Sprint 53 Day 3 - Streaming Integration
 * @version 1.0.0
 */

import * as vscode from 'vscode';
import * as path from 'path';
import { Logger } from '../utils/logger';
import type { GeneratedFile } from '../types/codegen';

/**
 * File write result
 */
export interface FileWriteResult {
    path: string;
    success: boolean;
    error?: string;
}

/**
 * Directory structure
 */
export interface DirectoryInfo {
    path: string;
    files: string[];
    subdirectories: DirectoryInfo[];
}

/**
 * File Service
 *
 * Provides file system operations for the code generation workflow.
 */
export class FileService {
    private static instance: FileService | undefined;

    private constructor() {
        Logger.info('FileService initialized');
    }

    /**
     * Get singleton instance
     */
    public static getInstance(): FileService {
        if (!FileService.instance) {
            FileService.instance = new FileService();
        }
        return FileService.instance;
    }

    /**
     * Write a single file to disk
     */
    public async writeFile(
        basePath: string,
        file: GeneratedFile
    ): Promise<FileWriteResult> {
        const fullPath = path.join(basePath, file.path);
        const dirPath = path.dirname(fullPath);

        try {
            // Create directory if needed
            const dirUri = vscode.Uri.file(dirPath);
            try {
                await vscode.workspace.fs.createDirectory(dirUri);
            } catch {
                // Directory may already exist
            }

            // Write file
            const fileUri = vscode.Uri.file(fullPath);
            const content = Buffer.from(file.content, 'utf-8');
            await vscode.workspace.fs.writeFile(fileUri, content);

            Logger.info(`File written: ${fullPath}`);

            return {
                path: file.path,
                success: true,
            };
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : String(error);
            Logger.error(`Failed to write file ${file.path}: ${errorMessage}`);

            return {
                path: file.path,
                success: false,
                error: errorMessage,
            };
        }
    }

    /**
     * Write multiple files to disk
     */
    public async writeFiles(
        basePath: string,
        files: GeneratedFile[],
        onProgress?: (completed: number, total: number, currentFile: string) => void
    ): Promise<FileWriteResult[]> {
        const results: FileWriteResult[] = [];
        const total = files.length;

        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            if (!file) continue;

            if (onProgress) {
                onProgress(i, total, file.path);
            }

            const result = await this.writeFile(basePath, file);
            results.push(result);
        }

        const successCount = results.filter(r => r.success).length;
        Logger.info(`Wrote ${successCount}/${total} files to ${basePath}`);

        return results;
    }

    /**
     * Open a file in the editor
     */
    public async openFile(filePath: string): Promise<void> {
        try {
            const uri = vscode.Uri.file(filePath);
            const doc = await vscode.workspace.openTextDocument(uri);
            await vscode.window.showTextDocument(doc, vscode.ViewColumn.One);
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : String(error);
            Logger.error(`Failed to open file ${filePath}: ${errorMessage}`);
            void vscode.window.showErrorMessage(`Failed to open file: ${errorMessage}`);
        }
    }

    /**
     * Open generated file content in a new untitled editor
     */
    public async openGeneratedFile(
        file: GeneratedFile
    ): Promise<vscode.TextDocument | undefined> {
        try {
            const doc = await vscode.workspace.openTextDocument({
                content: file.content,
                language: file.language,
            });
            await vscode.window.showTextDocument(doc, vscode.ViewColumn.One);
            return doc;
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : String(error);
            Logger.error(`Failed to open generated file ${file.path}: ${errorMessage}`);
            return undefined;
        }
    }

    /**
     * Preview file in read-only mode
     */
    public async previewFile(
        file: GeneratedFile
    ): Promise<vscode.TextDocument | undefined> {
        try {
            const doc = await vscode.workspace.openTextDocument({
                content: file.content,
                language: file.language,
            });
            await vscode.window.showTextDocument(doc, {
                viewColumn: vscode.ViewColumn.Beside,
                preserveFocus: true,
                preview: true,
            });
            return doc;
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : String(error);
            Logger.error(`Failed to preview file ${file.path}: ${errorMessage}`);
            return undefined;
        }
    }

    /**
     * Create directory structure from file list
     */
    public async createDirectoryStructure(
        basePath: string,
        files: GeneratedFile[]
    ): Promise<void> {
        const directories = new Set<string>();

        for (const file of files) {
            const dirPath = path.dirname(file.path);
            if (dirPath && dirPath !== '.') {
                // Add all parent directories
                const parts = dirPath.split('/');
                for (let i = 1; i <= parts.length; i++) {
                    directories.add(parts.slice(0, i).join('/'));
                }
            }
        }

        // Sort directories by depth (create parent first)
        const sortedDirs = Array.from(directories).sort((a, b) =>
            a.split('/').length - b.split('/').length
        );

        for (const dir of sortedDirs) {
            const fullPath = path.join(basePath, dir);
            const uri = vscode.Uri.file(fullPath);

            try {
                await vscode.workspace.fs.createDirectory(uri);
            } catch {
                // Directory may already exist
            }
        }

        Logger.info(`Created ${directories.size} directories in ${basePath}`);
    }

    /**
     * Check if a file exists
     */
    public async fileExists(filePath: string): Promise<boolean> {
        try {
            const uri = vscode.Uri.file(filePath);
            await vscode.workspace.fs.stat(uri);
            return true;
        } catch {
            return false;
        }
    }

    /**
     * Check if a directory exists
     */
    public async directoryExists(dirPath: string): Promise<boolean> {
        try {
            const uri = vscode.Uri.file(dirPath);
            const stat = await vscode.workspace.fs.stat(uri);
            return (stat.type & vscode.FileType.Directory) !== 0;
        } catch {
            return false;
        }
    }

    /**
     * Get directory structure
     */
    public async getDirectoryStructure(
        dirPath: string
    ): Promise<DirectoryInfo | undefined> {
        try {
            const uri = vscode.Uri.file(dirPath);
            const entries = await vscode.workspace.fs.readDirectory(uri);

            const files: string[] = [];
            const subdirectories: DirectoryInfo[] = [];

            for (const [name, type] of entries) {
                if (type === vscode.FileType.File) {
                    files.push(name);
                } else if (type === vscode.FileType.Directory) {
                    const subDir = await this.getDirectoryStructure(
                        path.join(dirPath, name)
                    );
                    if (subDir) {
                        subdirectories.push(subDir);
                    }
                }
            }

            return {
                path: dirPath,
                files: files.sort(),
                subdirectories: subdirectories.sort((a, b) =>
                    a.path.localeCompare(b.path)
                ),
            };
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : String(error);
            Logger.error(`Failed to read directory ${dirPath}: ${errorMessage}`);
            return undefined;
        }
    }

    /**
     * Delete a file
     */
    public async deleteFile(filePath: string): Promise<boolean> {
        try {
            const uri = vscode.Uri.file(filePath);
            await vscode.workspace.fs.delete(uri);
            Logger.info(`Deleted file: ${filePath}`);
            return true;
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : String(error);
            Logger.error(`Failed to delete file ${filePath}: ${errorMessage}`);
            return false;
        }
    }

    /**
     * Delete a directory recursively
     */
    public async deleteDirectory(
        dirPath: string,
        recursive = true
    ): Promise<boolean> {
        try {
            const uri = vscode.Uri.file(dirPath);
            await vscode.workspace.fs.delete(uri, { recursive });
            Logger.info(`Deleted directory: ${dirPath}`);
            return true;
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : String(error);
            Logger.error(`Failed to delete directory ${dirPath}: ${errorMessage}`);
            return false;
        }
    }

    /**
     * Copy a file
     */
    public async copyFile(
        sourcePath: string,
        targetPath: string,
        overwrite = false
    ): Promise<boolean> {
        try {
            const sourceUri = vscode.Uri.file(sourcePath);
            const targetUri = vscode.Uri.file(targetPath);

            // Create target directory if needed
            const targetDir = path.dirname(targetPath);
            const targetDirUri = vscode.Uri.file(targetDir);
            try {
                await vscode.workspace.fs.createDirectory(targetDirUri);
            } catch {
                // Directory may already exist
            }

            await vscode.workspace.fs.copy(sourceUri, targetUri, { overwrite });
            Logger.info(`Copied file: ${sourcePath} -> ${targetPath}`);
            return true;
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : String(error);
            Logger.error(`Failed to copy file ${sourcePath}: ${errorMessage}`);
            return false;
        }
    }

    /**
     * Get relative path from base
     */
    public getRelativePath(basePath: string, filePath: string): string {
        return path.relative(basePath, filePath);
    }

    /**
     * Get absolute path from base and relative
     */
    public getAbsolutePath(basePath: string, relativePath: string): string {
        return path.join(basePath, relativePath);
    }

    /**
     * Get file extension
     */
    public getFileExtension(filePath: string): string {
        return path.extname(filePath).toLowerCase().slice(1);
    }

    /**
     * Get VS Code language ID from file path
     */
    public getLanguageId(filePath: string): string {
        const ext = this.getFileExtension(filePath);
        const langMap: Record<string, string> = {
            'py': 'python',
            'ts': 'typescript',
            'tsx': 'typescriptreact',
            'js': 'javascript',
            'jsx': 'javascriptreact',
            'json': 'json',
            'md': 'markdown',
            'yaml': 'yaml',
            'yml': 'yaml',
            'html': 'html',
            'css': 'css',
            'scss': 'scss',
            'less': 'less',
            'sql': 'sql',
            'sh': 'shellscript',
            'bash': 'shellscript',
            'xml': 'xml',
            'vue': 'vue',
            'svelte': 'svelte',
            'go': 'go',
            'rs': 'rust',
            'java': 'java',
            'kt': 'kotlin',
            'swift': 'swift',
            'c': 'c',
            'cpp': 'cpp',
            'h': 'c',
            'hpp': 'cpp',
            'cs': 'csharp',
            'rb': 'ruby',
            'php': 'php',
            'r': 'r',
            'dart': 'dart',
            'dockerfile': 'dockerfile',
            'toml': 'toml',
            'ini': 'ini',
            'env': 'dotenv',
        };
        return langMap[ext] || 'plaintext';
    }

    /**
     * Get file icon based on extension
     */
    public getFileIcon(filePath: string): string {
        const ext = this.getFileExtension(filePath);
        const iconMap: Record<string, string> = {
            'py': '🐍',
            'ts': '📘',
            'tsx': '⚛️',
            'js': '📒',
            'jsx': '⚛️',
            'json': '📋',
            'md': '📝',
            'yaml': '⚙️',
            'yml': '⚙️',
            'html': '🌐',
            'css': '🎨',
            'sql': '🗃️',
            'sh': '💻',
            'dockerfile': '🐳',
            'go': '🐹',
            'rs': '🦀',
            'java': '☕',
            'vue': '💚',
            'svelte': '🧡',
        };
        return iconMap[ext] || '📄';
    }

    /**
     * Watch a directory for changes
     */
    public watchDirectory(
        dirPath: string,
        onCreated?: (uri: vscode.Uri) => void,
        onChanged?: (uri: vscode.Uri) => void,
        onDeleted?: (uri: vscode.Uri) => void
    ): vscode.Disposable {
        const pattern = new vscode.RelativePattern(dirPath, '**/*');
        const watcher = vscode.workspace.createFileSystemWatcher(pattern);

        if (onCreated) {
            watcher.onDidCreate(onCreated);
        }
        if (onChanged) {
            watcher.onDidChange(onChanged);
        }
        if (onDeleted) {
            watcher.onDidDelete(onDeleted);
        }

        Logger.info(`Started watching directory: ${dirPath}`);

        return watcher;
    }
}

/**
 * Get FileService singleton
 */
export function getFileService(): FileService {
    return FileService.getInstance();
}
