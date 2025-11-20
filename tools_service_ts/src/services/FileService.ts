import fs from 'fs-extra';
import path from 'path';
import glob from 'glob';
import { promisify } from 'util';

const globPromise = promisify(glob);

export class FileService {
  private workspaceRoot: string;

  constructor(workspaceRoot: string = ".") {
    this.workspaceRoot = path.resolve(workspaceRoot);
    console.log(`[TS-FileService] Workspace Root: ${this.workspaceRoot}`);
  }

  private getFullPath(relativePath: string): string {
    let fullPath = path.resolve(relativePath);
    if (!path.isAbsolute(relativePath)) {
      fullPath = path.resolve(this.workspaceRoot, relativePath);
    }
    return fullPath;
  }

  private getRelativePath(fullPath: string): string {
    return path.relative(this.workspaceRoot, fullPath);
  }

  async readFile(filePath: string, lineStart?: number, lineEnd?: number) {
    console.log(`[TS-FileService.readFile] ${filePath} (${lineStart}-${lineEnd})`);
    try {
      const fullPath = this.getFullPath(filePath);
      
      if (!(await fs.pathExists(fullPath))) {
        return { success: false, error: `File not found: ${filePath}` };
      }
      
      const stat = await fs.stat(fullPath);
      if (!stat.isFile()) {
        return { success: false, error: `Not a file: ${filePath}` };
      }

      const content = await fs.readFile(fullPath, 'utf-8');
      const lines = content.split('\n');
      
      let resultLines = lines;
      if (lineStart !== undefined || lineEnd !== undefined) {
        const start = lineStart ? lineStart - 1 : 0;
        const end = lineEnd ? lineEnd : lines.length;
        resultLines = lines.slice(start, end);
      }

      return {
        success: true,
        path: this.getRelativePath(fullPath),
        content: resultLines.join('\n'),
        lines: resultLines.length,
        total_lines: lineStart === undefined ? lines.length : undefined
      };
    } catch (error: any) {
      return { success: false, error: `Read failed: ${error.message}` };
    }
  }

  async writeFile(filePath: string, content: string, createDirs: boolean = true) {
    console.log(`[TS-FileService.writeFile] ${filePath}`);
    try {
      const fullPath = this.getFullPath(filePath);
      
      if (createDirs) {
        await fs.ensureDir(path.dirname(fullPath));
      }

      await fs.writeFile(fullPath, content, 'utf-8');
      
      return {
        success: true,
        path: this.getRelativePath(fullPath),
        bytes_written: Buffer.byteLength(content, 'utf-8')
      };
    } catch (error: any) {
      return { success: false, error: `Write failed: ${error.message}` };
    }
  }

  async editFileBatch(filePath: string, edits: Array<{old: string, new: string}>) {
    console.log(`[TS-FileService.editFileBatch] ${filePath} (${edits.length} edits)`);
    try {
      const fullPath = this.getFullPath(filePath);
      
      if (!(await fs.pathExists(fullPath))) {
        return { success: false, error: `File not found: ${filePath}` };
      }

      let content = await fs.readFile(fullPath, 'utf-8');
      let replacements = 0;

      for (const edit of edits) {
        if (content.includes(edit.old)) {
          content = content.replace(edit.old, edit.new);
          replacements++;
        }
      }

      await fs.writeFile(fullPath, content, 'utf-8');

      return {
        success: true,
        path: this.getRelativePath(fullPath),
        total_edits: edits.length,
        successful_edits: replacements,
        failed_edits: edits.length - replacements
      };
    } catch (error: any) {
      return { success: false, error: `Batch edit failed: ${error.message}` };
    }
  }

  async listFiles(directory: string = ".", recursive: boolean = false) {
    console.log(`[TS-FileService.listFiles] ${directory} (recursive: ${recursive})`);
    try {
      const fullDirPath = this.getFullPath(directory);
      
      if (!(await fs.pathExists(fullDirPath))) {
        return { success: false, error: `Directory not found: ${directory}` };
      }

      const pattern = recursive ? "**/*" : "*";
      // Use glob package directly instead of fs-extra re-export or util.promisify if needed, 
      // but fs-extra doesn't have glob. We imported glob.
      
      const matches = await globPromise(pattern, { 
        cwd: fullDirPath, 
        dot: false, // Exclude hidden files by default
        mark: true  // Add / to directories
      });

      const files = [];
      const dirs = [];

      for (const match of matches) {
        const fullItemPath = path.join(fullDirPath, match);
        const relPath = this.getRelativePath(fullItemPath);
        
        // Skip hidden files/dirs if they matched somehow
        if (path.basename(match).startsWith('.')) continue;

        try {
            const stat = await fs.stat(fullItemPath);
            if (stat.isFile()) {
                files.push({
                    path: relPath,
                    name: path.basename(match),
                    size: stat.size,
                    type: "file"
                });
            } else if (stat.isDirectory()) {
                dirs.push({
                    path: relPath,
                    name: path.basename(match),
                    type: "directory"
                });
            }
        } catch (e) {
            // Ignore stat errors (e.g. broken symlinks)
        }
      }

      return {
        success: true,
        directory: this.getRelativePath(fullDirPath),
        files: files.sort((a, b) => a.name.localeCompare(b.name)),
        directories: dirs.sort((a, b) => a.name.localeCompare(b.name)),
        total_files: files.length,
        total_directories: dirs.length
      };

    } catch (error: any) {
      return { success: false, error: `List files failed: ${error.message}` };
    }
  }
}

