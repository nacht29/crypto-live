import type { Metadata } from 'next';
import './fonts.css';
import './globals.css';

export const metadata: Metadata = {
  title: 'Crypto Live Dashboard',
  description: 'Realtime crypto prices powered by DynamoDB + S3.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>{children}</body>
    </html>
  );
}
