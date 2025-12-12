import { randomUUID } from 'crypto';

import { Request, Response, NextFunction } from 'express';

import config from '../config';
import { AppError, ErrorCode, createError } from '../errors';

const convertToError = (err: unknown): Error => {
  if (err instanceof Error) {
    return err;
  }
  if (err === null || err === undefined) {
    return new Error('Unknown error');
  }
  // Safely convert to string for non-Error types
  let message: string;
  if (typeof err === 'string') {
    message = err;
  } else if (typeof err === 'number' || typeof err === 'boolean') {
    message = String(err);
  } else if (typeof err === 'object') {
    try {
      message = JSON.stringify(err);
    } catch {
      message = 'Unknown error (could not stringify)';
    }
  } else {
    // symbol, bigint, function, etc.
    message = 'Unknown error (unsupported type)';
  }
  return new Error(message);
};

export const errorMiddleware = (
  err: unknown,
  req: Request,
  res: Response,
  _next: NextFunction
): void => {
  const isAppError = err instanceof AppError;
  const safeError = convertToError(err);
  const traceId = req.traceId || (isAppError ? err.traceId : randomUUID());
  let logLevel: 'error' | 'warn' = 'error';

  if (isAppError) {
    const errorResponse = {
      error: {
        code: err.code,
        message: err.message || 'Unknown error',
        status: err.statusCode,
        traceId: err.traceId,
        timestamp: err.timestamp,
        details: (err as AppError & { validationErrors?: unknown }).validationErrors,
      },
    };
    if (err.statusCode < 500) {
      logLevel = 'warn';
    }
    res.status(err.statusCode).json(errorResponse);
  } else {
    const errorResponse = {
      error: {
        code: ErrorCode.INTERNAL_ERROR,
        message:
          config.NODE_ENV === 'production'
            ? 'Internal server error'
            : safeError.message || 'Unknown error',
        status: 500,
        traceId,
        timestamp: new Date().toISOString(),
      },
    };
    res.status(500).json(errorResponse);
  }

  const errorLog = {
    traceId,
    error: {
      name: safeError.name,
      message: safeError.message || 'Unknown error',
      code: isAppError ? err.code : ErrorCode.INTERNAL_ERROR,
      stack: config.NODE_ENV !== 'production' ? safeError.stack : undefined,
    },
    request: {
      method: req.method,
      url: req.url,
      userAgent:
        typeof (req as Request & { get?: Request['get'] }).get === 'function'
          ? req.get('user-agent')
          : req.headers?.['user-agent'],
      ip: req.ip,
    },
    timestamp: new Date().toISOString(),
  };

  if (logLevel === 'error') {
    console.error('Application error:', errorLog);
  } else {
    console.warn('Client error:', errorLog);
  }
};

export const notFoundMiddleware = (req: Request, res: Response, _next: NextFunction): void => {
  const error = createError.notFound(`Route ${req.method} ${req.url} not found`);
  const traceId = req.traceId || randomUUID();

  res.status(404).json({
    error: {
      code: error.code,
      message: error.message,
      traceId,
      timestamp: new Date().toISOString(),
    },
  });
};

export default errorMiddleware;
