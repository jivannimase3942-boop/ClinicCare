import React, { useEffect, useRef, useState } from 'react'
import { useAuth } from '@/context/AuthContext'
import { useToast } from '@/context/ToastContext'

declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize: (config: {
            client_id: string
            callback: (response: { credential: string }) => void
            auto_select?: boolean
            cancel_on_tap_outside?: boolean
          }) => void
          renderButton: (
            parent: HTMLElement,
            options: {
              theme?: 'outline' | 'filled_blue' | 'filled_black'
              size?: 'large' | 'medium' | 'small'
              text?: 'signin_with' | 'signup_with' | 'continue_with' | 'signin'
              shape?: 'rectangular' | 'pill' | 'circle' | 'square'
              logo_alignment?: 'left' | 'center'
              width?: string | number
              locale?: string
            }
          ) => void
          prompt?: () => void
        }
      }
    }
  }
}

interface GoogleSignInButtonProps {
  mode?: 'signin' | 'signup'
  onSuccess?: (user: any) => void
  onError?: (error: Error) => void
  className?: string
}

export const GoogleSignInButton: React.FC<GoogleSignInButtonProps> = ({
  mode = 'signin',
  onSuccess,
  onError,
  className = '',
}) => {
  const { loginWithGoogle } = useAuth()
  const { showToast } = useToast()
  const btnRef = useRef<HTMLDivElement>(null)
  const [isGsiLoaded, setIsGsiLoaded] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)

  const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID

  useEffect(() => {
    // Check if Google GSI script has initialized
    const checkGsi = () => {
      if (window.google?.accounts?.id) {
        setIsGsiLoaded(true)
        return true
      }
      return false
    }

    if (checkGsi()) return

    const interval = setInterval(() => {
      if (checkGsi()) {
        clearInterval(interval)
      }
    }, 200)

    const timeout = setTimeout(() => {
      clearInterval(interval)
    }, 5000)

    return () => {
      clearInterval(interval)
      clearTimeout(timeout)
    }
  }, [])

  useEffect(() => {
    if (!isGsiLoaded || !googleClientId || !btnRef.current) return

    try {
      window.google?.accounts.id.initialize({
        client_id: googleClientId,
        callback: async (response: { credential: string }) => {
          if (!response?.credential) {
            showToast('No credential returned from Google', 'error')
            return
          }
          setIsProcessing(true)
          try {
            const user = await loginWithGoogle(response.credential)
            if (onSuccess) {
              onSuccess(user)
            }
          } catch (err: any) {
            if (onError) {
              onError(err)
            }
          } finally {
            setIsProcessing(false)
          }
        },
      })

      // Clear previous buttons if re-rendering
      if (btnRef.current) {
        btnRef.current.innerHTML = ''
        window.google?.accounts.id.renderButton(btnRef.current, {
          theme: 'outline',
          size: 'large',
          text: mode === 'signup' ? 'signup_with' : 'continue_with',
          shape: 'rectangular',
          logo_alignment: 'left',
          width: 320,
        })
      }
    } catch (e) {
      console.error('[ClinicCare] Google Identity Services error:', e)
    }
  }, [isGsiLoaded, googleClientId, mode])

  return (
    <div className={`w-full flex flex-col items-center justify-center ${className}`}>
      {googleClientId ? (
        <div className="min-h-[44px] flex items-center justify-center">
          {isProcessing ? (
            <div className="flex items-center gap-2 py-2 px-4 rounded-xl border border-slate-200 bg-slate-50 text-xs font-medium text-slate-600 animate-pulse">
              <svg className="w-4 h-4 animate-spin text-sky-600" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              Authenticating with Google...
            </div>
          ) : (
            <div ref={btnRef} id={`google-btn-${mode}`} className="flex justify-center" />
          )}
        </div>
      ) : (
        <button
          type="button"
          onClick={() => {
            showToast(
              'Google Sign-In is configured on backend. Set VITE_GOOGLE_CLIENT_ID on frontend to activate Google button.',
              'info'
            )
          }}
          className="w-full max-w-[320px] inline-flex items-center justify-center gap-3 py-2.5 px-4 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-xs font-semibold shadow-sm transition hover:shadow"
        >
          <svg className="w-4 h-4" viewBox="0 0 24 24">
            <path
              fill="#4285F4"
              d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
            />
            <path
              fill="#34A853"
              d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
            />
            <path
              fill="#FBBC05"
              d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
            />
            <path
              fill="#EA4335"
              d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
            />
          </svg>
          {mode === 'signup' ? 'Continue with Google' : 'Sign in with Google'}
        </button>
      )}
    </div>
  )
}
