import { useState } from 'react';

export function useTaskState() {
  const [status, setStatus] = useState<'idle' | 'running' | 'success' | 'failed'>('idle');
  return { status, setStatus };
}
