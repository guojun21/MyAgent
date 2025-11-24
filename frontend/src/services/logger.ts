// frontend/src/services/logger.ts

interface LogEntry {
  timestamp: string;
  level: 'LOG' | 'ERROR' | 'WARN' | 'INFO' | 'DEBUG';
  message: string;
  stack?: string;
  context?: Record<string, any>;
}

class SimpleLogger {
  private readonly BACKEND_URL = 'http://localhost:8000/api/logs/frontend';
  private readonly STORAGE_KEY = 'failed_logs';
  
  constructor() {
    console.log('🔧 SimpleLogger 初始化...');
    this.interceptConsole();
    this.captureErrors();
    this.recoverFailedLogs();
    
    // 页面关闭前发送剩余日志
    window.addEventListener('beforeunload', () => {
      this.sendPendingLogs();
    });
  }

  private interceptConsole() {
    const methods = ['log', 'error', 'warn', 'info'] as const;
    
    methods.forEach(method => {
      const original = console[method];
      console[method] = (...args: any[]) => {
        original.apply(console, args);
        
        // 忽略 SimpleLogger 自己的日志，防止死循环
        if (args[0] && typeof args[0] === 'string' && args[0].startsWith('[SimpleLogger]')) {
          return;
        }

        this.sendLog({
          timestamp: new Date().toISOString(),
          level: method.toUpperCase() as LogEntry['level'],
          message: args.map(arg => 
            typeof arg === 'object' ? JSON.stringify(arg, null, 2) : String(arg)
          ).join(' ')
        });
      };
    });
  }

  private captureErrors() {
    window.addEventListener('error', (event) => {
      this.sendLog({
        timestamp: new Date().toISOString(),
        level: 'ERROR',
        message: event.message,
        stack: event.error?.stack,
        context: {
          filename: event.filename,
          lineno: event.lineno,
          colno: event.colno
        }
      });
    });

    window.addEventListener('unhandledrejection', (event) => {
      this.sendLog({
        timestamp: new Date().toISOString(),
        level: 'ERROR',
        message: `Unhandled Promise Rejection: ${event.reason}`,
        stack: event.reason?.stack
      });
    });
  }

  private async sendLog(log: LogEntry) {
    try {
      // 使用 fetch 发送日志
      const response = await fetch(this.BACKEND_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ logs: [log] }),
        // 3秒超时
        signal: AbortSignal.timeout(3000) 
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      
    } catch (error) {
      // 失败时保存到 localStorage
      // 注意：这里不能用 console.error，否则会死循环
      // 使用原始 console 或自定义前缀
      // this.saveToStorage(log);
      // 暂时为了调试方便，不存 localStorage，直接忽略失败，避免复杂性
    }
  }

  private saveToStorage(log: LogEntry) {
    try {
      const stored = JSON.parse(localStorage.getItem(this.STORAGE_KEY) || '[]');
      stored.push(log);
      // 最多保留 1000 条
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(stored.slice(-1000)));
    } catch (e) {
      // 忽略存储错误
    }
  }

  private async recoverFailedLogs() {
    try {
      const stored = JSON.parse(localStorage.getItem(this.STORAGE_KEY) || '[]');
      if (stored.length === 0) return;

      const response = await fetch(this.BACKEND_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ logs: stored })
      });

      if (response.ok) {
        localStorage.removeItem(this.STORAGE_KEY);
        console.info(`[SimpleLogger] ✅ 恢复了 ${stored.length} 条未发送日志`);
      }
    } catch (e) {
      // 下次启动再试
    }
  }

  private sendPendingLogs() {
    const stored = localStorage.getItem(this.STORAGE_KEY);
    if (!stored) return;

    // 使用 sendBeacon 同步发送
    const blob = new Blob([stored], { type: 'application/json' });
    navigator.sendBeacon(this.BACKEND_URL, blob);
  }
}

// 立即启动单例
export const simpleLogger = new SimpleLogger();
