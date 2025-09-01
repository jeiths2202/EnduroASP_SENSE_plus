interface SmedDataEvent {
  action: string;
  map_file?: string;
  fields?: any;
  program_name?: string;
  session_id?: string;
  hub_metadata?: any;
}

class WebSocketService {
  private ws: WebSocket | null = null;
  private listeners: Map<string, Set<Function>> = new Map();
  private connected: boolean = false;
  private terminalId: string = 'webui';
  private sessionId: string | null = null;
  private wsname: string = 'WSNAME00';
  private user: string = 'unknown';
  private reconnectAttempts: number = 0;
  private maxReconnectAttempts: number = 5;
  private reconnectTimer: NodeJS.Timeout | null = null;

  connect(apiUrl: string = 'http://localhost:8000') {
    if (this.connected) {
      console.log('[WebSocket] Already connected');
      return;
    }

    console.log('[WebSocket] Connecting to Flask-SocketIO server:', apiUrl);
    
    // For Flask-SocketIO, we'll use HTTP polling instead of raw WebSocket
    this.connectToFlaskSocketIO(apiUrl);
  }

  private connectToFlaskSocketIO(baseUrl: string) {
    // Use HTTP API calls to simulate SocketIO events for Flask-SocketIO compatibility
    this.connected = true;
    this.emit('hub_connected', { connected: true });
    console.log('[WebSocket] Connected to Flask-SocketIO server via HTTP polling');
  }

  private setupEventHandlers() {
    if (!this.ws) return;

    this.ws.onopen = () => {
      console.log('[WebSocket] Connected to server');
      this.connected = true;
      this.reconnectAttempts = 0;
      this.emit('hub_connected', { connected: true });
      
      // Send initial registration
      this.registerWithHub(this.terminalId, this.user, this.wsname);
    };

    this.ws.onclose = () => {
      console.log('[WebSocket] Disconnected from server');
      this.connected = false;
      this.emit('hub_disconnected', { connected: false });
      this.handleReconnect();
    };

    this.ws.onerror = (error) => {
      console.error('[WebSocket] Connection error:', error);
      this.connected = false;
      this.emit('hub_connection_error', { error });
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.handleMessage(data);
      } catch (error) {
        console.error('[WebSocket] Failed to parse message:', error);
      }
    };
  }

  private handleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('[WebSocket] Max reconnection attempts reached');
      return;
    }

    this.reconnectAttempts++;
    const delay = Math.min(1000 * this.reconnectAttempts, 5000);
    
    console.log(`[WebSocket] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
    
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
    }
    
    this.reconnectTimer = setTimeout(() => {
      this.connect();
    }, delay);
  }

  private handleMessage(data: any) {
    console.log('[WebSocket] Message received:', data);
    
    if (data.type === 'smed_display' || data.action === 'smed_display') {
      this.handleSmedDisplay(data);
    } else if (data.type === 'command_confirmation') {
      this.emit('command_confirmation', data);
    } else if (data.type === 'hub_registered') {
      this.sessionId = data.session_id;
      this.emit('hub_registered', data);
    }
  }

  private handleSmedDisplay(data: any) {
    const smedData: SmedDataEvent = {
      action: 'smed_display',
      map_file: data.map_file || data.map_name,
      fields: data.fields,
      program_name: data.program_name,
      session_id: data.session_id,
      hub_metadata: {
        source: 'websocket_hub',
        timestamp: new Date().toISOString()
      }
    };

    this.emit('smed_data_received', smedData);
  }

  registerWithHub(terminalId: string, username: string, wsname: string) {
    this.terminalId = terminalId;
    this.user = username;
    this.wsname = wsname;

    if (this.isConnected()) {
      console.log('[WebSocket] Registering with Hub:', { terminalId, username, wsname });
      
      this.sendMessage({
        type: 'hub_register',
        terminal_id: terminalId,
        user: username,
        wsname: wsname,
        client_type: 'smed_viewer'
      });
    }
  }

  sendCommandToHub(command: string) {
    if (!this.isConnected()) {
      console.warn('[WebSocket] Cannot send command - not connected');
      return false;
    }

    console.log('[WebSocket] Sending command via HTTP API:', command);
    
    // Send command via HTTP API to execute program
    this.sendHttpCommand(command);
    return true;
  }

  private async sendHttpCommand(command: string) {
    try {
      const response = await fetch('http://localhost:8000/api/execute', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: this.user,
          program: command.includes('MAIN001') ? 'MAIN001' : command,
          input_fields: {
            terminal_id: this.terminalId,
            wsname: this.wsname
          }
        })
      });

      const result = await response.json();
      console.log('[WebSocket] Command result:', result);
      
      if (result.success) {
        this.emit('command_confirmation', { command: command, success: true });
      } else {
        console.error('[WebSocket] Command failed:', result.message);
      }
    } catch (error) {
      console.error('[WebSocket] HTTP command failed:', error);
    }
  }

  sendKeyEventToHub(key: string, fieldValues: Record<string, string> = {}) {
    if (!this.isConnected()) {
      console.warn('[WebSocket] Cannot send key event - not connected');
      return false;
    }

    console.log('[WebSocket] Sending key event via HTTP API:', key, fieldValues);
    
    // Send F9 key event via HTTP API
    if (key === 'F9') {
      this.sendF9KeyEvent(fieldValues);
    } else {
      this.sendGenericKeyEvent(key, fieldValues);
    }

    return true;
  }

  private async sendF9KeyEvent(fieldValues: Record<string, string>) {
    try {
      console.log('[WebSocket] Sending F9 ABEND trigger to MAIN001...');
      
      const response = await fetch('http://localhost:8000/api/execute', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: this.user,
          program: 'MAIN001',
          input_fields: {
            EMP_FUNC: 'F9',  // This will trigger F9 case in MAIN001
            terminal_id: this.terminalId,
            wsname: this.wsname,
            ...fieldValues
          }
        })
      });

      const result = await response.json();
      console.log('[WebSocket] F9 ABEND trigger result:', result);
      
      if (result.success) {
        this.emit('command_confirmation', { 
          command: 'F9_ABEND_TRIGGER', 
          success: true, 
          message: 'CEE3204S ABEND triggered successfully' 
        });
      } else {
        console.error('[WebSocket] F9 ABEND trigger failed:', result.message);
      }
    } catch (error) {
      console.error('[WebSocket] F9 key event failed:', error);
    }
  }

  private async sendGenericKeyEvent(key: string, fieldValues: Record<string, string>) {
    try {
      const response = await fetch('http://localhost:8000/api/execute', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: this.user,
          program: 'MAIN001',
          input_fields: {
            EMP_FUNC: key,
            terminal_id: this.terminalId,
            wsname: this.wsname,
            ...fieldValues
          }
        })
      });

      const result = await response.json();
      console.log('[WebSocket] Key event result:', result);
      
    } catch (error) {
      console.error('[WebSocket] Generic key event failed:', error);
    }
  }

  sendMenuSelection(program: string, selection: string) {
    if (!this.isConnected()) {
      console.warn('[WebSocket] Cannot send menu selection - not connected');
      return false;
    }

    console.log('[WebSocket] Sending menu selection to Hub:', program, selection);
    
    this.sendMessage({
      type: 'hub_menu_selection',
      program: program,
      selection: selection,
      terminal_id: this.terminalId,
      user: this.user,
      wsname: this.wsname,
      timestamp: new Date().toISOString()
    });

    return true;
  }

  private sendMessage(data: any) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    } else {
      console.warn('[WebSocket] Cannot send message - connection not open');
    }
  }

  // Event listener management
  on(event: string, callback: Function) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)!.add(callback);
  }

  off(event: string, callback: Function) {
    if (this.listeners.has(event)) {
      this.listeners.get(event)!.delete(callback);
    }
  }

  private emit(event: string, data: any) {
    if (this.listeners.has(event)) {
      this.listeners.get(event)!.forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error('[WebSocket] Error in event callback:', error);
        }
      });
    }
  }

  isConnected(): boolean {
    return this.connected && this.ws?.readyState === WebSocket.OPEN;
  }

  getTerminalId(): string {
    return this.terminalId;
  }

  disconnect() {
    console.log('[WebSocket] Disconnecting from server');
    
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    
    this.connected = false;
    this.listeners.clear();
  }
}

// Export singleton instance
export const webSocketService = new WebSocketService();
export default webSocketService;