import { NextRequest, NextResponse } from 'next/server'

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ params: string[] }> }
) {
  // Await params as required by Next.js 15
  const resolvedParams = await params
  const [width, height] = resolvedParams.params
  const searchParams = request.nextUrl.searchParams
  const text = searchParams.get('text') || '?'
  const bg = searchParams.get('bg') || '0891b2'
  const color = searchParams.get('color') || 'ffffff'

  // Validate dimensions
  const w = Math.min(Math.max(parseInt(width) || 32, 16), 512)
  const h = Math.min(Math.max(parseInt(height) || 32, 16), 512)

  // Create a simple SVG placeholder
  const svg = `
    <svg width="${w}" height="${h}" xmlns="http://www.w3.org/2000/svg">
      <rect width="100%" height="100%" fill="#${bg}"/>
      <text x="50%" y="50%" font-family="Arial, sans-serif" font-size="${Math.min(w, h) / 3}" font-weight="bold" 
            fill="#${color}" text-anchor="middle" dominant-baseline="central">${text}</text>
    </svg>
  `

  return new NextResponse(svg, {
    headers: {
      'Content-Type': 'image/svg+xml',
      'Cache-Control': 'public, max-age=3600'
    }
  })
}
