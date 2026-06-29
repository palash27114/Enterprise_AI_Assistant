interface WelcomeBannerProps {
  userName: string;
  isReturning: boolean;
  onDismiss: () => void;
}

export function WelcomeBanner({ userName, isReturning, onDismiss }: WelcomeBannerProps) {
  return (
    <div className="welcome-banner">
      <div>
        <p className="welcome-banner-eyebrow">
          {isReturning ? "Welcome back" : "Welcome"}
        </p>
        <h3>
          {isReturning
            ? `Good to see you again, ${userName}!`
            : `Hi ${userName}, your workspace is ready.`}
        </h3>
        <p>
          {isReturning
            ? "Pick up a previous chat from the sidebar or start a new one below."
            : "Ask anything — I'll answer directly or fetch live data when needed."}
        </p>
      </div>
      <button type="button" className="welcome-banner-dismiss" onClick={onDismiss} aria-label="Dismiss">
        ×
      </button>
    </div>
  );
}
