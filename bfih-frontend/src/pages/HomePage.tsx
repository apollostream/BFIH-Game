import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { PageContainer } from '../components/layout/PageContainer';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Input } from '../components/ui/Input';
import { ReasoningModelSelector } from '../components/ui/ReasoningModelSelector';
import { useAnalysisStore } from '../stores';
import { pageVariants, staggerContainerVariants, cardVariants } from '../utils';

// Icons as inline SVGs for cleaner design
const IconAnalysis = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
  </svg>
);

const IconBrain = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M12 2a3 3 0 0 0-3 3v.5a3 3 0 0 0-3 3v.5a3 3 0 0 0-3 3v1a3 3 0 0 0 3 3h.5a3 3 0 0 0 3 3h1a3 3 0 0 0 3-3h.5a3 3 0 0 0 3-3v-1a3 3 0 0 0-3-3v-.5a3 3 0 0 0-3-3V5a3 3 0 0 0-3-3Z" />
  </svg>
);

const IconChart = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M3 3v18h18M7 16l4-4 4 4 5-6" />
  </svg>
);

const IconTarget = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <circle cx="12" cy="12" r="10" />
    <circle cx="12" cy="12" r="6" />
    <circle cx="12" cy="12" r="2" />
  </svg>
);

export function HomePage() {
  const navigate = useNavigate();
  const [proposition, setProposition] = useState('');
  const {
    submitNewAnalysis,
    isSubmitting,
    error,
    selectedReasoningModel,
    setReasoningModel,
  } = useAnalysisStore();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!proposition.trim()) return;

    const analysisId = await submitNewAnalysis(proposition.trim());
    if (analysisId) {
      navigate(`/analysis/${analysisId}`);
    }
  };

  const examplePropositions = [
    "The Boeing 737 MAX crashes were primarily caused by organizational failures rather than technical defects",
    "Remote work will become the dominant mode of employment by 2030",
    "Cryptocurrency will replace traditional banking within 20 years",
    "AI will achieve artificial general intelligence before 2030",
  ];

  return (
    <motion.div
      variants={pageVariants}
      initial="initial"
      animate="animate"
      exit="exit"
      className="min-h-screen"
    >
      <PageContainer className="max-w-5xl mx-auto">
        {/* Hero Section */}
        <motion.div
          className="text-center py-16 md:py-24 relative"
          variants={staggerContainerVariants}
          initial="initial"
          animate="animate"
        >
          {/* Decorative elements */}
          <div className="absolute inset-0 overflow-hidden pointer-events-none">
            <motion.div
              className="absolute top-20 left-10 w-72 h-72 bg-paradigm-k1/10 rounded-full blur-3xl"
              animate={{ scale: [1, 1.2, 1], opacity: [0.3, 0.5, 0.3] }}
              transition={{ duration: 8, repeat: Infinity }}
            />
            <motion.div
              className="absolute bottom-20 right-10 w-96 h-96 bg-paradigm-k2/10 rounded-full blur-3xl"
              animate={{ scale: [1.2, 1, 1.2], opacity: [0.3, 0.5, 0.3] }}
              transition={{ duration: 10, repeat: Infinity }}
            />
          </div>

          <motion.div variants={cardVariants} className="relative">
            <span className="inline-block px-4 py-1.5 mb-6 text-sm font-medium rounded-full glass border border-accent/30 text-accent">
              Bayesian Framework for Intellectual Honesty
            </span>
          </motion.div>

          <motion.h1
            variants={cardVariants}
            className="text-4xl md:text-6xl lg:text-7xl font-bold mb-6 leading-tight"
          >
            <span className="gradient-text">Hypothesis Tournament</span>
          </motion.h1>

          <motion.p
            variants={cardVariants}
            className="text-lg md:text-xl text-text-secondary max-w-2xl mx-auto leading-relaxed"
          >
            Rigorously test your beliefs using Bayesian reasoning. AI generates hypotheses,
            gathers real-world evidence, and computes posteriors across multiple epistemic paradigms.
          </motion.p>
        </motion.div>

        {/* Submission Form */}
        <motion.div variants={cardVariants} className="relative z-10">
          <div className="gradient-border p-[1px] rounded-2xl">
            <Card variant="elevated" className="p-8 md:p-10 rounded-2xl bg-surface-1/95">
              <form onSubmit={handleSubmit} className="space-y-6">
                <div>
                  <label className="block text-lg font-semibold text-text-primary mb-3">
                    What do you want to investigate?
                  </label>
                  <div className="relative">
                    <Input
                      value={proposition}
                      onChange={(e) => setProposition(e.target.value)}
                      placeholder="Enter a testable proposition..."
                      className="text-lg py-4 pl-5 pr-12 rounded-xl"
                      disabled={isSubmitting}
                    />
                    <div className="absolute right-4 top-1/2 -translate-y-1/2 text-text-muted">
                      <IconAnalysis />
                    </div>
                  </div>
                  <p className="mt-3 text-sm text-text-muted">
                    Example: "Climate change will cause significant economic disruption by 2050"
                  </p>
                </div>

                {/* Model Selection */}
                <div className="flex items-center justify-between">
                  <div className="text-sm text-text-secondary">
                    Advanced: Choose reasoning model for analysis depth vs. cost
                  </div>
                  <ReasoningModelSelector
                    value={selectedReasoningModel}
                    onChange={setReasoningModel}
                  />
                </div>

                {error && (
                  <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="p-4 rounded-xl bg-error/10 border border-error/30 text-error flex items-center gap-3"
                  >
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <circle cx="12" cy="12" r="10" />
                      <path d="M12 8v4m0 4h.01" />
                    </svg>
                    {error}
                  </motion.div>
                )}

                <Button
                  type="submit"
                  size="lg"
                  className="w-full py-4 text-lg font-semibold rounded-xl btn-glow"
                  loading={isSubmitting}
                  disabled={!proposition.trim() || isSubmitting}
                >
                  {isSubmitting ? 'Starting Analysis...' : 'Begin BFIH Analysis'}
                </Button>
              </form>
            </Card>
          </div>
        </motion.div>

        {/* Example Propositions */}
        <motion.div
          variants={staggerContainerVariants}
          initial="initial"
          animate="animate"
          className="mt-16"
        >
          <motion.h2
            variants={cardVariants}
            className="text-sm font-medium text-text-muted uppercase tracking-wider mb-4"
          >
            Try an example
          </motion.h2>
          <div className="grid gap-3">
            {examplePropositions.map((example, index) => (
              <motion.button
                key={index}
                variants={cardVariants}
                onClick={() => setProposition(example)}
                disabled={isSubmitting}
                className="text-left p-5 rounded-xl glass
                         border border-border hover:border-accent/50
                         transition-all duration-300 group
                         text-text-secondary hover:text-text-primary
                         disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <div className="flex items-start gap-4">
                  <span className="flex-shrink-0 w-8 h-8 rounded-lg bg-surface-3 flex items-center justify-center text-text-muted group-hover:bg-accent/20 group-hover:text-accent transition-colors">
                    {index + 1}
                  </span>
                  <span className="text-base leading-relaxed">{example}</span>
                </div>
              </motion.button>
            ))}
          </div>
        </motion.div>

        {/* How It Works */}
        <motion.div
          variants={staggerContainerVariants}
          initial="initial"
          animate="animate"
          className="mt-20 mb-16"
        >
          <motion.h2
            variants={cardVariants}
            className="text-2xl font-bold text-text-primary text-center mb-10"
          >
            How It Works
          </motion.h2>

          <div className="grid md:grid-cols-4 gap-6">
            {[
              {
                icon: <IconBrain />,
                phase: 'Phase 1-3',
                title: 'AI Setup',
                desc: 'Generates paradigms, hypotheses & priors',
                color: 'paradigm-k1',
              },
              {
                icon: <IconTarget />,
                phase: 'Phase 4',
                title: 'Place Bets',
                desc: 'Wager on your predicted outcomes',
                color: 'paradigm-k2',
              },
              {
                icon: <IconAnalysis />,
                phase: 'Phase 5',
                title: 'Evidence',
                desc: 'Review evidence & update beliefs',
                color: 'paradigm-k3',
              },
              {
                icon: <IconChart />,
                phase: 'Phase 6-8',
                title: 'Resolution',
                desc: 'Final posteriors & analysis',
                color: 'paradigm-k4',
              },
            ].map((step, index) => (
              <motion.div
                key={index}
                variants={cardVariants}
                className={`p-6 rounded-xl glass border border-${step.color}/30 hover:border-${step.color}/50 transition-all duration-300 group card-hover`}
              >
                <div className={`w-12 h-12 rounded-xl bg-${step.color}/20 flex items-center justify-center text-${step.color} mb-4 group-hover:glow-${step.color} transition-all`}>
                  {step.icon}
                </div>
                <div className={`text-sm font-medium text-${step.color} mb-1`}>
                  {step.phase}
                </div>
                <div className="text-lg font-semibold text-text-primary mb-2">
                  {step.title}
                </div>
                <div className="text-sm text-text-muted leading-relaxed">
                  {step.desc}
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Quick Links */}
        <motion.div
          variants={cardVariants}
          className="flex justify-center gap-4 pb-16"
        >
          <Button
            variant="ghost"
            onClick={() => navigate('/library')}
            className="text-text-secondary hover:text-text-primary"
          >
            Browse Scenario Library
          </Button>
        </motion.div>
      </PageContainer>
    </motion.div>
  );
}
