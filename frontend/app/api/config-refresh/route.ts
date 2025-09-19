import { NextResponse } from 'next/server'

export async function POST() {
  try {
    // Call the backend to refresh its configuration cache
    const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/config/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    })
    
    if (response.ok) {
      return NextResponse.json({ 
        success: true, 
        message: 'Backend configuration cache refreshed successfully' 
      })
    } else {
      const errorData = await response.json()
      return NextResponse.json(
        { success: false, error: errorData.detail || 'Failed to refresh backend configuration' },
        { status: response.status }
      )
    }
  } catch (error) {
    console.error('Error refreshing backend configuration:', error)
    return NextResponse.json(
      { success: false, error: 'Failed to connect to backend for configuration refresh' },
      { status: 500 }
    )
  }
}