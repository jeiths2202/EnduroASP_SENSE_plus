import React, { useState, useCallback, useEffect } from 'react';
import { ComputerDesktopIcon, ExclamationTriangleIcon, CheckCircleIcon } from '@heroicons/react/24/outline';
import WorkstationInput from './WorkstationInput';
import AspCliWebTerminal from './AspCliWebTerminal';
import webSocketService from './websocketService';
import { WorkstationStatus } from '../types/workstation';

interface WorkstationAuthWrapperProps {
  isDarkMode: boolean;
}

interface AuthState {
  isAuthenticated: boolean;
  wsname: string;
  status: WorkstationStatus | null;
  user: string;
}

const WorkstationAuthWrapper: React.FC<WorkstationAuthWrapperProps> = ({ isDarkMode }) => {
  const [authState, setAuthState] = useState<AuthState>({
    isAuthenticated: false,
    wsname: '',
    status: null,
    user: 'admin'
  });
  
  const [workstationName, setWorkstationName] = useState('WSNAME00');
  const [isValid, setIsValid] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState<string>('');
  const [isInitializing, setIsInitializing] = useState(true);

  // 초기화 시 기존 인증 상태 확인
  useEffect(() => {
    const checkExistingAuth = () => {
      const savedAuth = localStorage.getItem('workstationAuth');
      if (savedAuth) {
        try {
          const parsedAuth = JSON.parse(savedAuth);
          if (parsedAuth.wsname && parsedAuth.isAuthenticated) {
            // 저장된 인증 정보가 있으면 자동으로 연결 시도
            setAuthState(parsedAuth);
            // WebSocket 연결도 복원
            if (!webSocketService.isConnected()) {
              webSocketService.connect('http://localhost:8000');
              // Note: The new WebSocket service handles connection and registration automatically
            }
          }
        } catch (error) {
          console.error('Error parsing saved auth:', error);
          localStorage.removeItem('workstationAuth');
        }
      }
      setIsInitializing(false);
    };

    checkExistingAuth();
  }, []);

  // WebSocket 이벤트 핸들러 설정
  useEffect(() => {
    const handleConnectionEstablished = (data: any) => {
      console.log('WebSocket connection established:', data);
    };

    const handleTerminalRegistered = (data: any) => {
      console.log('Terminal registered successfully:', data);
      setError('');
    };

    const handleRegistrationError = (data: { error: string }) => {
      console.error('Terminal registration failed:', data.error);
      setError(`Registration failed: ${data.error}`);
      setIsConnecting(false);
    };

    const handleWorkstationDisabled = (data: { wsname: string }) => {
      if (data.wsname === authState.wsname) {
        setError('Workstation has been disabled by administrator');
        handleLogoff();
      }
    };

    webSocketService.on('session_established', handleConnectionEstablished);
    webSocketService.on('terminal_registered', handleTerminalRegistered);
    webSocketService.on('registration_error', handleRegistrationError);
    webSocketService.on('workstation_disabled', handleWorkstationDisabled);

    return () => {
      webSocketService.off('session_established', handleConnectionEstablished);
      webSocketService.off('terminal_registered', handleTerminalRegistered);
      webSocketService.off('registration_error', handleRegistrationError);
      webSocketService.off('workstation_disabled', handleWorkstationDisabled);
    };
  }, [authState.wsname]);

  const handleWsnameChange = useCallback((wsname: string, valid: boolean) => {
    setWorkstationName(wsname);
    setIsValid(valid);
    setError('');
  }, []);

  const handleLogin = useCallback(async () => {
    if (!isValid || !workstationName) {
      setError('Please enter a valid workstation name');
      return;
    }

    setIsConnecting(true);
    setError('');

    try {
      // 단순히 workstation name으로만 체크
      const isValidWorkstation = await webSocketService.connectWorkstation(workstationName);
      if (!isValidWorkstation) {
        throw new Error('Invalid workstation name');
      }

      // WebSocket 연결
      if (!webSocketService.isConnected()) {
        try {
          await webSocketService.connect('http://localhost:8000');
          console.log('WebSocket connected successfully');
        } catch (error) {
          console.error('Failed to connect WebSocket:', error);
          throw new Error('WebSocket connection failed');
        }
      }

      // 터미널 등록 (간단한 방식)
      const user = authState.user || 'admin';
      webSocketService.registerTerminal('webui', user, workstationName);
      
      // 잠시 대기 후 성공으로 처리
      await new Promise(resolve => setTimeout(resolve, 1000));

      // 인증 성공
      const newAuthState: AuthState = {
        isAuthenticated: true,
        wsname: workstationName,
        status: null, // Simplified authentication doesn't require status
        user: user
      };

      setAuthState(newAuthState);
      
      // 인증 정보 저장
      localStorage.setItem('workstationAuth', JSON.stringify(newAuthState));

    } catch (error: any) {
      console.error('Login failed:', error);
      setError(error.message || 'Connection failed. Please check if the server is running.');
    } finally {
      setIsConnecting(false);
    }
  }, [isValid, workstationName, authState.user]);

  const handleLogoff = useCallback(() => {
    // WebSocket 연결 해제
    webSocketService.disconnect();
    
    // 인증 상태 초기화
    setAuthState({
      isAuthenticated: false,
      wsname: '',
      status: null,
      user: 'admin'
    });
    
    // 저장된 인증 정보 삭제
    localStorage.removeItem('workstationAuth');
    
    // 폼 상태 초기화
    setWorkstationName('WSNAME00');
    setIsValid(false);
    setError('');
  }, []);

  // 초기화 중이면 로딩 표시
  if (isInitializing) {
    return (
      <div className={`min-h-screen flex items-center justify-center ${isDarkMode ? 'bg-gray-900' : 'bg-gray-50'}`}>
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className={`mt-4 text-sm ${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>
            Initializing...
          </p>
        </div>
      </div>
    );
  }

  // 인증되지 않은 경우 로그인 화면 표시
  if (!authState.isAuthenticated) {
    return (
      <div className={`min-h-screen flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8 ${isDarkMode ? 'bg-gray-900' : 'bg-gray-50'}`}>
        <div className="max-w-md w-full space-y-8">
          <div className="text-center">
            <ComputerDesktopIcon className={`mx-auto h-12 w-12 ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`} />
            <h2 className={`mt-6 text-3xl font-extrabold ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
              ASP System Terminal
            </h2>
            <p className={`mt-2 text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
              Enter your workstation name to connect
            </p>
          </div>

          <div className={`mt-8 space-y-6 p-8 rounded-lg shadow-md ${isDarkMode ? 'bg-gray-800' : 'bg-white'}`}>
            <WorkstationInput
              defaultWsname={workstationName}
              onWsnameChange={handleWsnameChange}
              disabled={isConnecting}
              showStatus={true}
              allowEnableDisable={false}
            />

            {error && (
              <div className="rounded-md bg-red-50 p-4">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <ExclamationTriangleIcon className="h-5 w-5 text-red-400" />
                  </div>
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-red-800">Connection Error</h3>
                    <div className="mt-2 text-sm text-red-700">
                      <p>{error}</p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            <div>
              <button
                onClick={handleLogin}
                disabled={!isValid || isConnecting}
                className={`group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 ${
                  !isValid || isConnecting
                    ? 'bg-gray-400 cursor-not-allowed'
                    : 'bg-blue-600 hover:bg-blue-700'
                }`}
              >
                {isConnecting ? (
                  <div className="flex items-center">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Connecting...
                  </div>
                ) : (
                  'Connect'
                )}
              </button>
            </div>

            <div className={`text-xs ${isDarkMode ? 'text-gray-400' : 'text-gray-500'} text-center`}>
              <p>This will connect to the ASP System Command Server</p>
              <p>and register your workstation for terminal access.</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // 인증된 경우 터미널 화면 표시
  return (
    <div className="h-screen flex flex-col">
      {/* 상단 워크스테이션 정보 바 */}
      <div className={`px-4 py-2 border-b flex items-center justify-between ${
        isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
      }`}>
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <ComputerDesktopIcon className={`h-5 w-5 ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`} />
            <span className={`font-medium ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
              Workstation: {authState.wsname}
            </span>
          </div>
          
          {authState.status && (
            <div className="flex items-center space-x-2">
              <CheckCircleIcon className={`h-4 w-4 ${
                authState.status.status === 'ON' && authState.status.connected 
                  ? 'text-green-500' 
                  : authState.status.status === 'ON' 
                  ? 'text-yellow-500' 
                  : 'text-red-500'
              }`} />
              <span className={`text-sm ${
                authState.status.status === 'ON' && authState.status.connected 
                  ? 'text-green-600' 
                  : authState.status.status === 'ON' 
                  ? 'text-yellow-600' 
                  : 'text-red-600'
              }`}>
                {authState.status.status === 'ON' && authState.status.connected 
                  ? 'Active & Connected' 
                  : authState.status.status === 'ON' 
                  ? 'Active (Not Connected)' 
                  : 'Disabled'}
              </span>
            </div>
          )}

          <div className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
            User: {authState.user}
          </div>
        </div>

        <button
          onClick={handleLogoff}
          className={`px-3 py-1 text-sm font-medium rounded-md transition-colors ${
            isDarkMode 
              ? 'text-gray-300 bg-gray-700 hover:bg-gray-600 focus:ring-gray-500' 
              : 'text-gray-700 bg-gray-100 hover:bg-gray-200 focus:ring-gray-500'
          } focus:outline-none focus:ring-2 focus:ring-offset-1`}
        >
          LOGOFF
        </button>
      </div>

      {/* 터미널 영역 */}
      <div className="flex-1 overflow-hidden">
        <AspCliWebTerminal 
          isDarkMode={isDarkMode}
          workstationName={authState.wsname}
          user={authState.user}
        />
      </div>
    </div>
  );
};

export default WorkstationAuthWrapper;