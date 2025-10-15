import React, { useState, useEffect, useCallback } from 'react';
import {
  HomeIcon,
  CodeBracketIcon,
  CommandLineIcon,
  DocumentTextIcon,
  CogIcon,
  BookOpenIcon,
  ChatBubbleLeftRightIcon,
  WrenchScrewdriverIcon,
  ArrowsRightLeftIcon,
} from '@heroicons/react/24/outline';
import Sidebar from './components/Sidebar';
import TabSystem from './components/TabSystem';
import CobolAXPage from './pages/CobolAXPage';
import ClAXPage from './pages/ClAXPage';
import AITransformPage from './pages/AITransformPage';
import ToolsPage from './pages/ToolsPage';
import DocumentationPage from './pages/DocumentationPage';
import SourceConversionPage from './pages/SourceConversionPage';
import DatasetConversionPage from './pages/DatasetConversionPage';
import ChatPage from './pages/ChatPage';
import AspCliWebTerminal from './components/AspCliWebTerminal';
import WorkstationAuthWrapper from './components/WorkstationAuthWrapper';
import MarkdownRenderer from './components/MarkdownRenderer';
import { MenuItem, Tab, Theme } from './types';
import { I18nContext, createI18nContextValue } from './hooks/useI18n';
import { Language } from './i18n';

function App() {
  const [theme, setTheme] = useState<Theme>({ mode: 'dark' });
  const [language, setLanguage] = useState<Language>('ja');
  const [activeMenuId, setActiveMenuId] = useState<string | null>('dashboard');
  const [isLoggedIn, setIsLoggedIn] = useState<boolean>(false);

  useEffect(() => {
    // Check if user is logged in
    const userInfo = localStorage.getItem('openaspUser');
    if (userInfo) {
      try {
        const parsedUser = JSON.parse(userInfo);
        if (parsedUser.app === 'ofasp-ax') {
          setIsLoggedIn(true);
        }
      } catch (error) {
        console.error('Error parsing user info:', error);
        localStorage.removeItem('openaspUser');
      }
    }
  }, []);
  const getDashboardContent = (t: (key: string) => string, tn: (key: string) => any) => (
    <div className="p-8">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
        {t('dashboard.title')}
      </h1>
      <p className="text-gray-600 dark:text-gray-400 mb-8">
        {t('dashboard.subtitle')}
      </p>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 border border-gray-200 dark:border-gray-700">
          <div className="flex items-center mb-4">
            <CodeBracketIcon className="w-8 h-8 text-blue-600 dark:text-blue-400 mr-3" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              {t('dashboard.cobolTitle')}
            </h3>
          </div>
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            {t('dashboard.cobolDescription')}
          </p>
          <div className="text-sm text-gray-500 dark:text-gray-400">
            {tn('dashboard.cobolFeatures').map((feature: string, index: number) => (
              <div key={index}>• {feature}</div>
            ))}
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 border border-gray-200 dark:border-gray-700">
          <div className="flex items-center mb-4">
            <CommandLineIcon className="w-8 h-8 text-green-600 dark:text-green-400 mr-3" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              {t('dashboard.clTitle')}
            </h3>
          </div>
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            {t('dashboard.clDescription')}
          </p>
          <div className="text-sm text-gray-500 dark:text-gray-400">
            {tn('dashboard.clFeatures').map((feature: string, index: number) => (
              <div key={index}>• {feature}</div>
            ))}
          </div>
        </div>
      </div>

      <div className="mt-8 bg-blue-50 dark:bg-blue-900/20 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-blue-900 dark:text-blue-100 mb-2">
          {t('dashboard.processTitle')}
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
          {tn('dashboard.processSteps').map((step: any, index: number) => (
            <div key={index} className="text-center">
              <div className="w-12 h-12 bg-blue-600 text-white rounded-full flex items-center justify-center mx-auto mb-2 text-lg font-bold">
                {index + 1}
              </div>
              <h4 className="font-medium text-blue-900 dark:text-blue-100">{step.title}</h4>
              <p className="text-sm text-blue-700 dark:text-blue-300 mt-1">
                {step.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  const [tabs, setTabs] = useState<Tab[]>([]);
  const [activeTabId, setActiveTabId] = useState<string>('dashboard');
  const [sidebarWidth, setSidebarWidth] = useState(256);

  const handleMenuSelect = useCallback((item: MenuItem) => {
    setActiveMenuId(item.id);

    // 既存のタブを確認
    const existingTab = tabs.find((tab) => tab.id === item.id);
    if (existingTab) {
      setActiveTabId(item.id);
      return;
    }

    // 新しいタブを作成
    let content: React.ReactNode;
    switch (item.id) {
      case 'dashboard':
        return;
      case 'cobol-ax':
        content = <CobolAXPage isDarkMode={theme.mode === 'dark'} />;
        break;
      case 'cl-ax':
        content = <ClAXPage isDarkMode={theme.mode === 'dark'} />;
        break;
      case 'ai-transform':
      case 'ai-transform-main':
        content = <AITransformPage isDarkMode={theme.mode === 'dark'} />;
        break;
      case 'asp-webui':
        content = (
          <div className="h-full">
            <WorkstationAuthWrapper isDarkMode={theme.mode === 'dark'} />
          </div>
        );
        break;
      case 'tools':
        content = <ToolsPage isDarkMode={theme.mode === 'dark'} />;
        break;
      case 'docs':
        content = <DocumentationPage isDarkMode={theme.mode === 'dark'} />;
        break;
      case 'source-conversion':
        content = <SourceConversionPage isDarkMode={theme.mode === 'dark'} />;
        break;
      case 'dataset-conversion':
        content = <DatasetConversionPage isDarkMode={theme.mode === 'dark'} />;
        break;
      case 'chat':
        content = <ChatPage isDarkMode={theme.mode === 'dark'} />;
        break;
      default:
        content = (
          <div className="p-8">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
              {item.label}
            </h2>
            <div className="bg-gray-100 dark:bg-gray-800 rounded-lg p-8 text-center">
              <p className="text-gray-600 dark:text-gray-400">
                この機能は現在開発中です
              </p>
            </div>
          </div>
        );
    }

    const newTab: Tab = {
      id: item.id,
      title: item.label,
      content: content,
      type: 'document',
      timestamp: new Date(),
    };

    setTabs([...tabs, newTab]);
    setActiveTabId(item.id);
  }, [tabs, theme.mode]);

  // テーマおよび言語の初期化
  useEffect(() => {
    const savedTheme = localStorage.getItem('theme') as 'light' | 'dark' | null;
    if (savedTheme) {
      setTheme({ mode: savedTheme });
    } else {
      setTheme({ mode: 'dark' });
      localStorage.setItem('theme', 'dark');
    }

    const savedLanguage = localStorage.getItem('language') as Language | null;
    const envDefaultLang = process.env.REACT_APP_DEFAULT_LANG as Language || 'ja';
    
    if (savedLanguage) {
      setLanguage(savedLanguage);
    } else {
      // 環境変数またはデフォルト値で日本語設定
      setLanguage(envDefaultLang);
      localStorage.setItem('language', envDefaultLang);
    }
  }, []);

  // 言語変更時のタブ更新
  useEffect(() => {
    const i18nValue = createI18nContextValue(language, handleLanguageChange);
    
    // 初期ダッシュボードタブ生成または更新
    setTabs(prevTabs => {
      const existingDashboard = prevTabs.find(tab => tab.id === 'dashboard');
      const newDashboard = {
        id: 'dashboard',
        title: i18nValue.t('common.dashboard'),
        content: getDashboardContent(i18nValue.t, i18nValue.tn),
        type: 'document' as const,
        timestamp: new Date(),
      };

      if (existingDashboard) {
        // 既存のダッシュボードタブ更新
        return prevTabs.map(tab => 
          tab.id === 'dashboard' ? newDashboard : tab
        );
      } else {
        // 新しいダッシュボードタブ追加
        return [newDashboard, ...prevTabs];
      }
    });
  }, [language]);

  // テーマ変更時の処理
  useEffect(() => {
    if (theme.mode === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
    localStorage.setItem('theme', theme.mode);
  }, [theme]);

  // サイドバー幅の監視
  useEffect(() => {
    const checkSidebarWidth = () => {
      const sidebar = document.querySelector('.fixed.left-0');
      if (sidebar) {
        const width = sidebar.getBoundingClientRect().width;
        setSidebarWidth(width);
      }
    };

    checkSidebarWidth();
    const interval = setInterval(checkSidebarWidth, 100);
    return () => clearInterval(interval);
  }, []);

  const getMenuItems = (t: (key: string) => string): MenuItem[] => [
    { id: 'dashboard', label: t('common.dashboard'), icon: <HomeIcon /> },
    { 
      id: 'code-conversion', 
      label: 'コード変換', 
      icon: <ArrowsRightLeftIcon />,
      subItems: [
        { id: 'source-conversion', label: 'ソース変換', icon: <CodeBracketIcon /> },
        { id: 'dataset-conversion', label: 'データセット変換', icon: <DocumentTextIcon /> }
      ]
    },
    { 
      id: 'ai-transform', 
      label: 'AI Transform', 
      icon: <CogIcon />,
      subItems: [
        { id: 'ai-transform-main', label: 'AI変換処理', icon: <CogIcon /> },
        { id: 'asp-webui', label: 'System Command', icon: <CommandLineIcon /> },
      ]
    },
    { id: 'cobol-ax', label: t('navigation.cobolAX'), icon: <CodeBracketIcon /> },
    { id: 'cl-ax', label: t('navigation.clAX'), icon: <CommandLineIcon /> },
    { id: 'tools', label: 'Tools', icon: <WrenchScrewdriverIcon /> },
    { id: 'docs', label: t('common.documentation'), icon: <BookOpenIcon /> },
    { id: 'chat', label: t('common.chat'), icon: <ChatBubbleLeftRightIcon /> },
  ];

  const handleTabSelect = (tabId: string) => {
    setActiveTabId(tabId);
    setActiveMenuId(tabId);
  };

  const handleTabClose = (tabId: string) => {
    const newTabs = tabs.filter((tab) => tab.id !== tabId);
    setTabs(newTabs);

    if (activeTabId === tabId) {
      const newActiveTab = newTabs[newTabs.length - 1];
      if (newActiveTab) {
        setActiveTabId(newActiveTab.id);
        setActiveMenuId(newActiveTab.id);
      }
    }
  };

  const handleThemeToggle = () => {
    setTheme({ mode: theme.mode === 'light' ? 'dark' : 'light' });
  };

  const handleLanguageChange = (newLanguage: Language) => {
    setLanguage(newLanguage);
    localStorage.setItem('language', newLanguage);
  };

  const i18nValue = createI18nContextValue(language, handleLanguageChange);

  // Show login page if not logged in
  if (!isLoggedIn) {
    return (
      <div className="h-screen">
        <iframe 
          src="/login.html" 
          className="w-full h-full border-none"
          title="OpenASP AX Login"
        />
      </div>
    );
  }

  return (
    <I18nContext.Provider value={i18nValue}>
      <div className="h-screen bg-gray-50 dark:bg-gray-950">
        <Sidebar
          menuItems={getMenuItems(i18nValue.t)}
          activeMenuId={activeMenuId}
          onMenuSelect={handleMenuSelect}
          theme={theme}
          onThemeToggle={handleThemeToggle}
          user={{ name: 'Admin', role: i18nValue.t('user.role') }}
        />
        <TabSystem
          tabs={tabs}
          activeTabId={activeTabId}
          onTabSelect={handleTabSelect}
          onTabClose={handleTabClose}
          sidebarWidth={sidebarWidth}
        />
      </div>
    </I18nContext.Provider>
  );
}

export default App;
