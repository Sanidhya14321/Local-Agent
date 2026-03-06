import { PropsWithChildren } from 'react';

export function AppShell({ children }: PropsWithChildren) {
  return <div style={{ maxWidth: 1100, margin: '0 auto' }}>{children}</div>;
}
