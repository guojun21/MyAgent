import { exec } from 'child_process';
import { promisify } from 'util';

const execPromise = promisify(exec);

export class TerminalService {
  
  async executeCommand(command: string, timeout: number = 30) {
    console.log(`[TS-TerminalService] Running: ${command}`);
    
    try {
      const { stdout, stderr } = await execPromise(command, {
        timeout: timeout * 1000,
        maxBuffer: 1024 * 1024 * 10 // 10MB buffer
      });

      return {
        success: true,
        command: command,
        output: stdout || stderr, // Combine or prefer stdout
        error: null
      };
    } catch (error: any) {
      return {
        success: false,
        command: command,
        output: error.stdout,
        error: error.message || error.stderr || "Unknown error"
      };
    }
  }
}

