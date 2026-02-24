import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: '🎣 Gradient Fisherman — AI Data Assistant',
  description: 'Cast your data into the sea of AI. Chat with your CSV data in plain English — powered by DigitalOcean Gradient™ AI.',
  keywords: ['AI', 'data analysis', 'CSV', 'DigitalOcean', 'Gradient AI', 'SMB', 'business intelligence'],
  openGraph: {
    title: 'Gradient Fisherman — AI Data Assistant for Small Businesses',
    description: 'Upload your CSV data and ask questions in plain English. No SQL required.',
    type: 'website',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="ocean-bg min-h-screen">{children}</body>
    </html>
  )
}
