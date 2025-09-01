import React, { useState, useEffect, useRef } from 'react';
import webSocketService from '../webSocketService';
import './TerminalComponent.css';

interface SmedField {
  name: string;
  row: number;
  col: number;
  length: number;
  value?: string;
  prompt?: string;
  type?: string;
}

interface TerminalComponentProps {
  isVisible: boolean;
  onClose: () => void;
}

const TerminalComponent: React.FC<TerminalComponentProps> = ({ isVisible, onClose }) => {
  const [isConnected, setIsConnected] = useState(false);
  const [terminal, setTerminal] = useState<string[]>([]);
  const [command, setCommand] = useState('');
  const [smedFields, setSmedFields] = useState<SmedField[]>([]);
  const [showSmedDisplay, setShowSmedDisplay] = useState(false);
  const terminalRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!isVisible) return;

    // Connect to Flask-SocketIO server
    webSocketService.connect('http://localhost:8000');
    
    // Register with Hub
    webSocketService.registerWithHub('webui_terminal', 'admin', 'WSNAME00');

    // Set up event handlers
    const handleConnect = () => {
      setIsConnected(true);
      addTerminalLine('Connected to WebSocket Hub at localhost:8000');
    };

    const handleDisconnect = () => {
      setIsConnected(false);
      addTerminalLine('Disconnected from WebSocket Hub');
    };

    const handleSmedData = (data: any) => {
      console.log('[Terminal] SMED data received:', data);
      
      if (data.fields && Array.isArray(data.fields)) {
        setSmedFields(data.fields);
        setShowSmedDisplay(true);
        addTerminalLine(`SMED display received: ${data.map_file || 'Unknown'}`);
      } else if (data.map_file) {
        // Handle SMED map format
        const fields: SmedField[] = [];
        
        // Convert data to SMED fields format
        if (data.fields) {
          Object.entries(data.fields).forEach(([key, value]: [string, any]) => {
            if (typeof value === 'object' && value.row !== undefined && value.col !== undefined) {
              fields.push({
                name: key,
                row: value.row,
                col: value.col,
                length: value.length || 10,
                value: value.value || '',
                prompt: value.prompt || '',
                type: value.type || 'display'
              });
            }
          });
        }
        
        setSmedFields(fields);
        setShowSmedDisplay(true);
        addTerminalLine(`SMED map loaded: ${data.map_file}`);
      }
    };

    const handleCommandConfirmation = (data: any) => {
      addTerminalLine(`Command confirmed: ${data.command || 'Unknown'}`);
    };

    webSocketService.on('hub_connected', handleConnect);
    webSocketService.on('hub_disconnected', handleDisconnect);
    webSocketService.on('smed_data_received', handleSmedData);
    webSocketService.on('command_confirmation', handleCommandConfirmation);

    // Focus input when terminal becomes visible
    setTimeout(() => {
      if (inputRef.current) {
        inputRef.current.focus();
      }
    }, 100);

    return () => {
      webSocketService.off('hub_connected', handleConnect);
      webSocketService.off('hub_disconnected', handleDisconnect);
      webSocketService.off('smed_data_received', handleSmedData);
      webSocketService.off('command_confirmation', handleCommandConfirmation);
      webSocketService.disconnect();
    };
  }, [isVisible]);

  const addTerminalLine = (line: string) => {
    const timestamp = new Date().toLocaleTimeString();
    setTerminal(prev => [...prev, `[${timestamp}] ${line}`]);
    
    // Auto-scroll to bottom
    setTimeout(() => {
      if (terminalRef.current) {
        terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
      }
    }, 10);
  };

  const handleCommandSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!command.trim()) return;
    
    addTerminalLine(`> ${command}`);
    
    if (command.toLowerCase() === 'clear') {
      setTerminal([]);
      setCommand('');
      return;
    }
    
    if (command.toLowerCase() === 'main001' || command.toLowerCase() === 'call main001') {
      // Execute MAIN001.java
      const success = webSocketService.sendCommandToHub('CALL PGM-MAIN001.TESTLIB,VOL-DISK01');
      if (success) {
        addTerminalLine('Executing MAIN001...');
      } else {
        addTerminalLine('Failed to send command - not connected to Hub');
      }
    } else {
      // Send generic command
      const success = webSocketService.sendCommandToHub(command);
      if (success) {
        addTerminalLine(`Command sent: ${command}`);
      } else {
        addTerminalLine('Failed to send command - not connected to Hub');
      }
    }
    
    setCommand('');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'F9') {
      e.preventDefault();
      addTerminalLine('> F9 key pressed - triggering ABEND test');
      
      // Send F9 key event to trigger ABEND in MAIN001
      const success = webSocketService.sendKeyEventToHub('F9', {});
      if (success) {
        addTerminalLine('F9 ABEND trigger sent to MAIN001');
      } else {
        addTerminalLine('Failed to send F9 key - not connected to Hub');
      }
    }
  };


  const renderSmedDisplay = () => {
    if (!showSmedDisplay || smedFields.length === 0) return null;

    return (
      <div className="smed-overlay">
        <div className="smed-container">
          <div className="smed-header">
            <h3>SMED Display</h3>
            <button onClick={() => setShowSmedDisplay(false)} className="smed-close">×</button>
          </div>
          <div className="smed-screen">
            {smedFields.map((field, index) => {
              const style = {
                position: 'absolute' as const,
                top: `${field.row * 20}px`,
                left: `${field.col * 10}px`,
                color: '#00ff00',
                fontFamily: 'monospace',
                fontSize: '14px'
              };

              if (field.type === 'input') {
                return (
                  <input
                    key={index}
                    type="text"
                    style={{
                      ...style,
                      background: 'transparent',
                      border: '1px solid #00ff00',
                      color: '#00ff00',
                      width: `${field.length * 10}px`
                    }}
                    maxLength={field.length}
                    defaultValue={field.value}
                    onKeyDown={handleKeyDown}
                  />
                );
              }

              return (
                <div key={index} style={style}>
                  {field.prompt || field.value}
                </div>
              );
            })}
          </div>
          <div className="smed-footer">
            Press F9 to trigger ABEND | F3 to close
          </div>
        </div>
      </div>
    );
  };

  if (!isVisible) return null;

  return (
    <div className="terminal-overlay">
      <div className="terminal-window">
        <div className="terminal-header">
          <span className="terminal-title">Web Terminal - {isConnected ? 'Connected' : 'Disconnected'}</span>
          <button onClick={onClose} className="terminal-close">×</button>
        </div>
        
        <div className="terminal-body" ref={terminalRef}>
          <div className="terminal-output">
            {terminal.map((line, index) => (
              <div key={index} className="terminal-line">{line}</div>
            ))}
          </div>
        </div>
        
        <form onSubmit={handleCommandSubmit} className="terminal-input-form">
          <span className="terminal-prompt">$</span>
          <input
            ref={inputRef}
            type="text"
            value={command}
            onChange={(e) => setCommand(e.target.value)}
            onKeyDown={handleKeyDown}
            className="terminal-input"
            placeholder="Enter command (try 'main001' or 'clear')"
            disabled={!isConnected}
          />
        </form>
        
        <div className="terminal-help">
          Commands: main001 (execute MAIN001), clear | Keys: F9 (ABEND test)
        </div>
      </div>
      
      {renderSmedDisplay()}
    </div>
  );
};

export default TerminalComponent;