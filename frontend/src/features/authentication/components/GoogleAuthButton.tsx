import React, { useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useGoogleLogin } from '../hooks/useAuth';
import { Button } from '@/shared/ui/Button';
import { GoogleIcon } from '@/shared/ui/GoogleIcon';

declare global {
  interface Window {
    google?: {
      accounts: {
        oauth2: {
          initTokenClient: (config: {
            client_id: string;
            scope: string;
            callback: (response: { access_token?: string; error?: string; error_description?: string }) => void;
          }) => {
            requestAccessToken: () => void;
          };
        };
      };
    };
  }
}

export interface GoogleAuthButtonProps {
  mode: 'signin' | 'signup';
  onError?: (error: string) => void;
  className?: string;
}

export const GoogleAuthButton: React.FC<GoogleAuthButtonProps> = ({
  mode,
  onError,
  className = '',
}) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { mutate: googleLogin, isPending } = useGoogleLogin();
  const tokenClientRef = useRef<{ requestAccessToken: () => void } | null>(null);

  const clientId =
    import.meta.env.VITE_GOOGLE_OAUTH_CLIENT_ID ||
    import.meta.env.VITE_OAUTH_CLIENT_ID ||
    '361966023924-7q9t65dlt4ogcs0kisal3csibp52ega0.apps.googleusercontent.com';

  const from = location.state?.from?.pathname || '/dashboard';

  useEffect(() => {
    let isMounted = true;

    const setupClient = () => {
      if (!isMounted || !window.google?.accounts?.oauth2) return;

      try {
        tokenClientRef.current = window.google.accounts.oauth2.initTokenClient({
          client_id: clientId,
          scope: 'openid email profile',
          callback: (response) => {
            if (response.error) {
              onError?.(response.error_description || 'Google authentication was cancelled.');
              return;
            }
            if (!response.access_token) {
              onError?.('No access token received from Google.');
              return;
            }

            googleLogin(response.access_token, {
              onSuccess: () => {
                navigate(from, { replace: true });
              },
              onError: (err: any) => {
                const msg =
                  err?.data?.credential ||
                  err?.data?.detail ||
                  err?.message ||
                  'Google authentication failed. Please try again.';
                onError?.(Array.isArray(msg) ? msg.join(' ') : String(msg));
              },
            });
          },
        });
      } catch (err) {
        console.warn('Failed to initialize Google OAuth2 client:', err);
      }
    };

    if (window.google?.accounts?.oauth2) {
      setupClient();
    } else {
      const existingScript = document.getElementById('google-gsi-client');
      if (existingScript) {
        existingScript.addEventListener('load', setupClient);
      } else {
        const script = document.createElement('script');
        script.id = 'google-gsi-client';
        script.src = 'https://accounts.google.com/gsi/client';
        script.async = true;
        script.defer = true;
        script.onload = setupClient;
        document.head.appendChild(script);
      }
    }

    return () => {
      isMounted = false;
    };
  }, [clientId, from, googleLogin, navigate, onError]);

  const handleClick = () => {
    if (tokenClientRef.current) {
      tokenClientRef.current.requestAccessToken();
    } else if (window.google?.accounts?.oauth2) {
      try {
        const client = window.google.accounts.oauth2.initTokenClient({
          client_id: clientId,
          scope: 'openid email profile',
          callback: (response) => {
            if (response.access_token) {
              googleLogin(response.access_token, {
                onSuccess: () => navigate(from, { replace: true }),
                onError: (err: any) => onError?.(err?.message || 'Google authentication failed.'),
              });
            }
          },
        });
        tokenClientRef.current = client;
        client.requestAccessToken();
      } catch {
        onError?.('Unable to launch Google authentication. Please check your browser popup settings.');
      }
    } else {
      onError?.('Google Sign-In is initializing. Please try again in a moment.');
    }
  };

  const buttonText = mode === 'signup' ? 'Sign up with Google' : 'Continue with Google';

  return (
    <div className={`w-full flex justify-center ${className}`}>
      <Button
        type="button"
        variant="secondary"
        size="md"
        fullWidth
        isLoading={isPending}
        disabled={isPending}
        onClick={handleClick}
        leftIcon={<GoogleIcon size={18} />}
        className="font-medium text-sm border-theme-border text-theme-text hover:bg-theme-surface-hover"
      >
        {buttonText}
      </Button>
    </div>
  );
};
