import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { AuthProvider } from '@/lib/auth-context';
import { Toaster } from 'sonner';
import { FlowgladProvider } from '@flowglad/nextjs';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Personal AI Assistant',
  description: 'Your intelligent life companion',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  // For the hackathon demo, we'll assume a user is always logged in
  // In a real implementation, you'd check the JWT token server-side
  const user = { id: 'demo-user', email: 'demo@example.com' };

  return (
    <html lang="en">
      <body className={inter.className}>
        <FlowgladProvider 
          serverRoute="/api/flowglad"
          loadBilling={!!user}
        >
          <AuthProvider>
            {children}
            <Toaster position="top-right" />
          </AuthProvider>
        </FlowgladProvider>
      </body>
    </html>
  );
}