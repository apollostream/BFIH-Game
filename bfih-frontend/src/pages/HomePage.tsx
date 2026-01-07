import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { PageContainer } from '../components/layout/PageContainer';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Input } from '../components/ui/Input';
import { useAnalysisStore } from '../stores';
import { pageVariants, staggerContainerVariants, cardVariants } from '../utils';

export function HomePage() {
  const navigate = useNavigate();
  const [proposition, setProposition] = useState('');
  const { submitNewAnalysis, isSubmitting, error } = useAnalysisStore();

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
    >
      <PageContainer className="max-w-4xl mx-auto">
        {/* Hero Section */}
        <motion.div
          className="text-center py-12"
          variants={staggerContainerVariants}
          initial="initial"
          animate="animate"
        >
          <motion.h1
            variants={cardVariants}
            className="text-5xl font-bold mb-4 bg-gradient-to-r from-paradigm-k1 via-paradigm-k2 to-paradigm-k3 bg-clip-text text-transparent"
          >
            BFIH Hypothesis Tournament
          </motion.h1>
          <motion.p
            variants={cardVariants}
            className="text-xl text-text-secondary max-w-2xl mx-auto"
          >
            Rigorously test your beliefs using Bayesian reasoning. Submit a proposition
            and watch as AI generates hypotheses, gathers evidence, and computes posteriors.
          </motion.p>
        </motion.div>

        {/* Submission Form */}
        <motion.div variants={cardVariants}>
          <Card variant="elevated" className="p-8">
            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label className="block text-lg font-medium text-text-primary mb-2">
                  Enter your proposition
                </label>
                <Input
                  value={proposition}
                  onChange={(e) => setProposition(e.target.value)}
                  placeholder="e.g., 'Climate change will cause significant economic disruption by 2050'"
                  className="text-lg py-4"
                  disabled={isSubmitting}
                />
                <p className="mt-2 text-sm text-text-muted">
                  A clear, testable claim that can be analyzed from multiple perspectives
                </p>
              </div>

              {error && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="p-4 rounded-lg bg-error/10 border border-error text-error"
                >
                  {error}
                </motion.div>
              )}

              <Button
                type="submit"
                size="lg"
                className="w-full"
                loading={isSubmitting}
                disabled={!proposition.trim() || isSubmitting}
              >
                {isSubmitting ? 'Submitting Analysis...' : 'Begin Analysis'}
              </Button>
            </form>
          </Card>
        </motion.div>

        {/* Example Propositions */}
        <motion.div
          variants={staggerContainerVariants}
          initial="initial"
          animate="animate"
          className="mt-12"
        >
          <motion.h2
            variants={cardVariants}
            className="text-lg font-medium text-text-secondary mb-4"
          >
            Try an example proposition:
          </motion.h2>
          <div className="grid gap-3">
            {examplePropositions.map((example, index) => (
              <motion.button
                key={index}
                variants={cardVariants}
                onClick={() => setProposition(example)}
                className="text-left p-4 rounded-lg bg-surface-1 border border-border
                         hover:border-accent hover:bg-surface-2 transition-all duration-200
                         text-text-secondary hover:text-text-primary"
              >
                "{example}"
              </motion.button>
            ))}
          </div>
        </motion.div>

        {/* How It Works */}
        <motion.div
          variants={staggerContainerVariants}
          initial="initial"
          animate="animate"
          className="mt-16 grid md:grid-cols-4 gap-4"
        >
          {[
            { phase: '1-3', title: 'Setup', desc: 'AI generates paradigms, hypotheses, and priors' },
            { phase: '4', title: 'Bet', desc: 'Place your initial bets on hypotheses' },
            { phase: '5', title: 'Evidence', desc: 'Review evidence and update beliefs' },
            { phase: '6-8', title: 'Resolve', desc: 'See results and analyze your reasoning' },
          ].map((step, index) => (
            <motion.div
              key={index}
              variants={cardVariants}
              className="p-4 rounded-lg bg-surface-1 border border-border text-center"
            >
              <div className="text-2xl font-bold text-accent mb-2">
                Phase {step.phase}
              </div>
              <div className="font-medium text-text-primary">{step.title}</div>
              <div className="text-sm text-text-muted mt-1">{step.desc}</div>
            </motion.div>
          ))}
        </motion.div>

        {/* Quick Links */}
        <motion.div
          variants={cardVariants}
          className="mt-12 flex justify-center gap-4"
        >
          <Button
            variant="ghost"
            onClick={() => navigate('/library')}
          >
            Browse Scenario Library
          </Button>
        </motion.div>
      </PageContainer>
    </motion.div>
  );
}
