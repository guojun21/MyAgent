import Parser from 'tree-sitter';
import Python from 'tree-sitter-python';
import TypeScript from 'tree-sitter-typescript';
import JavaScript from 'tree-sitter-javascript';
import fs from 'fs-extra';
import path from 'path';
import { promisify } from 'util';
import { exec } from 'child_process';

const execPromise = promisify(exec);

// TS parser comes with two variants: typescript and tsx
const TypeScriptParser = TypeScript.typescript;
const TsxParser = TypeScript.tsx;

interface CodeLocation {
  path: string;
  line: number;     // 1-based
  column: number;   // 0-based
  code?: string;    // The line of code
  type: string;     // "definition" | "reference" | "call" etc.
}

export class CodeAnalysisService {
  private workspaceRoot: string;
  private parsers: Map<string, Parser> = new Map();

  constructor(workspaceRoot: string) {
    this.workspaceRoot = path.resolve(workspaceRoot);
    this.initParsers();
  }

  private initParsers() {
    const pyParser = new Parser();
    pyParser.setLanguage(Python);
    this.parsers.set('.py', pyParser);

    const tsParser = new Parser();
    tsParser.setLanguage(TypeScriptParser);
    this.parsers.set('.ts', tsParser);

    const tsxParser = new Parser();
    tsxParser.setLanguage(TsxParser);
    this.parsers.set('.tsx', tsxParser);

    const jsParser = new Parser();
    jsParser.setLanguage(JavaScript);
    this.parsers.set('.js', jsParser);
    this.parsers.set('.jsx', jsParser);
  }

  private getParser(filePath: string): Parser | undefined {
    const ext = path.extname(filePath);
    return this.parsers.get(ext);
  }

  private getFullPath(relativePath: string): string {
    if (path.isAbsolute(relativePath)) return relativePath;
    return path.resolve(this.workspaceRoot, relativePath);
  }

  private getRelativePath(fullPath: string): string {
    return path.relative(this.workspaceRoot, fullPath);
  }

  /**
   * Find definitions of a symbol.
   * Strategy:
   * 1. If file_path is provided, check that file first.
   * 2. If not found or no file_path, search project-wide (using grep to filter files first).
   */
  async findDefinitions(symbol: string, contextFile?: string): Promise<CodeLocation[]> {
    const definitions: CodeLocation[] = [];
    
    // 1. Check context file if provided
    if (contextFile) {
      const fullPath = this.getFullPath(contextFile);
      if (await fs.pathExists(fullPath)) {
        const defs = await this.parseFileForDefinitions(fullPath, symbol);
        definitions.push(...defs);
      }
    }

    // If we found it in context file, we might still want to look elsewhere? 
    // Usually definitions are unique or shadowed, but let's simple logic:
    // If found in context file, return it (likely local var or method).
    // If not, search globally.
    if (definitions.length > 0) return definitions;

    // 2. Global Search
    // Use grep to find potential files
    const files = await this.grepFiles(symbol);
    
    for (const file of files) {
      // Skip the context file as we already checked it
      if (contextFile && this.getFullPath(contextFile) === file) continue;
      
      const defs = await this.parseFileForDefinitions(file, symbol);
      definitions.push(...defs);
    }

    return definitions;
  }

  async findReferences(symbol: string): Promise<CodeLocation[]> {
    // Use grep to find candidate files
    const files = await this.grepFiles(symbol);
    const references: CodeLocation[] = [];

    for (const file of files) {
      const refs = await this.parseFileForReferences(file, symbol);
      references.push(...refs);
    }

    return references;
  }

  private async grepFiles(pattern: string): Promise<string[]> {
    try {
      // grep -l (list files) -r (recursive) pattern .
      // Exclude node_modules and .git
      const exclude = "--exclude-dir=node_modules --exclude-dir=.git --exclude-dir=__pycache__";
      const cmd = `grep -l -r ${exclude} "${pattern}" "${this.workspaceRoot}"`;
      
      const { stdout } = await execPromise(cmd, { maxBuffer: 1024 * 1024 * 10 });
      return stdout.split('\n').filter(Boolean).map(p => p.trim());
    } catch (e) {
      // grep returns exit code 1 if no matches found, which throws error in execPromise
      return [];
    }
  }

  private async parseFileForDefinitions(filePath: string, symbol: string): Promise<CodeLocation[]> {
    const parser = this.getParser(filePath);
    if (!parser) return [];

    try {
      const content = await fs.readFile(filePath, 'utf-8');
      const tree = parser.parse(content);
      const results: CodeLocation[] = [];
      const lines = content.split('\n');

      // Query based on language
      const ext = path.extname(filePath);
      let queryScm = "";
      
      if (ext === '.py') {
        queryScm = `
          (function_definition name: (identifier) @name (#eq? @name "${symbol}")) @def
          (class_definition name: (identifier) @name (#eq? @name "${symbol}")) @def
        `;
      } else if (['.ts', '.tsx', '.js', '.jsx'].includes(ext)) {
        queryScm = `
          (function_declaration name: (identifier) @name (#eq? @name "${symbol}")) @def
          (class_declaration name: (identifier) @name (#eq? @name "${symbol}")) @def
          (method_definition name: (property_identifier) @name (#eq? @name "${symbol}")) @def
          (variable_declarator name: (identifier) @name (#eq? @name "${symbol}")) @def
          (interface_declaration name: (type_identifier) @name (#eq? @name "${symbol}")) @def
        `;
      }

      if (!queryScm) return [];

      try {
        const query = new Parser.Query(parser.getLanguage(), queryScm);
        const matches = query.matches(tree.rootNode);

        for (const match of matches) {
          for (const capture of match.captures) {
            if (capture.name === 'def') {
              const node = capture.node;
              results.push({
                path: this.getRelativePath(filePath),
                line: node.startPosition.row + 1,
                column: node.startPosition.column,
                code: lines[node.startPosition.row].trim(),
                type: node.type // function_definition, etc.
              });
            }
          }
        }
      } catch (qError) {
        console.error(`Query error in ${filePath}:`, qError);
      }

      return results;
    } catch (e) {
      console.error(`Failed to parse ${filePath}:`, e);
      return [];
    }
  }

  private async parseFileForReferences(filePath: string, symbol: string): Promise<CodeLocation[]> {
    const parser = this.getParser(filePath);
    if (!parser) return [];

    try {
      const content = await fs.readFile(filePath, 'utf-8');
      const tree = parser.parse(content);
      const results: CodeLocation[] = [];
      const lines = content.split('\n');

      // Generic identifier search
      // We want to find any identifier that matches the symbol
      // But we want to exclude definitions if possible (though references often include defs)
      // Simpler approach: Find ALL identifiers equal to symbol
      
      const ext = path.extname(filePath);
      let queryScm = "";

      if (ext === '.py') {
        queryScm = `(identifier) @id (#eq? @id "${symbol}")`;
      } else {
        // TS/JS: identifier, property_identifier, type_identifier
        queryScm = `
          (identifier) @id (#eq? @id "${symbol}")
          (property_identifier) @id (#eq? @id "${symbol}")
          (type_identifier) @id (#eq? @id "${symbol}")
        `;
      }

      if (!queryScm) return [];

      const query = new Parser.Query(parser.getLanguage(), queryScm);
      const matches = query.matches(tree.rootNode);

      for (const match of matches) {
        for (const capture of match.captures) {
          const node = capture.node;
          // Simple filter: Try to guess if it's a definition to exclude it?
          // For "References", usually seeing the definition is also fine/useful.
          // Let's include everything for now.
          
          results.push({
            path: this.getRelativePath(filePath),
            line: node.startPosition.row + 1,
            column: node.startPosition.column,
            code: lines[node.startPosition.row].trim(),
            type: "reference"
          });
        }
      }

      return results;
    } catch (e) {
      return [];
    }
  }
}

