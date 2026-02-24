/**
 * Copyright 2025 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

'use client'

import { createContext, useContext, useEffect, useState } from 'react'
import { initializeGoogleAuth } from '@/services/api'

interface GoogleAuthContextType {
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
  userProfile: { name: string, picture: string } | null
  setUserProfile: (profile: { name: string, picture: string } | null) => void
}

const GoogleAuthContext = createContext<GoogleAuthContextType>({
  isAuthenticated: false,
  isLoading: true,
  error: null,
  userProfile: null,
  setUserProfile: () => {}
})

export function GoogleAuthProvider({ children }: { children: React.ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [userProfile, setUserProfile] = useState<{ name: string, picture: string } | null>(null)

  useEffect(() => {
    const initAuth = async () => {
      try {
        // Wait for Google Identity Services to load
        let attempts = 0
        while (!window.google && attempts < 20) {
          await new Promise(resolve => setTimeout(resolve, 100))
          attempts++
        }

        if (!window.google) {
          throw new Error('Google Identity Services failed to load')
        }

        const clientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID
        if (!clientId) {
          throw new Error('NEXT_PUBLIC_GOOGLE_CLIENT_ID not set')
        }

        initializeGoogleAuth(clientId)

        // Auto-authenticate in the background
        // The Google Auth will prompt for login when needed
        setIsAuthenticated(true)
      } catch (error) {
        console.error('Failed to initialize Google Auth:', error)
        setError(error instanceof Error ? error.message : 'Failed to initialize')
        setIsAuthenticated(false)
      } finally {
        setIsLoading(false)
      }
    }

    initAuth()
  }, [])

  return (
    <GoogleAuthContext.Provider value={{ isAuthenticated, isLoading, error, userProfile, setUserProfile }}>
      {children}
    </GoogleAuthContext.Provider>
  )
}

export const useGoogleAuth = () => useContext(GoogleAuthContext)
