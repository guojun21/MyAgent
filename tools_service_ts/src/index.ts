import express from 'express';
import bodyParser from 'body-parser';
import cors from 'cors';
import { FileService } from './services/FileService';
import { TerminalService } from './services/TerminalService';
import { CodeAnalysisService } from './services/CodeAnalysisService';
import path from 'path';

const app = express();
const PORT = 8001;

// Middleware
app.use(cors());
app.use(bodyParser.json({ limit: '50mb' }));

// Initialize Services
// Assuming we are running from tools_service_ts/ directory, so workspace is parent
const WORKSPACE_ROOT = path.resolve(__dirname, '../../'); 
const fileService = new FileService(WORKSPACE_ROOT);
const terminalService = new TerminalService();
const codeAnalysisService = new CodeAnalysisService(WORKSPACE_ROOT);

console.log(`[TS-ToolService] Initialized with Workspace: ${WORKSPACE_ROOT}`);

// ============ File API ============

app.post('/file/read', async (req, res) => {
  const { path, line_start, line_end } = req.body;
  const result = await fileService.readFile(path, line_start, line_end);
  res.json(result);
});

app.post('/file/write', async (req, res) => {
  const { path, content, create_dirs } = req.body;
  const result = await fileService.writeFile(path, content, create_dirs);
  res.json(result);
});

app.post('/file/edit_batch', async (req, res) => {
  const { path, edits } = req.body;
  const result = await fileService.editFileBatch(path, edits);
  res.json(result);
});

app.post('/file/list', async (req, res) => {
  const directory = req.query.directory as string || ".";
  const recursive = req.query.recursive === 'true';
  const result = await fileService.listFiles(directory, recursive);
  res.json(result);
});

// ============ Terminal API ============

app.post('/terminal/run', async (req, res) => {
  const { command, timeout } = req.body;
  const result = await terminalService.executeCommand(command, timeout);
  res.json(result);
});

// ============ Code Analysis API (Tree-sitter) ============

app.post('/code/definition', async (req, res) => {
  const { symbol, path } = req.body;
  try {
    const result = await codeAnalysisService.findDefinitions(symbol, path);
    res.json({
      success: true,
      definitions: result
    });
  } catch (e: any) {
    res.json({ success: false, error: e.message });
  }
});

app.post('/code/references', async (req, res) => {
  const { symbol } = req.body;
  try {
    const result = await codeAnalysisService.findReferences(symbol);
    res.json({
      success: true,
      references: result
    });
  } catch (e: any) {
    res.json({ success: false, error: e.message });
  }
});

// Legacy Grep Search (kept for fallback)
app.post('/code/search', async (req, res) => {
    const { query, directory } = req.body;
    const cmd = `grep -r "${query}" "${directory || '.'}" | head -n 100`;
    const result = await terminalService.executeCommand(cmd);
    
    if (result.success) {
        res.json({
            success: true,
            matches: result.output.split('\n').filter(Boolean),
            count: result.output.split('\n').filter(Boolean).length
        });
    } else {
        res.json({
            success: false,
            error: result.error
        });
    }
});


// Start Server
app.listen(PORT, '0.0.0.0', () => {
  console.log(`[TS-ToolService] Running on http://0.0.0.0:${PORT}`);
});
