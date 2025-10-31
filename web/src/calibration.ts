/**
 * Client-side calibration utilities for multi-sample enrollment.
 */

/**
 * Calculate L1 (Manhattan) distance between two feature vectors.
 */
export function l1Distance(features1: number[], features2: number[]): number {
  if (features1.length !== features2.length) {
    throw new Error('Feature vectors must have same length');
  }
  return features1.reduce((sum, val, i) => sum + Math.abs(val - features2[i]), 0);
}

/**
 * Average multiple feature vectors to create a more stable template.
 */
export function averageFeatures(featureVectors: number[][]): number[] {
  if (featureVectors.length === 0) {
    throw new Error('At least one feature vector required');
  }
  
  const n = featureVectors.length;
  const length = featureVectors[0].length;
  
  // Ensure all vectors have same length
  for (const vec of featureVectors) {
    if (vec.length !== length) {
      throw new Error('All feature vectors must have same length');
    }
  }
  
  // Average each position
  const averaged: number[] = [];
  for (let i = 0; i < length; i++) {
    const avg = featureVectors.reduce((sum, vec) => sum + vec[i], 0) / n;
    averaged.push(Math.round(avg));
  }
  
  return averaged;
}

/**
 * Calculate adaptive threshold (tau) based on sample variance.
 * Uses mean + multiplier * stddev to set threshold.
 */
export function calculateAdaptiveTau(
  template: number[],
  samples: number[][],
  baseTau: number = 400,
  multiplier: number = 2.0,
): number {
  if (samples.length === 0) {
    return baseTau;
  }
  
  // Calculate distances from template to each sample
  const distances = samples.map(sample => l1Distance(template, sample));
  
  if (distances.length < 2) {
    // Not enough samples for variance, use base + small margin
    const meanDist = distances[0] || 0;
    return Math.max(baseTau, Math.round(meanDist * 1.5));
  }
  
  // Calculate mean and standard deviation
  const meanDist = distances.reduce((a, b) => a + b, 0) / distances.length;
  const variance = distances.reduce((sum, d) => sum + Math.pow(d - meanDist, 2), 0) / distances.length;
  const stddev = Math.sqrt(variance);
  
  // Adaptive threshold: mean + multiplier * stddev
  const adaptiveTau = Math.round(meanDist + multiplier * stddev);
  
  // Ensure it's at least baseTau
  return Math.max(baseTau, adaptiveTau);
}

/**
 * Calculate quality metrics for a template.
 */
export function calculateTemplateQuality(
  template: number[],
  samples: number[][],
): { meanDistance: number; stddevDistance: number; consistencyScore: number } {
  if (samples.length === 0) {
    return { meanDistance: 0, stddevDistance: 0, consistencyScore: 0 };
  }
  
  const distances = samples.map(sample => l1Distance(template, sample));
  const meanDist = distances.reduce((a, b) => a + b, 0) / distances.length;
  const variance = distances.reduce((sum, d) => sum + Math.pow(d - meanDist, 2), 0) / distances.length;
  const stddev = Math.sqrt(variance);
  
  // Consistency score: lower stddev = higher consistency (0-1 scale)
  const consistencyScore = Math.max(0, Math.min(1, 1 - (stddev / 200)));
  
  return {
    meanDistance: Math.round(meanDist * 100) / 100,
    stddevDistance: Math.round(stddev * 100) / 100,
    consistencyScore: Math.round(consistencyScore * 1000) / 1000,
  };
}

