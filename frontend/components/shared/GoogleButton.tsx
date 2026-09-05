"use client";

import { useEffect, useRef, useCallback } from "react";

declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize: (config: any) => void;
          renderButton: (element: HTMLElement, config: any) => void;
          prompt: () => void;
        };
      };
    };
  }
}

interface GoogleButtonProps {
  onSuccess: (credential: string) => void;
  onError?: (error: any) => void;
  text?: string;
}

export function GoogleButton({ onSuccess, onError, text = "Sign in with Google" }: GoogleButtonProps) {
  const buttonRef = useRef<HTMLDivElement>(null);
  const clientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;

  const handleCallback = useCallback(
    (response: any) => {
      if (response.credential) {
        onSuccess(response.credential);
      }
    },
    [onSuccess]
  );

  useEffect(() => {
    if (!clientId || !window.google || !buttonRef.current) return;

    window.google.accounts.id.initialize({
      client_id: clientId,
      callback: handleCallback,
    });

    window.google.accounts.id.renderButton(buttonRef.current, {
      text,
      theme: "filled_black",
      size: "large",
      width: "100%",
      shape: "rectangular",
    });
  }, [clientId, handleCallback, text]);

  if (!clientId) {
    return (
      <button disabled className="w-full h-12 rounded-md bg-secondary text-secondary-foreground opacity-50 cursor-not-allowed text-sm">
        Google OAuth not configured
      </button>
    );
  }

  return <div ref={buttonRef} className="w-full" />;
}
