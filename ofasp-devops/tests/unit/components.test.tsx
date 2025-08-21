import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { I18nContext } from '../../src/hooks/useI18n'
import DevOpsDashboard from '../../src/pages/DevOpsDashboard'
import DevOpsCobolPage from '../../src/pages/DevOpsCobolPage'
import DevOpsClPage from '../../src/pages/DevOpsClPage'

// Mock i18n context
const mockI18nContext = {
  language: 'en' as const,
  setLanguage: jest.fn(),
  t: (key: string, params?: Record<string, string>) => {
    const translations: Record<string, string> = {
      'common.download': 'Download',
      'common.selectFile': 'Select File',
      'languages.java': 'Java',
      'languages.c': 'C',
      'languages.shell': 'Shell',
      'languages.python': 'Python',
      'languages.javascript': 'JavaScript',
    }
    let result = translations[key] || key
    if (params) {
      Object.entries(params).forEach(([paramKey, paramValue]) => {
        result = result.replace(new RegExp(`\\{${paramKey}\\}`, 'g'), paramValue)
      })
    }
    return result
  },
  tn: (key: string) => {
    const nestedTranslations: Record<string, string[]> = {
      'clAX.commands.fileOps': ['CPYF', 'DLTF', 'CRTPF'],
      'clAX.commands.programExec': ['CALL', 'SBMJOB', 'EVOKE'],
      'clAX.commands.variables': ['DCL', 'CHGVAR', 'RTVJOBA'],
    }
    return nestedTranslations[key] || []
  },
}

const renderWithI18n = (component: React.ReactElement) => {
  return render(
    <I18nContext.Provider value={mockI18nContext}>
      {component}
    </I18nContext.Provider>
  )
}

describe('DevOps Dashboard Components', () => {
  describe('DevOpsDashboard', () => {
    it('renders dashboard with main elements', () => {
      renderWithI18n(<DevOpsDashboard isDarkMode={false} />)
      
      expect(screen.getByText('DevOps Dashboard')).toBeInTheDocument()
      expect(screen.getByText('Real-time CI/CD Pipeline Monitoring & Legacy System Modernization')).toBeInTheDocument()
      expect(screen.getByText('System Operational')).toBeInTheDocument()
    })

    it('displays pipeline metrics', () => {
      renderWithI18n(<DevOpsDashboard isDarkMode={false} />)
      
      expect(screen.getByText('Active Pipelines')).toBeInTheDocument()
      expect(screen.getByText('Real-time Activity')).toBeInTheDocument()
      expect(screen.getByText('DevOps Architecture')).toBeInTheDocument()
    })

    it('handles dark mode correctly', () => {
      const { container } = renderWithI18n(<DevOpsDashboard isDarkMode={true} />)
      
      // Check if dark mode classes are applied
      expect(container.firstChild).toHaveClass('dark:bg-gray-900')
    })
  })

  describe('DevOpsCobolPage', () => {
    it('renders COBOL converter interface', () => {
      renderWithI18n(<DevOpsCobolPage isDarkMode={false} />)
      
      expect(screen.getByText('DevOps COBOL Converter')).toBeInTheDocument()
      expect(screen.getByText('COBOL to Modern Language Conversion with Automated CI/CD Pipeline')).toBeInTheDocument()
      expect(screen.getByText('Target Language')).toBeInTheDocument()
    })

    it('displays target language options', () => {
      renderWithI18n(<DevOpsCobolPage isDarkMode={false} />)
      
      expect(screen.getByText('Java')).toBeInTheDocument()
      expect(screen.getByText('C')).toBeInTheDocument()
      expect(screen.getByText('Shell')).toBeInTheDocument()
      expect(screen.getByText('Python')).toBeInTheDocument()
    })

    it('handles language selection', async () => {
      renderWithI18n(<DevOpsCobolPage isDarkMode={false} />)
      
      const pythonButton = screen.getByRole('button', { name: /Python/i })
      fireEvent.click(pythonButton)
      
      expect(pythonButton.closest('button')).toHaveClass('bg-blue-50')
    })

    it('handles file upload', async () => {
      renderWithI18n(<DevOpsCobolPage isDarkMode={false} />)
      
      const fileInput = screen.getByLabelText(/Select COBOL File/i)
      const file = new File(['IDENTIFICATION DIVISION.'], 'test.cbl', { type: 'text/plain' })
      
      fireEvent.change(fileInput, { target: { files: [file] } })
      
      // The file input should be handled (though we can't directly test the file reading)
      expect(fileInput).toBeInTheDocument()
    })

    it('enables convert button when source code is present', async () => {
      renderWithI18n(<DevOpsCobolPage isDarkMode={false} />)
      
      const textarea = screen.getByPlaceholderText(/Enter COBOL source code/i)
      const convertButton = screen.getByRole('button', { name: /Convert/i })
      
      expect(convertButton).toBeDisabled()
      
      fireEvent.change(textarea, { target: { value: 'IDENTIFICATION DIVISION.' } })
      
      expect(convertButton).not.toBeDisabled()
    })
  })

  describe('DevOpsClPage', () => {
    it('renders CL converter interface', () => {
      renderWithI18n(<DevOpsClPage isDarkMode={false} />)
      
      expect(screen.getByText('DevOps CL Converter')).toBeInTheDocument()
      expect(screen.getByText('IBM i CL to Modern Language Conversion with Automated CI/CD Pipeline')).toBeInTheDocument()
    })

    it('displays CL command reference', () => {
      renderWithI18n(<DevOpsClPage isDarkMode={false} />)
      
      expect(screen.getByText('CL Command Reference')).toBeInTheDocument()
      expect(screen.getByText('File Operations')).toBeInTheDocument()
      expect(screen.getByText('Program Execution')).toBeInTheDocument()
      expect(screen.getByText('Variable Handling')).toBeInTheDocument()
    })

    it('shows pipeline status indicators', () => {
      renderWithI18n(<DevOpsClPage isDarkMode={false} />)
      
      expect(screen.getByText('Ready for Deployment')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /Deploy to Pipeline/i })).toBeInTheDocument()
    })
  })

  describe('Integration Tests', () => {
    it('handles conversion workflow', async () => {
      renderWithI18n(<DevOpsCobolPage isDarkMode={false} />)
      
      // Enter source code
      const textarea = screen.getByPlaceholderText(/Enter COBOL source code/i)
      fireEvent.change(textarea, { 
        target: { value: 'IDENTIFICATION DIVISION.\nPROGRAM-ID. HELLO.' } 
      })
      
      // Select target language
      const javaButton = screen.getByRole('button', { name: /Java/i })
      fireEvent.click(javaButton)
      
      // Click convert
      const convertButton = screen.getByRole('button', { name: /Convert/i })
      fireEvent.click(convertButton)
      
      // Check if conversion starts
      await waitFor(() => {
        expect(screen.getByText(/Converting.../i)).toBeInTheDocument()
      })
    })

    it('maintains state consistency across interactions', () => {
      renderWithI18n(<DevOpsCobolPage isDarkMode={false} />)
      
      const textarea = screen.getByPlaceholderText(/Enter COBOL source code/i)
      const pythonButton = screen.getByRole('button', { name: /Python/i })
      
      // Set source code
      fireEvent.change(textarea, { target: { value: 'TEST CODE' } })
      expect(textarea).toHaveValue('TEST CODE')
      
      // Change language
      fireEvent.click(pythonButton)
      
      // Source code should be preserved
      expect(textarea).toHaveValue('TEST CODE')
    })
  })

  describe('Error Handling', () => {
    it('handles missing translations gracefully', () => {
      const contextWithMissingTranslations = {
        ...mockI18nContext,
        t: (key: string) => key, // Return key if translation missing
      }
      
      render(
        <I18nContext.Provider value={contextWithMissingTranslations}>
          <DevOpsDashboard isDarkMode={false} />
        </I18nContext.Provider>
      )
      
      // Should not crash even with missing translations
      expect(screen.getByText('DevOps Dashboard')).toBeInTheDocument()
    })

    it('handles empty form submission', () => {
      renderWithI18n(<DevOpsCobolPage isDarkMode={false} />)
      
      const convertButton = screen.getByRole('button', { name: /Convert/i })
      
      // Button should be disabled with empty source
      expect(convertButton).toBeDisabled()
      
      // Should not crash when clicked while disabled
      fireEvent.click(convertButton)
      expect(convertButton).toBeDisabled()
    })
  })
})