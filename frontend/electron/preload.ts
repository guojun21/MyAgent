import { contextBridge, ipcRenderer } from 'electron';

contextBridge.exposeInMainWorld('electron', {
  // Example API
  // sendMsg: (msg: string) => ipcRenderer.send('msg', msg),
});

