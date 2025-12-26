"use strict";
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
exports.FileService = void 0;
exports.getFileService = getFileService;
const vscode = __importStar(require("vscode"));
const path = __importStar(require("path"));
const logger_1 = require("../utils/logger");
/**
 * File Service
 *
 * Provides file system operations for the code generation workflow.
 */
class FileService {
    static instance;
    constructor() {
        logger_1.Logger.info('FileService initialized');
    }
    /**
     * Get singleton instance
     */
    static getInstance() {
        if (!FileService.instance) {
            FileService.instance = new FileService();
        }
        return FileService.instance;
    }
    /**
     * Write a single file to disk
     */
    async writeFile(basePath, file) {
        const fullPath = path.join(basePath, file.path);
        const dirPath = path.dirname(fullPath);
        try {
            // Create directory if needed
            const dirUri = vscode.Uri.file(dirPath);
            try {
                await vscode.workspace.fs.createDirectory(dirUri);
            }
            catch {
                // Directory may already exist
            }
            // Write file
            const fileUri = vscode.Uri.file(fullPath);
            const content = Buffer.from(file.content, 'utf-8');
            await vscode.workspace.fs.writeFile(fileUri, content);
            logger_1.Logger.info(`File written: ${fullPath}`);
            return {
                path: file.path,
                success: true,
            };
        }
        catch (error) {
            const errorMessage = error instanceof Error ? error.message : String(error);
            logger_1.Logger.error(`Failed to write file ${file.path}: ${errorMessage}`);
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
    async writeFiles(basePath, files, onProgress) {
        const results = [];
        const total = files.length;
        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            if (!file)
                continue;
            if (onProgress) {
                onProgress(i, total, file.path);
            }
            const result = await this.writeFile(basePath, file);
            results.push(result);
        }
        const successCount = results.filter(r => r.success).length;
        logger_1.Logger.info(`Wrote ${successCount}/${total} files to ${basePath}`);
        return results;
    }
    /**
     * Open a file in the editor
     */
    async openFile(filePath) {
        try {
            const uri = vscode.Uri.file(filePath);
            const doc = await vscode.workspace.openTextDocument(uri);
            await vscode.window.showTextDocument(doc, vscode.ViewColumn.One);
        }
        catch (error) {
            const errorMessage = error instanceof Error ? error.message : String(error);
            logger_1.Logger.error(`Failed to open file ${filePath}: ${errorMessage}`);
            void vscode.window.showErrorMessage(`Failed to open file: ${errorMessage}`);
        }
    }
    /**
     * Open generated file content in a new untitled editor
     */
    async openGeneratedFile(file) {
        try {
            const doc = await vscode.workspace.openTextDocument({
                content: file.content,
                language: file.language,
            });
            await vscode.window.showTextDocument(doc, vscode.ViewColumn.One);
            return doc;
        }
        catch (error) {
            const errorMessage = error instanceof Error ? error.message : String(error);
            logger_1.Logger.error(`Failed to open generated file ${file.path}: ${errorMessage}`);
            return undefined;
        }
    }
    /**
     * Preview file in read-only mode
     */
    async previewFile(file) {
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
        }
        catch (error) {
            const errorMessage = error instanceof Error ? error.message : String(error);
            logger_1.Logger.error(`Failed to preview file ${file.path}: ${errorMessage}`);
            return undefined;
        }
    }
    /**
     * Create directory structure from file list
     */
    async createDirectoryStructure(basePath, files) {
        const directories = new Set();
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
        const sortedDirs = Array.from(directories).sort((a, b) => a.split('/').length - b.split('/').length);
        for (const dir of sortedDirs) {
            const fullPath = path.join(basePath, dir);
            const uri = vscode.Uri.file(fullPath);
            try {
                await vscode.workspace.fs.createDirectory(uri);
            }
            catch {
                // Directory may already exist
            }
        }
        logger_1.Logger.info(`Created ${directories.size} directories in ${basePath}`);
    }
    /**
     * Check if a file exists
     */
    async fileExists(filePath) {
        try {
            const uri = vscode.Uri.file(filePath);
            await vscode.workspace.fs.stat(uri);
            return true;
        }
        catch {
            return false;
        }
    }
    /**
     * Check if a directory exists
     */
    async directoryExists(dirPath) {
        try {
            const uri = vscode.Uri.file(dirPath);
            const stat = await vscode.workspace.fs.stat(uri);
            return (stat.type & vscode.FileType.Directory) !== 0;
        }
        catch {
            return false;
        }
    }
    /**
     * Get directory structure
     */
    async getDirectoryStructure(dirPath) {
        try {
            const uri = vscode.Uri.file(dirPath);
            const entries = await vscode.workspace.fs.readDirectory(uri);
            const files = [];
            const subdirectories = [];
            for (const [name, type] of entries) {
                if (type === vscode.FileType.File) {
                    files.push(name);
                }
                else if (type === vscode.FileType.Directory) {
                    const subDir = await this.getDirectoryStructure(path.join(dirPath, name));
                    if (subDir) {
                        subdirectories.push(subDir);
                    }
                }
            }
            return {
                path: dirPath,
                files: files.sort(),
                subdirectories: subdirectories.sort((a, b) => a.path.localeCompare(b.path)),
            };
        }
        catch (error) {
            const errorMessage = error instanceof Error ? error.message : String(error);
            logger_1.Logger.error(`Failed to read directory ${dirPath}: ${errorMessage}`);
            return undefined;
        }
    }
    /**
     * Delete a file
     */
    async deleteFile(filePath) {
        try {
            const uri = vscode.Uri.file(filePath);
            await vscode.workspace.fs.delete(uri);
            logger_1.Logger.info(`Deleted file: ${filePath}`);
            return true;
        }
        catch (error) {
            const errorMessage = error instanceof Error ? error.message : String(error);
            logger_1.Logger.error(`Failed to delete file ${filePath}: ${errorMessage}`);
            return false;
        }
    }
    /**
     * Delete a directory recursively
     */
    async deleteDirectory(dirPath, recursive = true) {
        try {
            const uri = vscode.Uri.file(dirPath);
            await vscode.workspace.fs.delete(uri, { recursive });
            logger_1.Logger.info(`Deleted directory: ${dirPath}`);
            return true;
        }
        catch (error) {
            const errorMessage = error instanceof Error ? error.message : String(error);
            logger_1.Logger.error(`Failed to delete directory ${dirPath}: ${errorMessage}`);
            return false;
        }
    }
    /**
     * Copy a file
     */
    async copyFile(sourcePath, targetPath, overwrite = false) {
        try {
            const sourceUri = vscode.Uri.file(sourcePath);
            const targetUri = vscode.Uri.file(targetPath);
            // Create target directory if needed
            const targetDir = path.dirname(targetPath);
            const targetDirUri = vscode.Uri.file(targetDir);
            try {
                await vscode.workspace.fs.createDirectory(targetDirUri);
            }
            catch {
                // Directory may already exist
            }
            await vscode.workspace.fs.copy(sourceUri, targetUri, { overwrite });
            logger_1.Logger.info(`Copied file: ${sourcePath} -> ${targetPath}`);
            return true;
        }
        catch (error) {
            const errorMessage = error instanceof Error ? error.message : String(error);
            logger_1.Logger.error(`Failed to copy file ${sourcePath}: ${errorMessage}`);
            return false;
        }
    }
    /**
     * Get relative path from base
     */
    getRelativePath(basePath, filePath) {
        return path.relative(basePath, filePath);
    }
    /**
     * Get absolute path from base and relative
     */
    getAbsolutePath(basePath, relativePath) {
        return path.join(basePath, relativePath);
    }
    /**
     * Get file extension
     */
    getFileExtension(filePath) {
        return path.extname(filePath).toLowerCase().slice(1);
    }
    /**
     * Get VS Code language ID from file path
     */
    getLanguageId(filePath) {
        const ext = this.getFileExtension(filePath);
        const langMap = {
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
    getFileIcon(filePath) {
        const ext = this.getFileExtension(filePath);
        const iconMap = {
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
    watchDirectory(dirPath, onCreated, onChanged, onDeleted) {
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
        logger_1.Logger.info(`Started watching directory: ${dirPath}`);
        return watcher;
    }
}
exports.FileService = FileService;
/**
 * Get FileService singleton
 */
function getFileService() {
    return FileService.getInstance();
}
//# sourceMappingURL=fileService.js.map