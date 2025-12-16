import express, { Express } from 'express';
import cors from 'cors';
import helmet from 'helmet';
import compression from 'compression';
import morgan from 'morgan';
import { config } from './config';
import { logger } from './config/logger';
import { errorHandler } from './middleware/error-handler';
import { rateLimiter } from './middleware/rate-limiter';
import { authRouter } from './routes/auth';
import { systemRouter } from './routes/system';
import { resourcesRouter } from './routes/resources';
import { tasksRouter } from './routes/tasks';
import { metricsRouter } from './routes/metrics';

const app: Express = express();

// Middleware
app.use(helmet());
app.use(cors({
  origin: config.corsOrigin,
  credentials: true
}));
app.use(compression());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(morgan('combined', {
  stream: { write: (message) => logger.info(message.trim()) }
}));

// Rate limiting
app.use('/api', rateLimiter);

// Health check (no auth required)
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    version: '1.0.0'
  });
});

// API Routes
app.use('/api/v1/auth', authRouter);
app.use('/api/v1/system', systemRouter);
app.use('/api/v1/resources', resourcesRouter);
app.use('/api/v1/tasks', tasksRouter);
app.use('/api/v1/metrics', metricsRouter);

// API Documentation
app.get('/api/docs', (req, res) => {
  res.json({
    openapi: '3.0.0',
    info: {
      title: 'Unmanned Island System API',
      version: '1.0.0',
      description: 'REST API for external integrations'
    },
    servers: [
      { url: `http://localhost:${config.port}`, description: 'Development' }
    ],
    paths: {
      '/health': {
        get: {
          summary: 'Health check',
          tags: ['System'],
          responses: {
            '200': {
              description: 'System is healthy'
            }
          }
        }
      }
    }
  });
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({
    error: 'Not Found',
    message: `Cannot ${req.method} ${req.path}`
  });
});

// Error handler (must be last)
app.use(errorHandler);

// Start server
const port = config.port;
app.listen(port, () => {
  logger.info(`🚀 API Gateway started on port ${port}`);
  logger.info(`📚 API Documentation: http://localhost:${port}/api/docs`);
  logger.info(`🏥 Health Check: http://localhost:${port}/health`);
});

export default app;
