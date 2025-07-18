import React, { useState, useEffect, useRef } from 'react';
import { 
  CloudArrowUpIcon, 
  CloudArrowDownIcon, 
  EyeIcon, 
  TrashIcon,
  DocumentTextIcon,
  PlayIcon,
  PlusIcon
} from '@heroicons/react/24/outline';

interface Field {
  id: string;
  name: string;
  type: 'text' | 'input' | 'output' | 'button';
  x: number;
  y: number;
  width: number;
  height: number;
  value: string;
  cssClass: string;
  attributes: string;
  backgroundColor: string;
  textColor: string;
}

interface MapData {
  version: string;
  screenSize: { cols: number; rows: number };
  created: string;
  fieldCount: number;
  fields: Field[];
}

interface ASPMapEditorProps {
  isDarkMode: boolean;
}

const ASPMapEditor: React.FC<ASPMapEditorProps> = ({ isDarkMode }) => {
  const [fields, setFields] = useState<Map<string, Field>>(new Map());
  const [selectedField, setSelectedField] = useState<string | null>(null);
  const [selectedFields, setSelectedFields] = useState<Set<string>>(new Set());
  const [fieldCounter, setFieldCounter] = useState(0);
  const [draggedFieldType, setDraggedFieldType] = useState<string | null>(null);
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);
  const [mapDataOutput, setMapDataOutput] = useState('');
  const [smedFiles, setSmedFiles] = useState<string[]>([]);
  const [statusMessage, setStatusMessage] = useState('드래그 앤 드롭으로 필드를 추가하고, 클릭으로 선택하여 속성을 편집하세요.');
  
  const screenPanelRef = useRef<HTMLDivElement>(null);
  const [fieldProperties, setFieldProperties] = useState({
    id: '',
    name: '',
    width: 10,
    height: 1,
    value: '',
    cssClass: '',
    attributes: 'normal',
    backgroundColor: '#00ff00',
    textColor: '#ffffff'
  });

  const charWidth = 10;
  const charHeight = 20;
  const cols = 80;
  const rows = 24;

  useEffect(() => {
    updateMapDataOutput();
  }, [fields]);

  useEffect(() => {
    loadSmedFiles();
  }, []);

  const loadSmedFiles = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/smed/files');
      if (response.ok) {
        const data = await response.json();
        setSmedFiles(data.files || []);
      } else {
        console.error('Failed to load SMED files');
      }
    } catch (error) {
      console.error('Error loading SMED files:', error);
    }
  };

  const fieldTypes = [
    { type: 'text', label: '📝 Text Field', icon: DocumentTextIcon },
    { type: 'input', label: '📥 Input Field', icon: PlusIcon },
    { type: 'output', label: '📤 Output Field', icon: DocumentTextIcon },
    { type: 'button', label: '🔘 Button Field', icon: PlayIcon }
  ];

  const getDefaultValue = (type: string) => {
    switch (type) {
      case 'text': return 'Text Label';
      case 'input': return '_'.repeat(10);
      case 'output': return 'Output';
      case 'button': return 'Button';
      default: return 'Field';
    }
  };

  const createField = (type: string, x: number, y: number) => {
    const newCounter = fieldCounter + 1;
    setFieldCounter(newCounter);
    
    const fieldId = `FIELD_${newCounter.toString().padStart(3, '0')}`;
    
    const newField: Field = {
      id: fieldId,
      name: `${type.toUpperCase()}_${newCounter}`,
      type: type as 'text' | 'input' | 'output' | 'button',
      x: Math.floor(x / charWidth),
      y: Math.floor(y / charHeight),
      width: 10,
      height: 1,
      value: getDefaultValue(type),
      cssClass: '',
      attributes: 'normal',
      backgroundColor: '#00ff00',
      textColor: '#ffffff'
    };

    setFields(new Map(fields.set(fieldId, newField)));
    setSelectedField(fieldId);
    updateFieldProperties(newField);
    setStatusMessage(`${fieldId} 필드가 추가되었습니다.`);
  };

  const updateFieldProperties = (field: Field) => {
    setFieldProperties({
      id: field.id,
      name: field.name,
      width: field.width,
      height: field.height,
      value: field.value,
      cssClass: field.cssClass,
      attributes: field.attributes,
      backgroundColor: field.backgroundColor,
      textColor: field.textColor
    });
  };

  const handleFieldPropertyChange = (property: string, value: any) => {
    setFieldProperties(prev => ({ ...prev, [property]: value }));
    
    if (selectedField) {
      const field = fields.get(selectedField);
      if (field) {
        const updatedField = { ...field, [property]: value };
        setFields(new Map(fields.set(selectedField, updatedField)));
      }
    }
  };

  const handleDragStart = (e: React.DragEvent, fieldType: string) => {
    e.dataTransfer.setData('text/plain', fieldType);
    setDraggedFieldType(fieldType);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const fieldType = e.dataTransfer.getData('text/plain');
    
    if (screenPanelRef.current) {
      const rect = screenPanelRef.current.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      
      createField(fieldType, x, y);
    }
    
    setDraggedFieldType(null);
  };

  const handleFieldClick = (fieldId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    
    if (e.shiftKey) {
      // Multi-select mode
      const newSelectedFields = new Set(selectedFields);
      if (newSelectedFields.has(fieldId)) {
        newSelectedFields.delete(fieldId);
      } else {
        newSelectedFields.add(fieldId);
      }
      setSelectedFields(newSelectedFields);
    } else {
      // Single select mode
      setSelectedField(fieldId);
      setSelectedFields(new Set());
      
      const field = fields.get(fieldId);
      if (field) {
        updateFieldProperties(field);
      }
    }
  };

  const deleteSelectedField = () => {
    if (selectedField) {
      const newFields = new Map(fields);
      newFields.delete(selectedField);
      setFields(newFields);
      setSelectedField(null);
      setStatusMessage(`${selectedField} 필드가 삭제되었습니다.`);
    }
  };

  const clearAllFields = () => {
    setFields(new Map());
    setSelectedField(null);
    setSelectedFields(new Set());
    setFieldCounter(0);
    setStatusMessage('모든 필드가 삭제되었습니다.');
  };

  const updateMapDataOutput = () => {
    const mapData: MapData = {
      version: '1.0',
      screenSize: { cols, rows },
      created: new Date().toISOString(),
      fieldCount: fields.size,
      fields: Array.from(fields.values()).map(field => ({
        id: field.id,
        name: field.name,
        type: field.type,
        x: field.x,
        y: field.y,
        width: field.width,
        height: field.height,
        value: field.value,
        cssClass: field.cssClass,
        attributes: field.attributes,
        backgroundColor: field.backgroundColor,
        textColor: field.textColor
      }))
    };
    
    setMapDataOutput(JSON.stringify(mapData, null, 2));
  };

  const loadSmedFile = async (filename: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/smed/content/${filename}`);
      if (response.ok) {
        const content = await response.text();
        parseSmedContent(content);
        setStatusMessage(`SMED 파일 ${filename}을 불러왔습니다.`);
      } else {
        setStatusMessage(`SMED 파일 ${filename} 불러오기 실패`);
      }
    } catch (error) {
      setStatusMessage(`SMED 파일 불러오기 오류: ${error}`);
    }
  };

  const parseSmedContent = (content: string) => {
    const lines = content.split(/\r?\n/).map(line => line.trim());
    const newFields = new Map<string, Field>();
    let counter = 0;

    lines.forEach(line => {
      if (line.startsWith('ITEM')) {
        const match = line.match(/ITEM\s+(\S+)\s+TYPE=(\w)\s+POS=\((\d+),(\d+)\)\s+PROMPT=\"(.+?)\"(?:\s+COLOR=(#[A-Fa-f0-9]{6}|\w+))?/);
        if (match) {
          const [_, name, type, row, col, prompt, color] = match;
          counter++;
          
          const fieldId = `FIELD_${counter.toString().padStart(3, '0')}`;
          
          const field: Field = {
            id: fieldId,
            name: name,
            type: type === 'N' ? 'input' : type === 'A' ? 'output' : type === 'X' ? 'button' : 'text',
            x: parseInt(col) - 1,
            y: parseInt(row) - 1,
            width: prompt.length || 10,
            height: 1,
            value: prompt,
            cssClass: '',
            attributes: 'normal',
            backgroundColor: color || '#00ff00',
            textColor: '#ffffff'
          };
          
          newFields.set(fieldId, field);
        }
      }
    });

    setFields(newFields);
    setFieldCounter(counter);
  };

  const exportSmedFile = () => {
    const lines = ['MAPNAME GENERATEDMAP', ''];
    let groupCount = 0;

    Array.from(fields.values()).forEach((field, index) => {
      if (index % 5 === 0) {
        groupCount++;
        lines.push(`GROUP GRP${groupCount.toString().padStart(3, '0')}`);
      }
      
      const typeMap: { [key: string]: string } = {
        'input': 'N',
        'output': 'A',
        'text': 'T',
        'button': 'X'
      };
      
      const itemLine = `  ITEM ${field.name} TYPE=${typeMap[field.type] || 'T'} POS=(${field.y + 1},${field.x + 1}) PROMPT="${field.value}"${field.backgroundColor ? ` COLOR=${field.backgroundColor}` : ''}`;
      lines.push(itemLine);
    });

    const smedContent = lines.join('\n');
    const blob = new Blob([smedContent], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'generated_map.smed';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    setStatusMessage('SMED 파일이 다운로드되었습니다.');
  };

  const showPreview = () => {
    setIsPreviewOpen(true);
  };

  const closePreview = () => {
    setIsPreviewOpen(false);
  };

  return (
    <div className="h-full bg-gray-900 text-white p-6 overflow-hidden">
      <div className="max-w-7xl mx-auto h-full flex flex-col">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-white mb-2">ASP SMED Map Editor</h1>
          <p className="text-gray-400">드래그 앤 드롭으로 필드를 추가하고 SMED 맵을 편집하세요</p>
        </div>

        {/* Toolbar */}
        <div className="bg-gray-800 rounded-lg p-4 mb-6">
          <div className="flex flex-wrap gap-4 items-center">
            {/* Field Types */}
            <div className="flex gap-2">
              {fieldTypes.map(({ type, label }) => (
                <div
                  key={type}
                  className="px-3 py-2 bg-gray-700 hover:bg-gray-600 border border-gray-600 rounded cursor-pointer transition-colors"
                  draggable
                  onDragStart={(e) => handleDragStart(e, type)}
                >
                  {label}
                </div>
              ))}
            </div>

            {/* Action Buttons */}
            <div className="flex gap-2 ml-auto">
              <button
                onClick={showPreview}
                className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded flex items-center gap-2 transition-colors"
              >
                <EyeIcon className="w-4 h-4" />
                미리보기
              </button>
              
              <select
                className="px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
                onChange={(e) => e.target.value && loadSmedFile(e.target.value)}
                value=""
              >
                <option value="">SMED 불러오기</option>
                {smedFiles.map(file => (
                  <option key={file} value={file}>{file}</option>
                ))}
              </select>
              
              <button
                onClick={exportSmedFile}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded flex items-center gap-2 transition-colors"
              >
                <CloudArrowDownIcon className="w-4 h-4" />
                SMED 내보내기
              </button>
              
              <button
                onClick={clearAllFields}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 rounded flex items-center gap-2 transition-colors"
              >
                <TrashIcon className="w-4 h-4" />
                전체삭제
              </button>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 flex gap-6 overflow-hidden">
          {/* Screen Panel */}
          <div className="flex-1 flex flex-col">
            <div
              ref={screenPanelRef}
              className="bg-black border-2 border-green-400 relative overflow-hidden"
              style={{
                width: `${cols * charWidth}px`,
                height: `${rows * charHeight}px`,
                maxWidth: '100%',
                maxHeight: '100%'
              }}
              onDragOver={handleDragOver}
              onDrop={handleDrop}
            >
              {/* Grid */}
              <div className="absolute inset-0 opacity-30">
                {Array.from({ length: cols + 1 }, (_, i) => (
                  <div
                    key={`v-${i}`}
                    className="absolute w-px h-full bg-gray-700"
                    style={{ left: `${i * charWidth}px` }}
                  />
                ))}
                {Array.from({ length: rows + 1 }, (_, i) => (
                  <div
                    key={`h-${i}`}
                    className="absolute w-full h-px bg-gray-700"
                    style={{ top: `${i * charHeight}px` }}
                  />
                ))}
              </div>

              {/* Fields */}
              {Array.from(fields.values()).map(field => (
                <div
                  key={field.id}
                  className={`absolute cursor-pointer border font-mono text-sm transition-all ${
                    selectedField === field.id ? 'border-yellow-400 bg-yellow-400/20' : 'border-green-400 bg-green-400/10'
                  } ${selectedFields.has(field.id) ? 'border-orange-400 bg-orange-400/20' : ''}`}
                  style={{
                    left: `${field.x * charWidth}px`,
                    top: `${field.y * charHeight}px`,
                    width: `${field.width * charWidth}px`,
                    height: `${field.height * charHeight}px`,
                    backgroundColor: field.backgroundColor + '20',
                    color: field.textColor,
                    padding: '2px',
                    fontSize: '12px',
                    lineHeight: '16px'
                  }}
                  onClick={(e) => handleFieldClick(field.id, e)}
                >
                  {field.value.substring(0, field.width * field.height)}
                </div>
              ))}

              {/* Grid Info */}
              <div className="absolute top-2 right-2 text-xs text-gray-500">
                80 Cols x 24 Rows
              </div>
            </div>
          </div>

          {/* Properties Panel */}
          <div className="w-80 bg-gray-800 rounded-lg p-4">
            <h3 className="text-lg font-semibold mb-4">필드 속성</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">필드 ID</label>
                <input
                  type="text"
                  value={fieldProperties.id}
                  readOnly
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-gray-400"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">필드명</label>
                <input
                  type="text"
                  value={fieldProperties.name}
                  onChange={(e) => handleFieldPropertyChange('name', e.target.value)}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
                />
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-sm font-medium mb-1">폭</label>
                  <input
                    type="number"
                    value={fieldProperties.width}
                    onChange={(e) => handleFieldPropertyChange('width', parseInt(e.target.value))}
                    min="1"
                    max="80"
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">높이</label>
                  <input
                    type="number"
                    value={fieldProperties.height}
                    onChange={(e) => handleFieldPropertyChange('height', parseInt(e.target.value))}
                    min="1"
                    max="5"
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">기본값</label>
                <input
                  type="text"
                  value={fieldProperties.value}
                  onChange={(e) => handleFieldPropertyChange('value', e.target.value)}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">속성</label>
                <select
                  value={fieldProperties.attributes}
                  onChange={(e) => handleFieldPropertyChange('attributes', e.target.value)}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
                >
                  <option value="normal">일반</option>
                  <option value="readonly">읽기전용</option>
                  <option value="required">필수입력</option>
                  <option value="disabled">비활성화</option>
                  <option value="hidden">숨김</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-sm font-medium mb-1">배경색</label>
                  <input
                    type="color"
                    value={fieldProperties.backgroundColor}
                    onChange={(e) => handleFieldPropertyChange('backgroundColor', e.target.value)}
                    className="w-full h-10 bg-gray-700 border border-gray-600 rounded cursor-pointer"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">텍스트색</label>
                  <input
                    type="color"
                    value={fieldProperties.textColor}
                    onChange={(e) => handleFieldPropertyChange('textColor', e.target.value)}
                    className="w-full h-10 bg-gray-700 border border-gray-600 rounded cursor-pointer"
                  />
                </div>
              </div>

              <button
                onClick={deleteSelectedField}
                disabled={!selectedField}
                className="w-full px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-gray-600 rounded transition-colors"
              >
                선택된 필드 삭제
              </button>
            </div>
          </div>
        </div>

        {/* Status Bar */}
        <div className="mt-4 bg-gray-800 rounded px-4 py-2 text-sm text-gray-300">
          {statusMessage}
        </div>
      </div>

      {/* Preview Modal */}
      {isPreviewOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-80 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-6 max-w-4xl max-h-[90vh] overflow-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-bold">SMED 화면 미리보기</h3>
              <button
                onClick={closePreview}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 rounded transition-colors"
              >
                닫기
              </button>
            </div>
            
            <div
              className="bg-black border-2 border-green-400 relative"
              style={{
                width: `${cols * 10}px`,
                height: `${rows * 20}px`,
                fontFamily: 'monospace',
                fontSize: '14px',
                lineHeight: '20px'
              }}
            >
              {Array.from(fields.values()).map(field => (
                <div
                  key={field.id}
                  className="absolute font-mono whitespace-pre cursor-default"
                  style={{
                    left: `${field.x * 10}px`,
                    top: `${field.y * 20}px`,
                    width: `${field.width * 10}px`,
                    height: `${field.height * 20}px`,
                    backgroundColor: field.backgroundColor + '20',
                    color: field.textColor,
                    fontSize: '14px',
                    lineHeight: '20px',
                    padding: '1px 3px',
                    border: field.type === 'input' ? '1px solid #0080ff' : 'none'
                  }}
                >
                  {field.value}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ASPMapEditor;