const express = require('express');
const fs = require('fs').promises;
const path = require('path');
const cors = require('cors');
const pdfParse = require('pdf-parse');
const { spawn } = require('child_process');
const iconv = require('iconv-lite');

// Import centralized catalog configuration - no hardcoding
const { getCatalogPath } = require('../../config/catalog_config');

const app = express();
const PORT = process.env.FILE_API_PORT || 3008;

// Enable CORS for the React development server
app.use(cors({
  origin: ['http://localhost:3007', 'http://localhost:3000'],
  credentials: true
}));

app.use(express.json());

// Base directory for manual files
const MANUALS_BASE_DIR = '/data/asp-manuals';

// Base directory for ASP system commands
const ASP_SYSTEM_CMDS_DIR = '/home/aspuser/app/server/system-cmds';

/**
 * Encoding conversion utilities for SJIS ↔ Unicode
 */
const EncodingConverter = {
  /**
   * Convert SJIS buffer to Unicode string
   * @param {Buffer} sjisBuffer - SJIS encoded buffer
   * @returns {string} Unicode string
   */
  sjisToUnicode: (sjisBuffer) => {
    try {
      return iconv.decode(sjisBuffer, 'sjis');
    } catch (error) {
      console.error('SJIS to Unicode conversion error:', error);
      // Fallback to UTF-8 if SJIS conversion fails
      return sjisBuffer.toString('utf8');
    }
  },

  /**
   * Convert Unicode string to SJIS buffer
   * @param {string} unicodeString - Unicode string
   * @returns {Buffer} SJIS encoded buffer
   */
  unicodeToSjis: (unicodeString) => {
    try {
      return iconv.encode(unicodeString, 'sjis');
    } catch (error) {
      console.error('Unicode to SJIS conversion error:', error);
      // Fallback to UTF-8 if SJIS conversion fails
      return Buffer.from(unicodeString, 'utf8');
    }
  },

  /**
   * Detect and convert file content based on encoding
   * @param {Buffer} buffer - File content buffer
   * @param {string} encoding - Expected encoding ('sjis', 'utf8', 'shift_jis', etc.)
   * @returns {string} Converted Unicode string
   */
  convertFileContent: (buffer, encoding = 'utf8') => {
    const normalizedEncoding = encoding.toLowerCase();
    
    if (normalizedEncoding === 'sjis' || 
        normalizedEncoding === 'shift_jis' || 
        normalizedEncoding === 'shift-jis' ||
        normalizedEncoding === 'cp932') {
      return EncodingConverter.sjisToUnicode(buffer);
    } else {
      return buffer.toString('utf8');
    }
  }
};

/**
 * Recursively read directory structure
 * @param {string} dirPath - Directory path to read
 * @param {string} basePath - Base path for relative paths
 * @returns {Promise<Array>} Array of file/directory objects
 */
async function readDirectoryRecursive(dirPath, basePath = '') {
  const items = [];
  
  try {
    const entries = await fs.readdir(dirPath, { withFileTypes: true });
    
    for (const entry of entries) {
      const fullPath = path.join(dirPath, entry.name);
      const relativePath = path.join(basePath, entry.name);
      
      if (entry.isDirectory()) {
        const children = await readDirectoryRecursive(fullPath, relativePath);
        items.push({
          name: entry.name,
          path: relativePath,
          type: 'directory',
          children: children
        });
      } else if (entry.isFile()) {
        // Include markdown, text, and PDF files
        const ext = path.extname(entry.name).toLowerCase();
        if (['.md', '.txt', '.markdown', '.pdf'].includes(ext)) {
          const stats = await fs.stat(fullPath);
          items.push({
            name: entry.name,
            path: relativePath,
            type: 'file',
            extension: ext,
            size: stats.size
          });
        }
      }
    }
  } catch (error) {
    console.error(`Error reading directory ${dirPath}:`, error);
  }
  
  return items;
}

/**
 * Get directory structure
 */
app.get('/api/files/structure', async (req, res) => {
  try {
    const structure = await readDirectoryRecursive(MANUALS_BASE_DIR);
    res.json({
      success: true,
      basePath: MANUALS_BASE_DIR,
      structure: structure
    });
  } catch (error) {
    console.error('Error reading directory structure:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to read directory structure',
      message: error.message
    });
  }
});

/**
 * Read file content
 */
app.get('/api/files/content', async (req, res) => {
  const { filePath } = req.query;
  
  if (!filePath) {
    return res.status(400).json({
      success: false,
      error: 'File path is required'
    });
  }
  
  try {
    // Ensure the requested file is within the allowed directory
    const fullPath = path.join(MANUALS_BASE_DIR, filePath);
    const normalizedPath = path.normalize(fullPath);
    
    console.log('Requested file path:', filePath);
    console.log('Full path:', fullPath);
    console.log('Normalized path:', normalizedPath);
    
    if (!normalizedPath.startsWith(MANUALS_BASE_DIR)) {
      return res.status(403).json({
        success: false,
        error: 'Access denied: Path traversal attempt detected'
      });
    }
    
    // Check if file exists
    const stats = await fs.stat(normalizedPath);
    if (!stats.isFile()) {
      return res.status(400).json({
        success: false,
        error: 'Path is not a file'
      });
    }
    
    // Read file content based on file type
    const ext = path.extname(normalizedPath).toLowerCase();
    let content;
    
    if (ext === '.pdf') {
      // Parse PDF file
      const buffer = await fs.readFile(normalizedPath);
      const pdfData = await pdfParse(buffer);
      content = pdfData.text;
    } else {
      // Read as text file (markdown, txt)
      content = await fs.readFile(normalizedPath, 'utf-8');
    }
    
    res.json({
      success: true,
      path: filePath,
      content: content,
      size: stats.size,
      modified: stats.mtime,
      type: ext === '.pdf' ? 'pdf' : 'text'
    });
  } catch (error) {
    console.error('Error reading file:', error);
    if (error.code === 'ENOENT') {
      res.status(404).json({
        success: false,
        error: 'File not found'
      });
    } else {
      res.status(500).json({
        success: false,
        error: 'Failed to read file',
        message: error.message
      });
    }
  }
});

/**
 * Search files by content
 */
app.post('/api/files/search', async (req, res) => {
  const { query, caseSensitive = false } = req.body;
  
  if (!query) {
    return res.status(400).json({
      success: false,
      error: 'Search query is required'
    });
  }
  
  try {
    const results = [];
    const searchRegex = new RegExp(query, caseSensitive ? 'g' : 'gi');
    
    async function searchInDirectory(dirPath, basePath = '') {
      const entries = await fs.readdir(dirPath, { withFileTypes: true });
      
      for (const entry of entries) {
        const fullPath = path.join(dirPath, entry.name);
        const relativePath = path.join(basePath, entry.name);
        
        if (entry.isDirectory()) {
          await searchInDirectory(fullPath, relativePath);
        } else if (entry.isFile()) {
          const ext = path.extname(entry.name).toLowerCase();
          if (['.md', '.txt', '.markdown'].includes(ext)) {
            try {
              const content = await fs.readFile(fullPath, 'utf-8');
              const matches = content.match(searchRegex);
              
              if (matches && matches.length > 0) {
                // Extract context around matches
                const contexts = [];
                let match;
                const contextRegex = new RegExp(query, caseSensitive ? 'g' : 'gi');
                
                while ((match = contextRegex.exec(content)) !== null) {
                  const start = Math.max(0, match.index - 50);
                  const end = Math.min(content.length, match.index + query.length + 50);
                  const context = content.substring(start, end);
                  contexts.push({
                    text: context,
                    position: match.index
                  });
                  
                  // Limit to first 3 contexts per file
                  if (contexts.length >= 3) break;
                }
                
                results.push({
                  path: relativePath,
                  name: entry.name,
                  matches: matches.length,
                  contexts: contexts
                });
              }
            } catch (error) {
              console.error(`Error searching file ${fullPath}:`, error);
            }
          }
        }
      }
    }
    
    await searchInDirectory(MANUALS_BASE_DIR);
    
    res.json({
      success: true,
      query: query,
      results: results,
      totalMatches: results.reduce((sum, r) => sum + r.matches, 0)
    });
  } catch (error) {
    console.error('Error searching files:', error);
    res.status(500).json({
      success: false,
      error: 'Search failed',
      message: error.message
    });
  }
});

/**
 * Submit job using SBMJOB
 */
app.post('/api/jobs/submit', async (req, res) => {
  const { job, program, library, volume, parameters = '', priority = 5 } = req.body;
  
  if (!job || !program) {
    return res.status(400).json({
      success: false,
      error: 'Job name and program are required'
    });
  }
  
  try {
    const sbmjobCommand = `SMBJOB JOB=${job},PGM=${program}${
      library ? `,@LIB=${library}` : ''
    }${
      volume ? `,VOL=${volume}` : ''
    }${
      parameters ? `,PARA=${parameters}` : ''
    },JOBPTYY=${priority}`;
    
    const child = spawn('python', ['aspcli.py', ...sbmjobCommand.split(' ')], {
      cwd: ASP_SYSTEM_CMDS_DIR,
      stdio: ['ignore', 'pipe', 'pipe']
    });
    
    let stdout = '';
    let stderr = '';
    
    child.stdout.on('data', (data) => {
      stdout += data.toString();
    });
    
    child.stderr.on('data', (data) => {
      stderr += data.toString();
    });
    
    child.on('close', (code) => {
      if (code === 0) {
        res.json({
          success: true,
          jobId: job,
          message: 'Job submitted successfully',
          output: stdout
        });
      } else {
        res.status(500).json({
          success: false,
          error: 'Failed to submit job',
          output: stderr || stdout
        });
      }
    });
    
  } catch (error) {
    console.error('Error submitting job:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to submit job',
      message: error.message
    });
  }
});

/**
 * Get job list from PostgreSQL JOBINFO table
 */
app.get('/api/jobs', async (req, res) => {
  try {
    // Get jobs from PostgreSQL JOBINFO table
    const fetchProcess = spawn('python3', ['-c', `
import sys
sys.path.append('${ASP_SYSTEM_CMDS_DIR}/functions')
from jobinfo_db import get_all_jobs
import json
jobs = get_all_jobs()
print(json.dumps({"success": True, "jobs": jobs}))
    `], {
      cwd: ASP_SYSTEM_CMDS_DIR,
      stdio: ['pipe', 'pipe', 'pipe']
    });
    
    let output = '';
    let errorOutput = '';
    
    fetchProcess.stdout.on('data', (data) => {
      output += data.toString();
    });
    
    fetchProcess.stderr.on('data', (data) => {
      errorOutput += data.toString();
    });
    
    fetchProcess.on('close', (code) => {
      if (code === 0) {
        try {
          const result = JSON.parse(output.trim());
          if (result.success && result.jobs) {
            // Transform PostgreSQL job data to match UI format
            const transformedJobs = result.jobs.map(job => ({
              id: job.jobid,
              name: job.jobname,
              status: job.status.toLowerCase().trim(),
              user: job.user.trim(),
              start_time: job.sbmdt,
              cpu_time: '00:00:00',
              priority: 5,
              queue: '@SAME',
              program: job.jobname,
              library: 'TESTLIB',
              volume: 'DISK01',
              pid: null,
              log_file: `${job.jobid}.log`
            }));
            
            res.json({
              success: true,
              jobs: transformedJobs
            });
          } else {
            console.error('PostgreSQL jobs fetch failed:', result);
            fallbackToRefjob(res);
          }
        } catch (parseError) {
          console.error('Error parsing PostgreSQL response:', parseError);
          console.error('Raw output:', output);
          console.error('Error output:', errorOutput);
          fallbackToRefjob(res);
        }
      } else {
        console.error('PostgreSQL jobs fetch process failed with code:', code);
        console.error('Error output:', errorOutput);
        fallbackToRefjob(res);
      }
    });
    
  } catch (error) {
    console.error('Error fetching jobs from PostgreSQL:', error);
    fallbackToRefjob(res);
  }
});

function fallbackToRefjob(res) {
  const refjobCommand = 'REFJOB STS=@ALL';
  
  const child = spawn('python', ['aspcli.py', ...refjobCommand.split(' ')], {
    cwd: ASP_SYSTEM_CMDS_DIR,
    stdio: ['ignore', 'pipe', 'pipe']
  });
  
  let stdout = '';
  
  child.stdout.on('data', (data) => {
    stdout += data.toString();
  });
  
  child.on('close', (code) => {
    const jobs = parseRefjobOutput(stdout);
    res.json({
      success: true,
      jobs: jobs
    });
  });
}

/**
 * Get job status from PostgreSQL JOBINFO table
 */
app.get('/api/jobs/:jobId/status', async (req, res) => {
  const { jobId } = req.params;
  
  try {
    // Get job status from PostgreSQL JOBINFO table
    const statusProcess = spawn('python3', ['-c', `
import sys
sys.path.append('${ASP_SYSTEM_CMDS_DIR}/functions')
from jobinfo_db import get_jobinfo
import json
job = get_jobinfo('${jobId}')
print(json.dumps({"success": True, "job": job}))
    `], {
      cwd: ASP_SYSTEM_CMDS_DIR,
      stdio: ['pipe', 'pipe', 'pipe']
    });
    
    let output = '';
    let errorOutput = '';
    
    statusProcess.stdout.on('data', (data) => {
      output += data.toString();
    });
    
    statusProcess.stderr.on('data', (data) => {
      errorOutput += data.toString();
    });
    
    statusProcess.on('close', (code) => {
      if (code === 0) {
        try {
          const result = JSON.parse(output.trim());
          if (result.success && result.job) {
            const job = result.job;
            res.json({
              success: true,
              job: {
                id: job.jobid,
                name: job.jobname,
                status: job.status.toLowerCase().trim(),
                pid: null,
                actuallyRunning: false,
                program: job.jobname,
                library: 'TESTLIB',
                volume: 'DISK01',
                start_time: job.sbmdt,
                end_time: null,
                log_file: `${job.jobid}.log`
              }
            });
          } else {
            res.status(404).json({ success: false, error: 'Job not found' });
          }
        } catch (parseError) {
          console.error('Error parsing PostgreSQL job status response:', parseError);
          console.error('Raw output:', output);
          console.error('Error output:', errorOutput);
          res.status(500).json({ success: false, error: 'Internal error' });
        }
      } else {
        console.error('PostgreSQL job status fetch process failed with code:', code);
        console.error('Error output:', errorOutput);
        res.status(500).json({ success: false, error: 'Database error' });
      }
    });
    
  } catch (error) {
    console.error('Error fetching job status from PostgreSQL:', error);
    res.status(500).json({ success: false, error: 'Internal error' });
  }
});

/**
 * Get job log (JOBID-only log files from PostgreSQL)
 */
app.get('/api/jobs/:jobId/log', async (req, res) => {
  const { jobId } = req.params;
  
  try {
    // Use JOBID-only log file path (new PostgreSQL system uses JOBID.log format)
    const logPath = path.join('/home/aspuser/app/volume/JOBLOG', `${jobId}.log`);
    
    try {
      // Read log file as buffer to handle SJIS encoding
      const logBuffer = await fs.readFile(logPath);
      
      // Try to decode as SJIS first, fallback to UTF-8
      let logContent;
      try {
        // Attempt to decode as SJIS
        logContent = iconv.decode(logBuffer, 'SHIFT_JIS');
      } catch (sjisError) {
        // If SJIS fails, try UTF-8
        logContent = logBuffer.toString('utf-8');
      }
      
      res.set('Content-Type', 'text/plain; charset=utf-8');
      res.send(logContent);
      
    } catch (error) {
      if (error.code === 'ENOENT') {
        res.set('Content-Type', 'text/plain; charset=utf-8');
        res.send(`Job log for ${jobId} not found.\n\nLog file expected at: ${logPath}\n\nThis could mean:\n- Job is still pending or has not started\n- Job completed without generating log output\n- Log file was deleted or moved\n\nCheck job status in ジョブ管理.`);
      } else {
        console.error('Error reading log file:', error);
        res.status(500).set('Content-Type', 'text/plain; charset=utf-8');
        res.send(`Error reading job log: ${error.message}`);
      }
    }
    
  } catch (error) {
    console.error('Error fetching job log:', error);
    res.status(500).set('Content-Type', 'text/plain; charset=utf-8');
    res.send(`Error fetching job log: ${error.message}`);
  }
});

/**
 * Job control actions (hold, resume, cancel)
 */
app.post('/api/jobs/:jobId/:action', async (req, res) => {
  const { jobId, action } = req.params;
  
  const validActions = ['hold', 'resume', 'cancel', 'start'];
  if (!validActions.includes(action)) {
    return res.status(400).json({
      success: false,
      error: 'Invalid action. Valid actions: hold, resume, cancel, start'
    });
  }
  
  try {
    if (action === 'start') {
      // Actually start the job by calling the SBMJOB system
      const sqlite3 = require('sqlite3').verbose();
      const dbPath = '/home/aspuser/app/database/openasp_jobs.db';
      
      if (require('fs').existsSync(dbPath)) {
        const db = new sqlite3.Database(dbPath, sqlite3.OPEN_READONLY);
        
        db.get(`
          SELECT job_name, program, library, volume, parameters 
          FROM jobs 
          WHERE job_id = ?
        `, [jobId], (err, job) => {
          if (err || !job) {
            res.status(404).json({
              success: false,
              error: 'Job not found',
              jobId: jobId
            });
            return;
          }
          
          // Execute SBMJOB command to restart the job with same job name
          const sbmjobCommand = [
            'SBMJOB',
            `JOB=${job.job_name}`,
            `PGM=${job.program}`,
            `@LIB=${job.library}`,
            `VOL=${job.volume}`
          ];
          
          if (job.parameters) {
            sbmjobCommand.push(`PARA=${job.parameters}`);
          }
          
          const process = spawn('python', ['aspcli.py', ...sbmjobCommand], {
            cwd: ASP_SYSTEM_CMDS_DIR,
            stdio: ['pipe', 'pipe', 'pipe']
          });
          
          let output = '';
          let errorOutput = '';
          
          process.stdout.on('data', (data) => {
            output += data.toString();
          });
          
          process.stderr.on('data', (data) => {
            errorOutput += data.toString();
          });
          
          process.on('close', (code) => {
            if (code === 0) {
              // Extract new job ID from output
              const jobIdMatch = output.match(/Job ID: (J[A-F0-9]+)/);
              const newJobId = jobIdMatch ? jobIdMatch[1] : null;
              
              res.json({
                success: true,
                jobId: jobId,
                newJobId: newJobId,
                action: action,
                message: `Job restarted successfully`,
                output: output
              });
            } else {
              res.status(500).json({
                success: false,
                error: 'Failed to start job',
                jobId: jobId,
                exitCode: code,
                output: output,
                error: errorOutput
              });
            }
          });
          
          db.close();
        });
      } else {
        res.status(500).json({
          success: false,
          error: 'Database not found'
        });
      }
    } else {
      // For other actions, just return success for now
      res.json({
        success: true,
        jobId: jobId,
        action: action,
        message: `Job ${action} action will be implemented with job control system`
      });
    }
  } catch (error) {
    console.error(`Error performing ${action} on job ${jobId}:`, error);
    res.status(500).json({
      success: false,
      error: `Failed to ${action} job`,
      message: error.message
    });
  }
});

/**
 * Parse REFJOB output to extract job information
 */
function parseRefjobOutput(output) {
  const jobs = [];
  const lines = output.split('\n');
  
  for (const line of lines) {
    // Look for lines that match the pattern: " number. JOBNAME status @SAME"
    // Be very flexible with the regex to catch job entries
    const match = line.match(/^\s*\d+\.\s+(\S+)\s+(.+)$/);
    if (match) {
      const jobName = match[1];
      const remainder = match[2];
      
      // Skip library entries (they usually end with LIB or have TEST### pattern)
      if (jobName.endsWith('LIB') || /^TEST\d+$/.test(jobName)) {
        continue;
      }
      
      // Extract queue (usually @SAME at the end)
      const queueMatch = remainder.match(/@\S+/);
      const queue = queueMatch ? queueMatch[0] : '@SAME';
      
      // Determine status based on Japanese characters or patterns
      let status = 'pending'; // Default
      if (remainder.includes('実行') || remainder.includes('RUN')) {
        status = 'running';
      } else if (remainder.includes('完了') || remainder.includes('COMP')) {
        status = 'completed';
      } else if (remainder.includes('失敗') || remainder.includes('FAIL')) {
        status = 'failed';
      } else if (remainder.includes('保留') || remainder.includes('HOLD')) {
        status = 'held';
      }
      
      jobs.push({
        id: jobName,
        name: jobName,
        status: status,
        user: 'system',
        start_time: new Date().toISOString(),
        cpu_time: '00:00:00',
        priority: 5,
        queue: queue,
        program: jobName.includes('_') ? jobName.split('_').slice(1).join('_') : jobName,
        library: 'TESTLIB',
        volume: 'DISK01'
      });
    }
  }
  
  return jobs;
}

/**
 * Get dataset data
 */
app.get('/api/datasets/:volume/:library/:dataset/data', async (req, res) => {
  const { volume, library, dataset } = req.params;
  
  try {
    // Look for dataset file in volume directory structure
    const datasetPath = path.join('/home/aspuser/app/volume', volume, library, dataset);
    
    // Get dataset metadata from catalog
    let datasetEncoding = 'utf8';
    let rectype = 'FB';
    let reclen = 80;
    
    try {
      const catalogPath = getCatalogPath();
      const catalogData = JSON.parse(await fs.readFile(catalogPath, 'utf-8'));
      
      if (catalogData[volume] && 
          catalogData[volume][library] && 
          catalogData[volume][library][dataset]) {
        const datasetInfo = catalogData[volume][library][dataset];
        if (datasetInfo.ENCODING) datasetEncoding = datasetInfo.ENCODING;
        if (datasetInfo.RECTYPE) rectype = datasetInfo.RECTYPE;
        if (datasetInfo.RECLEN) reclen = datasetInfo.RECLEN;
      }
    } catch (catalogError) {
      console.warn('Could not read catalog for dataset info:', catalogError.message);
    }
    
    try {
      // Read file as buffer to handle binary data properly
      const buffer = await fs.readFile(datasetPath);
      let convertedData;
      
      if (rectype === 'FB') {
        // Fixed Block: Process records at byte level before conversion
        const records = [];
        let offset = 0;
        
        while (offset < buffer.length) {
          // Extract one record of reclen bytes
          const recordBuffer = buffer.slice(offset, offset + reclen);
          
          if (recordBuffer.length === 0) break;
          
          // Convert each record individually
          let recordText;
          if (datasetEncoding === 'shift_jis' || datasetEncoding === 'sjis') {
            recordText = EncodingConverter.sjisToUnicode(recordBuffer);
          } else {
            recordText = EncodingConverter.convertFileContent(recordBuffer, datasetEncoding);
          }
          
          // Pad with spaces if record is shorter than reclen
          if (recordBuffer.length < reclen) {
            const paddingLength = reclen - recordBuffer.length;
            recordText += ' '.repeat(paddingLength);
          }
          
          records.push(recordText);
          offset += reclen;
        }
        
        // Join records with newlines for display
        convertedData = records.join('\n');
        
      } else if (rectype === 'VB') {
        // Variable Block: Handle variable-length records with length prefixes
        if (datasetEncoding === 'shift_jis' || datasetEncoding === 'sjis') {
          convertedData = EncodingConverter.sjisToUnicode(buffer);
        } else {
          convertedData = EncodingConverter.convertFileContent(buffer, datasetEncoding);
        }
      } else {
        // Other record types: fallback to standard conversion
        convertedData = EncodingConverter.convertFileContent(buffer, datasetEncoding);
      }
      
      res.set('Content-Type', 'text/plain; charset=utf-8');
      res.send(convertedData);
    } catch (error) {
      if (error.code === 'ENOENT') {
        // Generate sample mixed English/Japanese data for demonstration  
        const sampleData = generateSampleDatasetData(dataset);
        res.set('Content-Type', 'text/plain; charset=utf-8');
        res.send(sampleData);
      } else {
        throw error;
      }
    }
  } catch (error) {
    console.error('Error fetching dataset data:', error);
    res.status(500).set('Content-Type', 'text/plain');
    res.send(`Error fetching dataset data: ${error.message}`);
  }
});

/**
 * Delete dataset
 */
app.delete('/api/datasets/:volume/:library/:dataset', async (req, res) => {
  const { volume, library, dataset } = req.params;
  
  try {
    const datasetPath = path.join('/home/aspuser/app/volume', volume, library, dataset);
    
    try {
      await fs.unlink(datasetPath);
      res.json({
        success: true,
        message: `Dataset ${dataset} deleted successfully`
      });
    } catch (error) {
      if (error.code === 'ENOENT') {
        res.json({
          success: true,
          message: `Dataset ${dataset} was already deleted or does not exist`
        });
      } else {
        throw error;
      }
    }
  } catch (error) {
    console.error('Error deleting dataset:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to delete dataset',
      message: error.message
    });
  }
});

/**
 * Update dataset data (with encoding conversion)
 */
app.put('/api/datasets/:volume/:library/:dataset', async (req, res) => {
  const { volume, library, dataset } = req.params;
  const { data: newData } = req.body;
  
  if (!newData) {
    return res.status(400).json({
      success: false,
      error: 'No data provided'
    });
  }
  
  try {
    const datasetPath = path.join('/home/aspuser/app/volume', volume, library, dataset);
    
    // Get encoding information from catalog
    let datasetEncoding = 'utf8';
    try {
      const catalogPath = getCatalogPath();
      const catalogData = JSON.parse(await fs.readFile(catalogPath, 'utf-8'));
      
      if (catalogData[volume] && 
          catalogData[volume][library] && 
          catalogData[volume][library][dataset] &&
          catalogData[volume][library][dataset].ENCODING) {
        datasetEncoding = catalogData[volume][library][dataset].ENCODING;
      }
    } catch (catalogError) {
      console.warn('Could not read catalog for encoding info:', catalogError.message);
    }
    
    // Convert Unicode data to appropriate encoding for server storage
    let bufferToWrite;
    const normalizedEncoding = datasetEncoding.toLowerCase();
    
    if (normalizedEncoding === 'sjis' || 
        normalizedEncoding === 'shift_jis' || 
        normalizedEncoding === 'shift-jis' ||
        normalizedEncoding === 'cp932') {
      // Convert Unicode to SJIS for server storage
      bufferToWrite = EncodingConverter.unicodeToSjis(newData);
    } else {
      // Store as UTF-8
      bufferToWrite = Buffer.from(newData, 'utf8');
    }
    
    // Create directory if it doesn't exist
    const datasetDir = path.dirname(datasetPath);
    await fs.mkdir(datasetDir, { recursive: true });
    
    // Write the converted data to file
    await fs.writeFile(datasetPath, bufferToWrite);
    
    res.json({
      success: true,
      message: `Dataset ${dataset} updated successfully`,
      encoding: datasetEncoding
    });
    
  } catch (error) {
    console.error('Error updating dataset:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to update dataset',
      message: error.message
    });
  }
});

/**
 * Generate sample dataset data with mixed English/Japanese content
 */
function generateSampleDatasetData(datasetName) {
  const sampleRecords = [
    'EMP001    John Smith        営業部     Tokyo     ¥350000   2020-04-01',
    'EMP002    田中太郎          開発部     Osaka     ¥420000   2019-03-15',
    'EMP003    Mary Johnson      人事部     Tokyo     ¥380000   2021-01-10',
    'EMP004    佐藤花子          経理部     Nagoya    ¥365000   2018-07-22',
    'EMP005    David Wilson      IT部       Tokyo     ¥450000   2022-02-28',
    'EMP006    山田一郎          営業部     Fukuoka   ¥340000   2020-09-14',
    'EMP007    Sarah Davis       マーケティング部 Tokyo ¥390000   2021-06-03',
    'EMP008    鈴木美咲          開発部     Osaka     ¥410000   2019-11-20',
    'EMP009    Michael Brown     品質管理部 Tokyo     ¥360000   2020-12-05',
    'EMP010    高橋健太          総務部     Kyoto     ¥355000   2021-08-17'
  ];
  
  if (datasetName.includes('CUSTOMER')) {
    return [
      'CUST001   ABC Corporation   アメリカ   New York      Active    2023-01-15',
      'CUST002   トヨタ自動車      日本       Toyota City   Active    2022-03-20',
      'CUST003   Samsung Electronics 韓国    Seoul         Active    2023-05-10',
      'CUST004   ソニー株式会社    日本       Tokyo         Active    2022-12-01',
      'CUST005   Microsoft Corp    アメリカ   Redmond       Active    2023-02-28'
    ].join('');
  }
  
  if (datasetName.includes('PAYROLL')) {
    return [
      'PAY202301田中太郎    420000  42000   378000  所得税    住民税    健康保険',
      'PAY202301John Smith  350000  35000   315000  Income Tax Municipal Health',
      'PAY202301佐藤花子    365000  36500   328500  所得税    住民税    健康保険',
      'PAY202301Mary Johnson380000  38000   342000  Income Tax Municipal Health',
      'PAY202301山田一郎    340000  34000   306000  所得税    住民税    健康保険'
    ].join('');
  }
  
  // Default sample data
  return sampleRecords.join('');
}

/**
 * Read CL file content with SJIS to Unicode conversion
 */
app.get('/api/cl/:volume/:library/:filename', async (req, res) => {
  try {
    const { volume, library, filename } = req.params;
    
    // Construct file path
    const volumePath = `/home/aspuser/app/volume/${volume}/${library}`;
    
    // First try without extension (except for Java)
    let filePath = path.join(volumePath, filename);
    let actualFilename = filename;
    
    // Check file existence - try without extension first
    let fileExists = await fs.access(filePath).then(() => true).catch(() => false);
    
    // If not found and filename has extension, try with extension
    if (!fileExists && filename.includes('.')) {
      const filenameWithExt = filename;
      filePath = path.join(volumePath, filenameWithExt);
      fileExists = await fs.access(filePath).then(() => true).catch(() => false);
      if (fileExists) {
        actualFilename = filenameWithExt;
      }
    }
    
    // If still not found, try common extensions
    if (!fileExists) {
      const baseFilename = filename.replace(/\.[^/.]+$/, ''); // Remove extension if exists
      const extensions = ['.cl', '.CL'];
      
      for (const ext of extensions) {
        filePath = path.join(volumePath, baseFilename + ext);
        fileExists = await fs.access(filePath).then(() => true).catch(() => false);
        if (fileExists) {
          actualFilename = baseFilename + ext;
          break;
        }
      }
    }
    
    if (!fileExists) {
      return res.status(404).json({
        success: false,
        error: 'CL file not found',
        path: filePath,
        tried: [filename, filename + '.cl', filename + '.CL']
      });
    }
    
    // Read file as buffer to handle SJIS encoding
    const fileBuffer = await fs.readFile(filePath);
    
    // Convert SJIS to Unicode for display
    const content = EncodingConverter.sjisToUnicode(fileBuffer);
    
    res.json({
      success: true,
      filename: actualFilename,
      volume: volume,
      library: library,
      content: content,
      size: fileBuffer.length,
      encoding: 'sjis'
    });
    
  } catch (error) {
    console.error('Error reading CL file:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to read CL file',
      message: error.message
    });
  }
});

/**
 * Execute CL program via SBMJOB
 */
app.post('/api/cl/execute', async (req, res) => {
  try {
    const { program, library, volume, jobname, parameters } = req.body;
    
    // Validate required fields
    if (!program || !library || !volume || !jobname) {
      return res.status(400).json({
        success: false,
        error: 'Missing required fields: program, library, volume, jobname'
      });
    }
    
    // Execute SBMJOB command
    const sbmjobCommand = `SBMJOB JOB=${jobname},PGM=${program},@LIB=${library},VOL=${volume}${parameters ? `,PARA=${parameters}` : ''}`;
    
    const process = spawn('python', ['aspcli.py', 'SBMJOB', `JOB=${jobname},PGM=${program},@LIB=${library},VOL=${volume}${parameters ? `,PARA=${parameters}` : ''}`], {
      cwd: ASP_SYSTEM_CMDS_DIR,
      stdio: ['pipe', 'pipe', 'pipe']
    });
    
    let output = '';
    let errorOutput = '';
    
    process.stdout.on('data', (data) => {
      output += data.toString();
    });
    
    process.stderr.on('data', (data) => {
      errorOutput += data.toString();
    });
    
    process.on('close', (code) => {
      if (code === 0) {
        // Extract job ID from output
        const jobIdMatch = output.match(/Job ID: (J[A-F0-9]+)/);
        const jobId = jobIdMatch ? jobIdMatch[1] : null;
        
        res.json({
          success: true,
          message: 'CL program execution submitted',
          command: sbmjobCommand,
          jobId: jobId,
          output: output
        });
      } else {
        res.status(500).json({
          success: false,
          error: 'Failed to execute CL program',
          command: sbmjobCommand,
          exitCode: code,
          output: output,
          error: errorOutput
        });
      }
    });
    
  } catch (error) {
    console.error('Error executing CL program:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to execute CL program',
      message: error.message
    });
  }
});

/**
 * Get JOBINFO from PostgreSQL database
 */
app.get('/api/jobinfo/:jobId', async (req, res) => {
  const { jobId } = req.params;
  
  try {
    const { spawn } = require('child_process');
    const process = spawn('python3', ['-c', `
import sys
sys.path.append('${ASP_SYSTEM_CMDS_DIR}/functions')
from jobinfo_db import get_jobinfo
import json
result = get_jobinfo('${jobId}')
print(json.dumps(result) if result else 'null')
    `], {
      cwd: ASP_SYSTEM_CMDS_DIR,
      stdio: ['pipe', 'pipe', 'pipe']
    });
    
    let output = '';
    let errorOutput = '';
    
    process.stdout.on('data', (data) => {
      output += data.toString();
    });
    
    process.stderr.on('data', (data) => {
      errorOutput += data.toString();
    });
    
    process.on('close', (code) => {
      if (code === 0) {
        try {
          const jobInfo = JSON.parse(output.trim());
          if (jobInfo) {
            res.json({
              success: true,
              jobInfo: jobInfo
            });
          } else {
            res.status(404).json({
              success: false,
              error: 'Job not found'
            });
          }
        } catch (parseError) {
          res.status(500).json({
            success: false,
            error: 'Failed to parse job info',
            details: parseError.message
          });
        }
      } else {
        res.status(500).json({
          success: false,
          error: 'Failed to get job info',
          details: errorOutput
        });
      }
    });
    
  } catch (error) {
    console.error('Error getting job info:', error);
    res.status(500).json({
      success: false,
      error: 'Server error',
      message: error.message
    });
  }
});

/**
 * Get job log file content
 */
app.get('/api/joblog/:jobId', async (req, res) => {
  const { jobId } = req.params;
  
  try {
    const fs = require('fs');
    const path = require('path');
    const logPath = path.join('/home/aspuser/app/volume/JOBLOG', `${jobId}.log`);
    
    if (!fs.existsSync(logPath)) {
      return res.status(404).json({
        success: false,
        error: 'Job log file not found',
        logPath: logPath
      });
    }
    
    const logContent = fs.readFileSync(logPath, 'utf8');
    
    res.json({
      success: true,
      jobId: jobId,
      logContent: logContent,
      logPath: logPath
    });
    
  } catch (error) {
    console.error('Error reading job log:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to read job log',
      message: error.message
    });
  }
});

/**
 * Delete JOBINFO and job log file
 */
app.delete('/api/jobinfo/:jobId', async (req, res) => {
  const { jobId } = req.params;
  
  try {
    const { spawn } = require('child_process');
    const fs = require('fs');
    const path = require('path');
    
    // Delete from PostgreSQL JOBINFO table
    const deleteProcess = spawn('python3', ['-c', `
import sys
sys.path.append('${ASP_SYSTEM_CMDS_DIR}/functions')
from jobinfo_db import delete_jobinfo
import json
result = delete_jobinfo('${jobId}')
print(json.dumps({"success": result}))
    `], {
      cwd: ASP_SYSTEM_CMDS_DIR,
      stdio: ['pipe', 'pipe', 'pipe']
    });
    
    let output = '';
    let errorOutput = '';
    
    deleteProcess.stdout.on('data', (data) => {
      output += data.toString();
    });
    
    deleteProcess.stderr.on('data', (data) => {
      errorOutput += data.toString();
    });
    
    deleteProcess.on('close', (code) => {
      if (code === 0) {
        try {
          const deleteResult = JSON.parse(output.trim());
          
          // Delete log file
          const logPath = path.join('/home/aspuser/app/volume/JOBLOG', `${jobId}.log`);
          let logDeleted = false;
          
          try {
            if (fs.existsSync(logPath)) {
              fs.unlinkSync(logPath);
              logDeleted = true;
              console.log(`Log file deleted: ${logPath}`);
            } else {
              console.log(`Log file not found: ${logPath}`);
            }
          } catch (logError) {
            console.error(`Error deleting log file: ${logError}`);
          }
          
          if (deleteResult.success || logDeleted) {
            res.json({
              success: true,
              message: `Job ${jobId} deleted successfully`,
              details: {
                jobinfo_deleted: deleteResult.success,
                log_file_deleted: logDeleted,
                log_path: logPath
              }
            });
          } else {
            res.status(404).json({
              success: false,
              error: 'Job not found in database and no log file',
              jobId: jobId
            });
          }
        } catch (parseError) {
          res.status(500).json({
            success: false,
            error: 'Failed to parse deletion result',
            details: parseError.message
          });
        }
      } else {
        res.status(500).json({
          success: false,
          error: 'Failed to delete job from database',
          details: errorOutput
        });
      }
    });
    
  } catch (error) {
    console.error('Error deleting job:', error);
    res.status(500).json({
      success: false,
      error: 'Server error',
      message: error.message
    });
  }
});

/**
 * Delete job from PostgreSQL JOBINFO table and log file
 */
app.delete('/api/jobs/:jobId', async (req, res) => {
  const { jobId } = req.params;
  
  try {
    // Delete from PostgreSQL JOBINFO table
    const deleteProcess = spawn('python3', ['-c', `
import sys
sys.path.append('${ASP_SYSTEM_CMDS_DIR}/functions')
from jobinfo_db import delete_jobinfo
import json
result = delete_jobinfo('${jobId}')
print(json.dumps({"success": result}))
    `], {
      cwd: ASP_SYSTEM_CMDS_DIR,
      stdio: ['pipe', 'pipe', 'pipe']
    });
    
    let output = '';
    let errorOutput = '';
    
    deleteProcess.stdout.on('data', (data) => {
      output += data.toString();
    });
    
    deleteProcess.stderr.on('data', (data) => {
      errorOutput += data.toString();
    });
    
    deleteProcess.on('close', async (code) => {
      let deleteResult = { success: false };
      
      if (code === 0) {
        try {
          deleteResult = JSON.parse(output.trim());
        } catch (parseError) {
          console.error('Error parsing PostgreSQL delete response:', parseError);
          console.error('Raw output:', output);
        }
      } else {
        console.error('PostgreSQL delete process failed with code:', code);
        console.error('Error output:', errorOutput);
      }
      
      // Also try to delete log file
      const logPath = path.join('/home/aspuser/app/volume/JOBLOG', `${jobId}.log`);
      let logDeleted = false;
      try {
        await fs.unlink(logPath);
        logDeleted = true;
        console.log(`Log file deleted: ${logPath}`);
      } catch (logError) {
        if (logError.code !== 'ENOENT') {
          console.error('Error deleting log file:', logError);
        }
      }
      
      if (deleteResult.success || logDeleted) {
        res.json({
          success: true,
          message: `Job ${jobId} deleted successfully`,
          details: {
            jobinfo_deleted: deleteResult.success,
            log_file_deleted: logDeleted,
            log_path: logPath
          }
        });
      } else {
        res.status(404).json({
          success: false,
          error: 'Job not found in database and no log file',
          jobId: jobId
        });
      }
    });
    
  } catch (error) {
    console.error('Error deleting job from PostgreSQL:', error);
    res.status(500).json({ 
      success: false, 
      error: 'Internal error',
      message: error.message 
    });
  }
});

/**
 * System status endpoint
 */
app.get('/api/system', async (req, res) => {
  try {
    const os = require('os');
    const fs = require('fs');
    
    // Get system information
    const cpuCount = os.cpus().length;
    const totalMem = os.totalmem();
    const freeMem = os.freemem();
    const usedMem = totalMem - freeMem;
    const memPercent = (usedMem / totalMem) * 100;
    
    // Get uptime
    const uptime = os.uptime();
    const days = Math.floor(uptime / 86400);
    const hours = Math.floor((uptime % 86400) / 3600);
    const minutes = Math.floor((uptime % 3600) / 60);
    const uptimeString = `${days}d ${hours}h ${minutes}m`;
    
    // Get load average (Unix/Linux only)
    const loadAvg = os.loadavg();
    
    // Mock CPU percentage (could be enhanced with actual CPU monitoring)
    const cpuPercent = loadAvg[0] * 10; // Rough estimation
    
    // Get disk usage for root filesystem
    let diskTotal = 0;
    let diskUsed = 0;
    let diskPercent = 0;
    try {
      const stats = await fs.promises.statfs('/');
      diskTotal = stats.blocks * stats.bsize;
      const diskFree = stats.bavail * stats.bsize;
      diskUsed = diskTotal - diskFree;
      diskPercent = (diskUsed / diskTotal) * 100;
    } catch (err) {
      // Fallback values if statfs is not available
      diskTotal = 1000000000000; // 1TB
      diskUsed = 156700000000;   // 156.7GB
      diskPercent = 15.3;
    }
    
    // Format bytes
    const formatBytes = (bytes) => {
      const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
      if (bytes === 0) return '0 B';
      const i = Math.floor(Math.log(bytes) / Math.log(1024));
      return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
    };
    
    // Mock process data
    const processes = [
      { pid: process.pid, name: 'asp-manager', user: 'aspuser', cpu_percent: 5.2, memory_percent: 3.1, status: 'running' },
      { pid: process.pid + 1, name: 'node', user: 'aspuser', cpu_percent: 2.1, memory_percent: 1.8, status: 'running' },
      { pid: process.pid + 2, name: 'python', user: 'aspuser', cpu_percent: 1.5, memory_percent: 2.3, status: 'sleeping' }
    ];
    
    // System alerts
    const alerts = [];
    if (cpuPercent > 80) {
      alerts.push({
        type: 'warning',
        message: `High CPU usage: ${cpuPercent.toFixed(1)}%`,
        timestamp: new Date().toISOString()
      });
    }
    if (memPercent > 80) {
      alerts.push({
        type: 'warning',
        message: `High memory usage: ${memPercent.toFixed(1)}%`,
        timestamp: new Date().toISOString()
      });
    }
    if (diskPercent > 90) {
      alerts.push({
        type: 'warning',
        message: `High disk usage: ${diskPercent.toFixed(1)}%`,
        timestamp: new Date().toISOString()
      });
    }
    
    // System logs
    const logs = [
      `[${new Date().toISOString()}] INFO: ASP Manager system monitoring active`,
      `[${new Date().toISOString()}] INFO: CPU usage: ${cpuPercent.toFixed(1)}%`,
      `[${new Date().toISOString()}] INFO: Memory usage: ${memPercent.toFixed(1)}%`,
      `[${new Date().toISOString()}] INFO: Disk usage: ${diskPercent.toFixed(1)}%`,
      `[${new Date().toISOString()}] INFO: Active processes: ${processes.length}`
    ];
    
    res.json({
      success: true,
      system_info: {
        hostname: os.hostname(),
        uptime: uptimeString,
        cpu_percent: Math.min(cpuPercent, 100),
        cpu_count: cpuCount,
        memory_total: formatBytes(totalMem),
        memory_used: formatBytes(usedMem),
        memory_percent: memPercent,
        disk_total: formatBytes(diskTotal),
        disk_used: formatBytes(diskUsed),
        disk_percent: diskPercent,
        process_count: processes.length,
        load_avg: loadAvg
      },
      processes: processes,
      alerts: alerts,
      logs: logs,
      last_update: new Date().toISOString()
    });
  } catch (error) {
    console.error('Error getting system status:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to get system status',
      message: error.message
    });
  }
});

/**
 * Health check endpoint
 */
app.get('/api/health', (req, res) => {
  res.json({
    success: true,
    status: 'healthy',
    basePath: MANUALS_BASE_DIR,
    aspSystemCmds: ASP_SYSTEM_CMDS_DIR,
    timestamp: new Date().toISOString()
  });
});

// Start job processor when server starts
function startJobProcessor() {
  console.log('Starting job processor...');
  
  try {
    // Use spawn with detached process for better control
    const jobProcessor = spawn('python', ['-c', `
import sys
import os
sys.path.append('/home/aspuser/app/server/system-cmds')
from functions.sbmjob import _job_processor_worker
import threading
import time

print('[JOB_PROCESSOR] Starting background job processor')

def run_processor():
    while True:
        try:
            _job_processor_worker()
            time.sleep(1)  # Small delay to prevent CPU overload
        except Exception as e:
            print(f'[JOB_PROCESSOR_ERROR] Error: {e}')
            time.sleep(5)

thread = threading.Thread(target=run_processor)
thread.daemon = True
thread.start()

# Keep the process alive
try:
    thread.join()
except KeyboardInterrupt:
    print('[JOB_PROCESSOR] Shutting down...')
    sys.exit(0)
`], {
      cwd: '/home/aspuser/app/server/system-cmds',
      detached: true,
      stdio: ['ignore', 'pipe', 'pipe']
    });

    jobProcessor.stdout.on('data', (data) => {
      console.log(`[JOB_PROCESSOR] ${data.toString().trim()}`);
    });

    jobProcessor.stderr.on('data', (data) => {
      console.error(`[JOB_PROCESSOR_ERROR] ${data.toString().trim()}`);
    });

    jobProcessor.on('exit', (code) => {
      console.log(`[JOB_PROCESSOR] Process exited with code ${code}`);
      if (code !== 0) {
        // Restart after 10 seconds on error
        setTimeout(startJobProcessor, 10000);
      }
    });

    // Don't wait for the job processor to finish
    jobProcessor.unref();
    
    console.log('[JOB_PROCESSOR] Started successfully');
  } catch (error) {
    console.error(`[JOB_PROCESSOR_ERROR] Failed to start: ${error}`);
    // Retry after 10 seconds
    setTimeout(startJobProcessor, 10000);
  }
}

// Start server
app.listen(PORT, '0.0.0.0', () => {
  console.log(`File API server running on port ${PORT}`);
  console.log(`Serving files from: ${MANUALS_BASE_DIR}`);
  
  // Start job processor after server is ready
  setTimeout(startJobProcessor, 2000);
});

module.exports = app;