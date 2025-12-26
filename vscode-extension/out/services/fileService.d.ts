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
export declare class FileService {
    private static instance;
    private constructor();
    /**
     * Get singleton instance
     */
    static getInstance(): FileService;
    /**
     * Write a single file to disk
     */
    writeFile(basePath: string, file: GeneratedFile): Promise<FileWriteResult>;
    /**
     * Write multiple files to disk
     */
    writeFiles(basePath: string, files: GeneratedFile[], onProgress?: (completed: number, total: number, currentFile: string) => void): Promise<FileWriteResult[]>;
    /**
     * Open a file in the editor
     */
    openFile(filePath: string): Promise<void>;
    /**
     * Open generated file content in a new untitled editor
     */
    openGeneratedFile(file: GeneratedFile): Promise<vscode.TextDocument | undefined>;
    /**
     * Preview file in read-only mode
     */
    previewFile(file: GeneratedFile): Promise<vscode.TextDocument | undefined>;
    /**
     * Create directory structure from file list
     */
    createDirectoryStructure(basePath: string, files: GeneratedFile[]): Promise<void>;
    /**
     * Check if a file exists
     */
    fileExists(filePath: string): Promise<boolean>;
    /**
     * Check if a directory exists
     */
    directoryExists(dirPath: string): Promise<boolean>;
    /**
     * Get directory structure
     */
    getDirectoryStructure(dirPath: string): Promise<DirectoryInfo | undefined>;
    /**
     * Delete a file
     */
    deleteFile(filePath: string): Promise<boolean>;
    /**
     * Delete a directory recursively
     */
    deleteDirectory(dirPath: string, recursive?: boolean): Promise<boolean>;
    /**
     * Copy a file
     */
    copyFile(sourcePath: string, targetPath: string, overwrite?: boolean): Promise<boolean>;
    /**
     * Get relative path from base
     */
    getRelativePath(basePath: string, filePath: string): string;
    /**
     * Get absolute path from base and relative
     */
    getAbsolutePath(basePath: string, relativePath: string): string;
    /**
     * Get file extension
     */
    getFileExtension(filePath: string): string;
    /**
     * Get VS Code language ID from file path
     */
    getLanguageId(filePath: string): string;
    /**
     * Get file icon based on extension
     */
    getFileIcon(filePath: string): string;
    /**
     * Watch a directory for changes
     */
    watchDirectory(dirPath: string, onCreated?: (uri: vscode.Uri) => void, onChanged?: (uri: vscode.Uri) => void, onDeleted?: (uri: vscode.Uri) => void): vscode.Disposable;
}
/**
 * Get FileService singleton
 */
export declare function getFileService(): FileService;
//# sourceMappingURL=fileService.d.ts.map