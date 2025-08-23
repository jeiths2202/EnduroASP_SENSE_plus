// API endpoint for real-time pipeline flow visualization
export default function handler(req: any, res: any) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  // Simulate real-time pipeline status for flow visualization
  const currentTime = new Date().getTime();
  const simulatedProgress = (currentTime % 60000) / 600; // 0-100 over 60 seconds

  const pipelineStatus: any = {
    commit: {
      status: simulatedProgress > 10 ? 'success' : 'running',
      progress: Math.min(100, simulatedProgress * 10),
      duration: simulatedProgress > 10 ? '2s' : undefined,
      details: 'Latest commit: feat: Add user authentication'
    },
    'build-artifact': {
      status: simulatedProgress > 20 ? 'success' : simulatedProgress > 10 ? 'running' : 'idle',
      progress: simulatedProgress > 10 ? Math.min(100, (simulatedProgress - 10) * 10) : 0,
      duration: simulatedProgress > 20 ? '15s' : undefined,
      details: 'Dependencies installed, code compiled'
    },
    build: {
      status: simulatedProgress > 30 ? 'success' : simulatedProgress > 20 ? 'running' : 'idle',
      progress: simulatedProgress > 20 ? Math.min(100, (simulatedProgress - 20) * 10) : 0,
      duration: simulatedProgress > 30 ? '45s' : undefined,
      details: 'Build completed successfully'
    },
    'build-decision': {
      status: simulatedProgress > 35 ? 'success' : simulatedProgress > 30 ? 'running' : 'idle',
      progress: simulatedProgress > 30 ? 100 : 0,
      details: 'Build validation passed'
    },
    test: {
      status: simulatedProgress > 50 ? 'success' : simulatedProgress > 35 ? 'running' : 'idle',
      progress: simulatedProgress > 35 ? Math.min(100, (simulatedProgress - 35) * 6.67) : 0,
      duration: simulatedProgress > 50 ? '1m 20s' : undefined,
      details: 'Unit tests: 156 passed, Integration tests: 42 passed'
    },
    'test-decision': {
      status: simulatedProgress > 55 ? 'success' : simulatedProgress > 50 ? 'running' : 'idle',
      progress: simulatedProgress > 50 ? 100 : 0,
      details: 'All tests passed'
    },
    security: {
      status: simulatedProgress > 70 ? 'success' : simulatedProgress > 55 ? 'running' : 'idle',
      progress: simulatedProgress > 55 ? Math.min(100, (simulatedProgress - 55) * 6.67) : 0,
      duration: simulatedProgress > 70 ? '30s' : undefined,
      details: 'No vulnerabilities found, Code quality: A'
    },
    'security-decision': {
      status: simulatedProgress > 75 ? 'success' : simulatedProgress > 70 ? 'running' : 'idle',
      progress: simulatedProgress > 70 ? 100 : 0,
      details: 'Security checks passed'
    },
    deploy: {
      status: simulatedProgress > 85 ? 'success' : simulatedProgress > 75 ? 'running' : 'idle',
      progress: simulatedProgress > 75 ? Math.min(100, (simulatedProgress - 75) * 10) : 0,
      duration: simulatedProgress > 85 ? '2m 15s' : undefined,
      details: 'Deployed to production environment'
    },
    'deploy-decision': {
      status: simulatedProgress > 90 ? 'success' : simulatedProgress > 85 ? 'running' : 'idle',
      progress: simulatedProgress > 85 ? 100 : 0,
      details: 'Deployment verified'
    },
    production: {
      status: simulatedProgress > 95 ? 'success' : simulatedProgress > 90 ? 'running' : 'idle',
      progress: simulatedProgress > 90 ? Math.min(100, (simulatedProgress - 90) * 20) : 0,
      details: 'Application is live and healthy'
    },
    // External systems (always idle)
    'devops-docs': {
      status: 'idle',
      details: 'DevOps documentation and policies'
    },
    'ci-cd-tools': {
      status: 'idle',
      details: 'Jenkins, GitHub Actions, GitLab CI'
    },
    infrastructure: {
      status: 'idle',
      details: 'AWS, Kubernetes, Docker'
    },
    monitoring: {
      status: 'idle',
      details: 'Prometheus, Grafana, ELK Stack'
    }
  };

  // Add some randomness for failed scenarios (5% chance)
  if (Math.random() < 0.05) {
    const failPoints = ['build', 'test', 'security', 'deploy'];
    const failAt = failPoints[Math.floor(Math.random() * failPoints.length)];
    
    if (pipelineStatus[failAt].status === 'running' || pipelineStatus[failAt].status === 'success') {
      pipelineStatus[failAt].status = 'failed';
      pipelineStatus[failAt].details = `Error: ${failAt} failed - ${
        failAt === 'build' ? 'Compilation error in module X' :
        failAt === 'test' ? '3 unit tests failed' :
        failAt === 'security' ? 'Critical vulnerability detected' :
        'Deployment timeout'
      }`;
    }
  }

  res.status(200).json(pipelineStatus);
}