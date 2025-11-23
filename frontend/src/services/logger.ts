/**
 * 前端日志收集服务
 * 收集 console.log/error/warn 并发送到后端保存到 llmlogs/frontend/
 */

interface LogEntry {
  level: 'log' | 'error' | 'warn' | 'info';
  message: string;
  timestamp: string;
  stack?: string;
}

class FrontendLogger {
  private logs: LogEntry[] = [];
  private maxBatchSize = 50; // 每批最多50条
  private flushInterval = 5000; // 5秒钟自动发送一次
  private backendUrl = 'http://localhost:8000';
  private timer: NodeJS.Timeout | null = null;

  constructor() {
    this.interceptConsole();
    this.startAutoFlush();
    this.handleBeforeUnload();
  }

  /**
   * 拦截 console 方法
   */
  private interceptConsole() {
    const originalLog = console.log;
    const originalError = console.error;
    const originalWarn = console.warn;
    const originalInfo = console.info;

    console.log = (...args: any[]) => {
      originalLog.apply(console, args);
      this.captureLog('log', args);
    };

    console.error = (...args: any[]) => {
      originalError.apply(console, args);
      this.captureLog('error', args);
    };

    console.warn = (...args: any[]) => {
      originalWarn.apply(console, args);
      this.captureLog('warn', args);
    };

    console.info = (...args: any[]) => {
      originalInfo.apply(console, args);
      this.captureLog('info', args);
    };

    // 全局错误捕获
    window.addEventListener('error', (event) => {
      this.captureLog('error', [
        `Uncaught Error: ${event.message}`,
        `at ${event.filename}:${event.lineno}:${event.colno}`,
        event.error?.stack || ''
      ]);
    });

    // Promise 未捕获错误
    window.addEventListener('unhandledrejection', (event) => {
      this.captureLog('error', [
        `Unhandled Promise Rejection: ${event.reason}`,
        event.reason?.stack || ''
      ]);
    });
  }

  /**
   * 捕获日志
   */
  private captureLog(level: LogEntry['level'], args: any[]) {
    const message = args.map(arg => {
      if (typeof arg === 'object') {
        try {
          return JSON.stringify(arg, null, 2);
        } catch {
          return String(arg);
        }
      }
      return String(arg);
    }).join(' ');

    const entry: LogEntry = {
      level,
      message,
      timestamp: new Date().toISOString(),
    };

    // 如果是 error，尝试获取堆栈
    if (level === 'error') {
      const errorArg = args.find(arg => arg instanceof Error);
      if (errorArg) {
        entry.stack = errorArg.stack;
      }
    }

    this.logs.push(entry);

    // 达到批次大小，立即发送
    if (this.logs.length >= this.maxBatchSize) {
      this.flush();
    }
  }

  /**
   * 启动自动刷新定时器
   */
  private startAutoFlush() {
    this.timer = setInterval(() => {
      if (this.logs.length > 0) {
        this.flush();
      }
    }, this.flushInterval);
  }

  /**
   * 页面关闭前发送
   */
  private handleBeforeUnload() {
    window.addEventListener('beforeunload', () => {
      this.flush(true); // 同步发送
    });
  }

  /**
   * 发送日志到后端
   */
  private async flush(sync: boolean = false) {
    if (this.logs.length === 0) return;

    const logsToSend = [...this.logs];
    this.logs = [];

    const payload = JSON.stringify({ logs: logsToSend });

    try {
      if (sync) {
        // 同步请求（页面关闭前）
        const xhr = new XMLHttpRequest();
        xhr.open('POST', `${this.backendUrl}/api/logs/frontend`, false);
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.send(payload);
      } else {
        // 异步请求
        await fetch(`${this.backendUrl}/api/logs/frontend`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: payload,
        });
      }
    } catch (error) {
      // 发送失败，打印到原生 console（不会再次捕获）
      console.warn('[FrontendLogger] 发送日志失败:', error);
    }
  }

  /**
   * 手动刷新
   */
  public manualFlush() {
    this.flush();
  }

  /**
   * 销毁
   */
  public destroy() {
    if (this.timer) {
      clearInterval(this.timer);
      this.timer = null;
    }
    this.flush(true);
  }
}

// 导出单例
export const frontendLogger = new FrontendLogger();

