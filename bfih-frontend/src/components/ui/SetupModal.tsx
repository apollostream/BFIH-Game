import { useState } from 'react';
import { Modal } from './Modal';
import { cn } from '../../utils';
import { runSetup } from '../../api';

interface SetupModalProps {
  isOpen: boolean;
  onComplete: () => void;
}

export function SetupModal({ isOpen, onComplete }: SetupModalProps) {
  const [apiKey, setApiKey] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [step, setStep] = useState<'input' | 'processing' | 'success'>('input');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!apiKey.trim()) {
      setError('Please enter your API key');
      return;
    }

    if (!apiKey.startsWith('sk-')) {
      setError('Invalid API key format. OpenAI API keys start with "sk-"');
      return;
    }

    if (!displayName.trim()) {
      setError('Please enter a display name');
      return;
    }

    // Validate display name (alphanumeric, underscores, hyphens, 3-20 chars)
    const nameRegex = /^[a-zA-Z0-9_-]{3,20}$/;
    if (!nameRegex.test(displayName.trim())) {
      setError('Display name must be 3-20 characters (letters, numbers, underscores, hyphens)');
      return;
    }

    setIsLoading(true);
    setStep('processing');

    try {
      const response = await runSetup(apiKey.trim(), displayName.trim());

      if (response.error) {
        setError(response.error);
        setStep('input');
      } else if (response.data?.success) {
        setStep('success');
        // Wait a moment to show success, then close
        setTimeout(() => {
          onComplete();
        }, 1500);
      }
    } catch (err) {
      setError('An unexpected error occurred. Please try again.');
      setStep('input');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={() => {}} // Prevent closing without setup
      title="Welcome to BFIH"
      description="One-time setup required"
      size="md"
      showCloseButton={false}
      closeOnBackdrop={false}
      closeOnEscape={false}
    >
      {step === 'input' && (
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-4">
            <p className="text-text-secondary">
              To use the BFIH Hypothesis Tournament, you need an OpenAI API key.
              Your key is stored locally in your browser and used to access OpenAI's AI services.
            </p>

            <div className="p-4 bg-surface-2 rounded-lg border border-border">
              <h4 className="font-medium text-text-primary mb-2">How to get an API key:</h4>
              <ol className="list-decimal list-inside text-sm text-text-secondary space-y-1">
                <li>Go to <a href="https://platform.openai.com/api-keys" target="_blank" rel="noopener noreferrer" className="text-accent hover:underline">platform.openai.com/api-keys</a></li>
                <li>Sign in or create an account</li>
                <li>Click "Create new secret key"</li>
                <li>Copy the key and paste it below</li>
              </ol>
            </div>

            <div>
              <label htmlFor="displayName" className="block text-sm font-medium text-text-primary mb-2">
                Display Name
              </label>
              <input
                type="text"
                id="displayName"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                placeholder="your_name"
                autoComplete="off"
                className={cn(
                  'w-full px-4 py-3 rounded-lg',
                  'bg-surface-0 border border-border',
                  'text-text-primary placeholder:text-text-muted',
                  'focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent',
                  'text-sm'
                )}
              />
              <p className="mt-1 text-xs text-text-muted">
                This name will appear on scenarios you create (3-20 characters)
              </p>
            </div>

            <div>
              <label htmlFor="apiKey" className="block text-sm font-medium text-text-primary mb-2">
                OpenAI API Key
              </label>
              <input
                type="password"
                id="apiKey"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="sk-proj-..."
                autoComplete="off"
                className={cn(
                  'w-full px-4 py-3 rounded-lg',
                  'bg-surface-0 border border-border',
                  'text-text-primary placeholder:text-text-muted',
                  'focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent',
                  'font-mono text-sm'
                )}
              />
            </div>

            {error && (
              <p className="text-sm text-error">{error}</p>
            )}

            <div className="p-3 bg-warning/10 border border-warning/30 rounded-lg">
              <p className="text-sm text-warning">
                <strong>Note:</strong> Using this app will incur charges on your OpenAI account.
                A typical analysis costs $0.50-$2.00.
              </p>
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading || !apiKey.trim() || !displayName.trim()}
            className={cn(
              'w-full py-3 rounded-lg font-medium',
              'bg-accent text-white',
              'hover:bg-accent-hover transition-colors',
              'disabled:opacity-50 disabled:cursor-not-allowed'
            )}
          >
            Complete Setup
          </button>
        </form>
      )}

      {step === 'processing' && (
        <div className="py-8 text-center space-y-4">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-accent border-t-transparent" />
          <div className="space-y-2">
            <p className="text-lg font-medium text-text-primary">Setting up your account...</p>
            <p className="text-sm text-text-secondary">
              Creating your vector store and uploading the BFIH methodology.
              This may take up to a minute.
            </p>
          </div>
        </div>
      )}

      {step === 'success' && (
        <div className="py-8 text-center space-y-4">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-success/20">
            <svg className="w-8 h-8 text-success" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <div className="space-y-2">
            <p className="text-lg font-medium text-text-primary">Setup Complete!</p>
            <p className="text-sm text-text-secondary">
              Your BFIH environment is ready. Redirecting...
            </p>
          </div>
        </div>
      )}
    </Modal>
  );
}
