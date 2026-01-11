import { useState } from 'react';
import { motion } from 'framer-motion';
import { Modal } from './Modal';
import { cn } from '../../utils';

interface HelpModalProps {
  isOpen: boolean;
  onClose: () => void;
}

type HelpTab = 'gameplay' | 'concepts';

export function HelpModal({ isOpen, onClose }: HelpModalProps) {
  const [activeTab, setActiveTab] = useState<HelpTab>('gameplay');

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Help"
      size="full"
    >
      {/* Tab Navigation */}
      <div className="flex gap-2 mb-6 border-b border-border pb-4">
        <TabButton
          active={activeTab === 'gameplay'}
          onClick={() => setActiveTab('gameplay')}
        >
          How to Play
        </TabButton>
        <TabButton
          active={activeTab === 'concepts'}
          onClick={() => setActiveTab('concepts')}
        >
          Key Concepts
        </TabButton>
      </div>

      {/* Tab Content */}
      <motion.div
        key={activeTab}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2 }}
        className="space-y-6"
      >
        {activeTab === 'gameplay' ? <GameplayContent /> : <ConceptsContent />}
      </motion.div>
    </Modal>
  );
}

function TabButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        'px-4 py-2 rounded-lg font-medium transition-colors',
        active
          ? 'bg-accent text-white'
          : 'bg-surface-2 text-text-secondary hover:text-text-primary hover:bg-surface-3'
      )}
    >
      {children}
    </button>
  );
}

function GameplayContent() {
  return (
    <div className="space-y-8">
      <Section title="Overview">
        <p>
          BFIH Tournament is a prediction game where you compete against AI "paradigm personas"
          to see who can best predict which hypothesis will be most supported by evidence.
          Each persona represents a different worldview and bets according to their beliefs.
        </p>
      </Section>

      <Section title="Game Phases">
        <div className="space-y-4">
          <Phase
            number={1}
            name="Setup"
            description="Review the scenario, research question, and available paradigms (worldviews). The analysis begins processing in the background."
          />
          <Phase
            number={2}
            name="Hypotheses"
            description="Explore the competing hypotheses that might explain the phenomenon. Each hypothesis has a unique perspective on the question."
          />
          <Phase
            number={3}
            name="Priors"
            description="See how each paradigm assigns initial probabilities to hypotheses before seeing evidence. These reflect each worldview's starting beliefs."
          />
          <Phase
            number={4}
            name="Betting"
            description="Allocate your credits across hypotheses. The odds are set by the priors—betting on unlikely hypotheses pays more if they win!"
          />
          <Phase
            number={5}
            name="Evidence"
            description="Watch as evidence is revealed and analyzed. See how different paradigms interpret the same evidence differently."
          />
          <Phase
            number={6}
            name="Resolution"
            description="Final posteriors are calculated. The hypothesis with the highest posterior probability wins. See your ranking on the leaderboard!"
          />
          <Phase
            number={7}
            name="Report"
            description="Read the detailed analysis report with all evidence, reasoning, and conclusions."
          />
        </div>
      </Section>

      <Section title="How Betting Works">
        <div className="space-y-3">
          <p>
            You have a budget of credits to distribute across hypotheses. The payoff system
            uses "odds against" based on prior probabilities:
          </p>
          <div className="bg-surface-2 rounded-lg p-4 font-mono text-sm">
            <div className="text-text-muted mb-2">If your hypothesis wins:</div>
            <div className="text-success">Payoff = (Bet / Prior) - Bet</div>
            <div className="text-text-muted mt-3 mb-2">If your hypothesis loses:</div>
            <div className="text-error">Payoff = -Bet</div>
          </div>
          <p className="text-text-secondary">
            <strong>Example:</strong> Bet 50 credits on H1 with prior 0.2 (20%). If H1 wins:
            (50 / 0.2) - 50 = 200 credits profit. If H1 loses: -50 credits.
          </p>
          <p className="text-text-secondary">
            Lower prior = higher potential payout, but also higher risk!
          </p>
        </div>
      </Section>

      <Section title="Competing Against Paradigm Personas">
        <p className="mb-3">
          Each paradigm becomes an AI opponent that bets proportionally to its prior beliefs.
          For example, if a paradigm assigns 40% prior to H1, it will bet 40% of its budget on H1.
        </p>
        <p className="text-text-secondary">
          Your goal is to outpredict these paradigm personas by understanding how evidence
          will shift probabilities. Hover over competitors in the leaderboard to see their
          credit allocation.
        </p>
      </Section>

      <Section title="Tips for Success">
        <ul className="list-disc list-inside space-y-2 text-text-secondary">
          <li>Study the priors carefully—they determine your potential payoffs</li>
          <li>Consider which hypothesis the evidence is likely to support most</li>
          <li>Diversify your bets to reduce risk, or concentrate them for higher potential gains</li>
          <li>Learn from the paradigms: understand why each worldview has its biases</li>
          <li>Read the full report after each game to deepen your understanding</li>
        </ul>
      </Section>
    </div>
  );
}

function ConceptsContent() {
  return (
    <div className="space-y-8">
      <Section title="Bayesian Reasoning">
        <p className="mb-3">
          Bayesian inference is a method of updating beliefs based on evidence. It starts with
          prior probabilities (initial beliefs) and updates them using new evidence to produce
          posterior probabilities (updated beliefs).
        </p>
        <div className="bg-surface-2 rounded-lg p-4 font-mono text-sm text-center">
          P(H|E) = P(E|H) × P(H) / P(E)
        </div>
        <p className="text-text-secondary mt-3">
          In plain language: The probability of a hypothesis given evidence equals how likely
          the evidence is if the hypothesis is true, times the prior probability, divided by
          the overall probability of the evidence.
        </p>
      </Section>

      <Section title="Priors">
        <p>
          Prior probabilities represent beliefs <em>before</em> seeing evidence. In BFIH,
          different paradigms assign different priors based on their worldview. A techno-optimist
          might assign high priors to technology-driven hypotheses, while a traditionalist
          might favor historical patterns.
        </p>
        <p className="text-text-secondary mt-2">
          Priors must sum to 100% across all hypotheses (MECE: Mutually Exclusive,
          Collectively Exhaustive).
        </p>
      </Section>

      <Section title="Posteriors">
        <p>
          Posterior probabilities are updated beliefs <em>after</em> incorporating evidence.
          Strong evidence in favor of a hypothesis increases its posterior; contradicting
          evidence decreases it.
        </p>
        <p className="text-text-secondary mt-2">
          The "winning" hypothesis is the one with the highest posterior probability
          after all evidence is considered.
        </p>
      </Section>

      <Section title="Paradigms (Worldviews)">
        <p className="mb-3">
          A paradigm is a coherent framework for interpreting the world. Each paradigm in BFIH
          represents a different epistemic stance:
        </p>
        <ul className="list-disc list-inside space-y-2 text-text-secondary">
          <li><strong>K0 - Empiricist:</strong> Balanced, data-driven, multi-domain perspective</li>
          <li><strong>K1 - Techno-Optimist:</strong> Favors technological and innovation-driven explanations</li>
          <li><strong>K2 - Traditionalist:</strong> Emphasizes historical patterns and cultural factors</li>
          <li><strong>K3 - Skeptic:</strong> Hedges across possibilities, cautious about strong claims</li>
          <li><strong>K4 - Policy-Focused:</strong> Emphasizes institutional and regulatory factors</li>
        </ul>
        <p className="text-text-secondary mt-3">
          Understanding paradigms helps you see how the same evidence can be interpreted
          differently depending on one's worldview.
        </p>
      </Section>

      <Section title="Likelihoods">
        <p>
          Likelihood P(E|H) measures how probable the observed evidence would be <em>if</em> a
          particular hypothesis were true. This is not the same as probability of the
          hypothesis—it asks: "Given H is true, how expected is this evidence?"
        </p>
        <p className="text-text-secondary mt-3">
          <strong>Example:</strong> If H = "It rained last night" and E = "The sidewalk is wet,"
          then P(E|H) is high (wet sidewalks are very expected if it rained). But P(E|not-H)
          might also be moderate (sprinklers, car wash, etc.).
        </p>
      </Section>

      <Section title="Likelihood Ratios">
        <p className="mb-3">
          The <strong>Likelihood Ratio</strong> (LR) compares how well a hypothesis predicts
          the evidence versus all alternatives combined:
        </p>
        <div className="bg-surface-2 rounded-lg p-4 font-mono text-sm text-center mb-3">
          <div>LR = P(E|H) / P(E|¬H)</div>
        </div>
        <p className="mb-3 text-text-secondary">
          Here ¬H represents the negation of H—all alternative hypotheses. P(E|¬H) is the
          weighted average likelihood across alternatives:
        </p>
        <div className="bg-surface-2 rounded-lg p-4 font-mono text-sm text-center mb-3">
          <div>P(E|¬H) = Σ P(E|Hⱼ) × P(Hⱼ) / (1 - P(H))</div>
          <div className="text-text-muted text-xs mt-1">for all j ≠ i</div>
        </div>
        <p className="mb-3">
          Philosopher <strong>Branden Fitelson</strong> demonstrated that this likelihood ratio
          is the uniquely correct measure of evidential support. His work established that
          any good confirmation measure must satisfy certain intuitive desiderata (axioms),
          and the likelihood ratio is the only measure that satisfies them all:
        </p>
        <ul className="list-disc list-inside space-y-2 text-text-secondary">
          <li><strong>Symmetry:</strong> Evidence E supports H exactly as much as it refutes ¬H</li>
          <li><strong>Equivalence:</strong> Logically equivalent hypotheses receive equal support</li>
          <li><strong>Law of Likelihood:</strong> E supports H iff P(E|H) {">"} P(E|¬H)</li>
          <li><strong>Additivity:</strong> Independent pieces of evidence combine multiplicatively</li>
        </ul>
      </Section>

      <Section title="Weight of Evidence (WoE)">
        <p>
          Weight of Evidence converts the likelihood ratio to a logarithmic scale measured
          in <strong>decibans</strong> (dB), invented by Alan Turing during WWII codebreaking:
        </p>
        <div className="bg-surface-2 rounded-lg p-4 font-mono text-sm text-center my-3">
          WoE = 10 × log₁₀(Likelihood Ratio)
        </div>
        <p className="mb-3 text-text-secondary">
          The logarithmic scale has a key advantage: independent pieces of evidence <em>add</em> rather
          than multiply, making it intuitive to accumulate evidence across multiple observations.
        </p>
        <ul className="list-disc list-inside space-y-1 text-text-secondary">
          <li><strong>+10 dB:</strong> Evidence is 10x more likely under H₁ than H₂ (strong support)</li>
          <li><strong>+20 dB:</strong> Evidence is 100x more likely under H₁ (very strong)</li>
          <li><strong>0 dB:</strong> Evidence equally consistent with both hypotheses (neutral)</li>
          <li><strong>-10 dB:</strong> Evidence favors H₂ over H₁ (strong refutation of H₁)</li>
        </ul>
        <p className="text-text-secondary mt-3">
          Turing considered ±10 dB (10:1 odds) to be meaningful evidence, and ±20 dB (100:1)
          to be decisive. BFIH uses this scale to help you calibrate your intuitions about
          evidence strength.
        </p>
      </Section>

      <Section title="Learning from the Game">
        <p className="mb-3">
          BFIH Tournament teaches critical thinking skills:
        </p>
        <ul className="list-disc list-inside space-y-2 text-text-secondary">
          <li><strong>Recognize your biases:</strong> Compare your bets to paradigm personas to see which worldview you align with</li>
          <li><strong>Update beliefs rationally:</strong> Practice adjusting predictions based on new evidence</li>
          <li><strong>Appreciate uncertainty:</strong> Even strong evidence rarely makes a hypothesis 100% certain</li>
          <li><strong>Consider alternative explanations:</strong> Multiple hypotheses can explain the same facts</li>
          <li><strong>Distinguish evidence strength:</strong> Learn to evaluate how much weight evidence should carry</li>
        </ul>
      </Section>

      <Section title="The MECE Principle">
        <p>
          Hypotheses are designed to be <strong>Mutually Exclusive</strong> (only one can be
          true) and <strong>Collectively Exhaustive</strong> (they cover all possibilities).
          This ensures probabilities sum to 100% and forces clear thinking about alternatives.
        </p>
        <p className="text-text-secondary mt-2">
          H0 typically serves as a "catch-all" hypothesis covering explanations not explicitly
          listed, ensuring the set is truly exhaustive.
        </p>
      </Section>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h3 className="text-lg font-semibold text-text-primary mb-3">{title}</h3>
      <div className="text-text-primary">{children}</div>
    </div>
  );
}

function Phase({
  number,
  name,
  description,
}: {
  number: number;
  name: string;
  description: string;
}) {
  return (
    <div className="flex gap-4">
      <div className="w-8 h-8 rounded-full bg-accent/20 text-accent flex items-center justify-center font-bold text-sm flex-shrink-0">
        {number}
      </div>
      <div>
        <div className="font-medium text-text-primary">{name}</div>
        <div className="text-sm text-text-secondary">{description}</div>
      </div>
    </div>
  );
}
