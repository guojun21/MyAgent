"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
var electron_1 = require("electron");
electron_1.contextBridge.exposeInMainWorld('electron', {
// Example API
// sendMsg: (msg: string) => ipcRenderer.send('msg', msg),
});
//# sourceMappingURL=preload.js.map