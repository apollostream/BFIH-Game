import { useEffect, useMemo, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import { PageContainer } from '../../components/layout/PageContainer';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { PhaseIndicator } from '../../components/game/PhaseIndicator';
import { useGameStore, useAnalysisStore } from '../../stores';
import { usePhaseNavigation } from '../../hooks';
import { pageVariants, cardVariants, formatPercent } from '../../utils';
import { generateSynopsis } from '../../api';
import type { EvidenceCluster, EvidenceItem, ClusterLikelihood } from '../../types';

// Helper to calculate Weight of Evidence in decibans
function calculateWoE(likelihood: number, prior: number): number {
  if (prior <= 0 || prior >= 1 || likelihood <= 0) return 0;
  const lr = likelihood / prior;
  if (lr <= 0) return 0;
  return 10 * Math.log10(lr);
}

export function ReportPage() {
  const { scenarioId } = useParams<{ scenarioId: string }>();
  const navigate = useNavigate();
  const { scenarioConfig, activeParadigm, setPhase } = useGameStore();
  const { currentAnalysis } = useAnalysisStore();
  const { handlePhaseClick, completedPhases, furthestPhase, isPhaseNavigable } = usePhaseNavigation();

  // Synopsis generation state
  const [synopsisLoading, setSynopsisLoading] = useState(false);
  const [synopsis, setSynopsis] = useState<string | null>(null);
  const [synopsisError, setSynopsisError] = useState<string | null>(null);
  const [showSynopsis, setShowSynopsis] = useState(false);

  useEffect(() => {
    setPhase('report');
  }, [setPhase]);

  // Handler to generate magazine synopsis
  const handleGenerateSynopsis = async () => {
    // Try to get analysis ID from currentAnalysis, or fall back to scenarioId
    const analysisId = currentAnalysis?.analysis_id || scenarioId;

    if (!analysisId) {
      setSynopsisError('No analysis ID available');
      return;
    }

    setSynopsisLoading(true);
    setSynopsisError(null);

    try {
      const result = await generateSynopsis(analysisId);
      setSynopsis(result.synopsis);
      setShowSynopsis(true);
    } catch (error) {
      setSynopsisError(error instanceof Error ? error.message : 'Failed to generate synopsis');
    } finally {
      setSynopsisLoading(false);
    }
  };

  // Determine if synopsis can be generated
  const canGenerateSynopsis = !!(currentAnalysis?.analysis_id || scenarioId);

  if (!scenarioConfig) {
    return (
      <PageContainer className="flex items-center justify-center min-h-[60vh]">
        <Card className="p-8 text-center">
          <p className="text-text-secondary mb-4">No scenario loaded</p>
          <Button onClick={() => navigate('/')}>Go Home</Button>
        </Card>
      </PageContainer>
    );
  }

  // Get evidence clusters from analysis metadata (where they actually live)
  // Fall back to scenarioConfig for backwards compatibility
  // Note: Evidence clusters can be stored in different locations depending on the scenario format
  const evidenceClusters = currentAnalysis?.metadata?.evidence_clusters
    || scenarioConfig.evidence_clusters
    || scenarioConfig.evidence?.clusters
    || [];

  // Get evidence items
  const evidenceItems = currentAnalysis?.metadata?.evidence_items
    || scenarioConfig?.evidence?.items
    || [];

  // Build priors data structure
  const priorsSource = scenarioConfig?.priors || scenarioConfig?.priors_by_paradigm;
  const priors = useMemo(() => {
    if (!priorsSource?.[activeParadigm]) return {};
    const result: Record<string, number> = {};
    for (const [hypId, prior] of Object.entries(priorsSource[activeParadigm])) {
      result[hypId] = typeof prior === 'number' ? prior : (prior as { probability: number })?.probability || 0;
    }
    return result;
  }, [priorsSource, activeParadigm]);

  // Get posteriors from analysis result
  const posteriors = useMemo(() => {
    if (currentAnalysis?.posteriors?.[activeParadigm]) {
      return currentAnalysis.posteriors[activeParadigm];
    }
    return priors;  // Fallback to priors
  }, [currentAnalysis, activeParadigm, priors]);

  // Build evidence items map for lookup
  const evidenceMap = useMemo(() => {
    const map: Record<string, EvidenceItem> = {};
    for (const item of evidenceItems) {
      map[item.evidence_id] = item;
    }
    return map;
  }, [evidenceItems]);

  // Generate the full report content including evidence clusters and Bayesian computation
  const reportContent = useMemo(() => {
    // Use backend report if available
    if (currentAnalysis?.report) return currentAnalysis.report;
    if (currentAnalysis?.full_report) return currentAnalysis.full_report;

    // Generate comprehensive fallback report
    const hypotheses = scenarioConfig.hypotheses || [];

    // Helper to get cluster items
    const getClusterItems = (cluster: EvidenceCluster): EvidenceItem[] => {
      if (cluster.items?.length) return cluster.items;
      if (cluster.evidence_ids?.length) {
        return cluster.evidence_ids.map((id) => evidenceMap[id]).filter(Boolean);
      }
      return [];
    };

    // Helper to get likelihoods for a cluster
    const getClusterLikelihoods = (cluster: EvidenceCluster): Record<string, ClusterLikelihood | number> => {
      return cluster.likelihoods_by_paradigm?.[activeParadigm] || cluster.likelihoods || {};
    };

    // Build evidence clusters section
    const evidenceClustersSection = evidenceClusters.map((cluster, idx) => {
      const items = getClusterItems(cluster);
      const itemsList = items.length > 0
        ? items.map((item) => {
            const citation = item.citation_apa ? ` — *${item.citation_apa}*` : '';
            return `- **${item.evidence_id}**: ${item.description || item.content}${citation}`;
          }).join('\n')
        : cluster.evidence_ids?.length
          ? `Evidence items: ${cluster.evidence_ids.join(', ')}`
          : 'No items specified';

      return `### Cluster ${idx + 1}: ${cluster.cluster_name}

${cluster.description || ''}

${itemsList}
`;
    }).join('\n');

    // Build Bayesian computation section with tables
    const bayesianSection = evidenceClusters.map((cluster, idx) => {
      const likelihoods = getClusterLikelihoods(cluster);

      // Build markdown table
      const tableRows = hypotheses.map((hyp) => {
        const likelihoodData = likelihoods[hyp.id];
        const prob = typeof likelihoodData === 'number'
          ? likelihoodData
          : (likelihoodData as ClusterLikelihood)?.probability ?? 0.5;
        const prior = priors[hyp.id] ?? 0.5;
        const lr = prior > 0 ? prob / prior : 1;
        const woe = calculateWoE(prob, prior);
        const woeSign = woe >= 0 ? '+' : '';

        return `| ${hyp.id} | ${hyp.name.slice(0, 40)}${hyp.name.length > 40 ? '...' : ''} | ${formatPercent(prob)} | ${formatPercent(prior)} | ${lr.toFixed(2)} | ${woeSign}${woe.toFixed(1)} |`;
      }).join('\n');

      return `### Cluster ${idx + 1}: ${cluster.cluster_name}

| Hypothesis | Description | P(E|H) | Prior | LR | WoE (db) |
|------------|-------------|--------|-------|-----|----------|
${tableRows}
`;
    }).join('\n');

    // Build posteriors summary
    const posteriorRows = hypotheses.map((hyp) => {
      const prior = priors[hyp.id] ?? 0;
      const posterior = posteriors[hyp.id] ?? prior;
      const change = posterior - prior;
      const changeSign = change >= 0 ? '+' : '';
      return `| ${hyp.id} | ${hyp.name.slice(0, 50)}${hyp.name.length > 50 ? '...' : ''} | ${formatPercent(prior)} | ${formatPercent(posterior)} | ${changeSign}${formatPercent(change)} |`;
    }).join('\n');

    // Build evidence matrix section
    const buildEvidenceMatrix = () => {
      if (evidenceClusters.length === 0) return '*No evidence clusters available*';

      // Build header row
      const clusterHeaders = evidenceClusters.map((_, i) => `C${i + 1}`).join(' | ');
      const headerRow = `| Hypothesis | ${clusterHeaders} |`;
      const separatorRow = `|------------|${evidenceClusters.map(() => '------').join('|')}|`;

      // Build data rows
      const dataRows = hypotheses.map((hyp) => {
        const woeValues = evidenceClusters.map((cluster) => {
          const likelihoods = cluster.likelihoods_by_paradigm?.[activeParadigm] || cluster.likelihoods || {};
          const likelihoodData = likelihoods[hyp.id];
          const prob = typeof likelihoodData === 'number'
            ? likelihoodData
            : (likelihoodData as ClusterLikelihood)?.probability ?? 0.5;
          const prior = priors[hyp.id] ?? 0.5;
          const woe = calculateWoE(prob, prior);
          const sign = woe >= 0 ? '+' : '';
          return `${sign}${woe.toFixed(1)}`;
        }).join(' | ');
        return `| ${hyp.id} | ${woeValues} |`;
      }).join('\n');

      const legend = evidenceClusters.map((c, i) => `C${i + 1}=${c.cluster_name}`).join(', ');
      return `${headerRow}\n${separatorRow}\n${dataRows}\n\n**Legend**: ${legend}`;
    };

    const evidenceMatrixSection = buildEvidenceMatrix();

    return `# BFIH Analysis Report

## Executive Summary

This analysis examined the proposition: "${scenarioConfig.proposition || scenarioConfig.scenario_narrative?.research_question || scenarioConfig.scenario_narrative?.title || scenarioConfig.narrative}"

### Paradigms Analyzed
${scenarioConfig.paradigms?.map((p) => `- **${p.id}**: ${p.name} — ${p.description || ''}`).join('\n') || 'No paradigms'}

### Hypotheses Evaluated
${hypotheses.map((h) => `- **${h.id}**: ${h.name}`).join('\n') || 'No hypotheses'}

---

## Methodology

The BFIH (Bayesian Framework for Intellectual Honesty) methodology was applied with the following forcing functions:

1. **Ontological Scan**: Verified coverage across 7 epistemic domains
2. **Ancestral Check**: Examined historical precedents and solutions
3. **Paradigm Inversion**: Generated inverse hypotheses for each paradigm
4. **MECE Synthesis**: Ensured hypotheses are mutually exclusive and collectively exhaustive

---

## Evidence Clusters

${evidenceClusters.length} evidence clusters were analyzed. Each cluster groups thematically related evidence items.

${evidenceClustersSection}

---

## Bayesian Computation

The following tables show the likelihood P(E|H), prior probability, likelihood ratio (LR), and Weight of Evidence (WoE) in decibans for each hypothesis under paradigm **${activeParadigm}**.

- **Positive WoE** (orange): Evidence supports the hypothesis
- **Negative WoE** (blue): Evidence refutes the hypothesis
- **WoE near 0**: Neutral evidence

${bayesianSection}

### Final Posteriors Summary

| Hypothesis | Description | Prior | Posterior | Change |
|------------|-------------|-------|-----------|--------|
${posteriorRows}

---

## Evidence Matrix

The following matrix shows the Weight of Evidence (WoE) in decibans for each hypothesis across all evidence clusters under paradigm **${activeParadigm}**.

${evidenceMatrixSection}

---

## Conclusions

The Bayesian analysis reveals how different epistemic paradigms lead to different posterior probabilities for each hypothesis. This demonstrates the fundamental insight of the BFIH framework: our conclusions are necessarily influenced by our prior assumptions and worldview.

Under the **${activeParadigm}** paradigm, the analysis shows:
${hypotheses.map((h) => {
  const post = posteriors[h.id] ?? 0;
  const prior = priors[h.id] ?? 0;
  const change = post - prior;
  if (Math.abs(change) < 0.05) return `- **${h.id}**: Remained relatively stable (${formatPercent(post)})`;
  if (change > 0) return `- **${h.id}**: Strengthened from ${formatPercent(prior)} to ${formatPercent(post)}`;
  return `- **${h.id}**: Weakened from ${formatPercent(prior)} to ${formatPercent(post)}`;
}).join('\n')}

---

*Report generated by the BFIH Hypothesis Tournament*
`;
  }, [scenarioConfig, currentAnalysis, evidenceClusters, evidenceItems, evidenceMap, priors, posteriors, activeParadigm]);

  return (
    <motion.div
      variants={pageVariants}
      initial="initial"
      animate="animate"
      exit="exit"
    >
      <PageContainer>
        {/* Phase Indicator */}
        <PhaseIndicator
          currentPhase="report"
          completedPhases={completedPhases}
          furthestPhase={furthestPhase}
          isPhaseNavigable={isPhaseNavigable}
          onPhaseClick={handlePhaseClick}
          className="mb-8"
        />

        {/* Title */}
        <motion.div variants={cardVariants} className="text-center mb-8">
          <h1 className="text-3xl font-bold text-text-primary mb-2">
            BFIH Analysis Report
          </h1>
          <p className="text-lg text-text-secondary">
            Complete methodology and findings
          </p>
        </motion.div>

        <div className="grid lg:grid-cols-4 gap-6">
          {/* Sidebar - Table of Contents */}
          <div className="lg:col-span-1">
            <motion.div variants={cardVariants} className="sticky top-24">
              <Card className="p-4">
                <h3 className="text-sm font-medium text-text-muted uppercase tracking-wide mb-3">
                  Contents
                </h3>
                <nav className="space-y-2">
                  {[
                    'Executive Summary',
                    'Methodology',
                    'Paradigms',
                    'Hypotheses',
                    'Evidence Clusters',
                    'Bayesian Computation',
                    'Evidence Matrix',
                    'Conclusions',
                  ].map((section) => (
                    <a
                      key={section}
                      href={`#${section.toLowerCase().replace(' ', '-')}`}
                      className="block text-sm text-text-secondary hover:text-accent transition-colors"
                    >
                      {section}
                    </a>
                  ))}
                </nav>
              </Card>

              {/* Quick Stats */}
              <Card className="p-4 mt-4">
                <h3 className="text-sm font-medium text-text-muted uppercase tracking-wide mb-3">
                  Analysis Stats
                </h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-text-secondary">Paradigms</span>
                    <Badge variant="secondary">
                      {scenarioConfig.paradigms?.length || 0}
                    </Badge>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-text-secondary">Hypotheses</span>
                    <Badge variant="secondary">
                      {scenarioConfig.hypotheses?.length || 0}
                    </Badge>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-text-secondary">Evidence</span>
                    <Badge variant="secondary">
                      {currentAnalysis?.metadata?.evidence_items_count
                        || evidenceClusters.reduce(
                          (sum, c) => sum + (c.items?.length || c.evidence_ids?.length || 0),
                          0
                        )
                        || 0}
                    </Badge>
                  </div>
                </div>
              </Card>

              {/* Actions */}
              <div className="mt-4 space-y-2">
                <Button
                  variant="secondary"
                  className="w-full"
                  onClick={() => {
                    const blob = new Blob([reportContent], { type: 'text/markdown' });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `bfih-report-${scenarioId}.md`;
                    a.click();
                    URL.revokeObjectURL(url);
                  }}
                >
                  Download Report
                </Button>
                <Button
                  variant="ghost"
                  className="w-full"
                  onClick={() => navigator.clipboard.writeText(reportContent)}
                >
                  Copy to Clipboard
                </Button>

                {/* Magazine Synopsis Button */}
                <div className="pt-2 border-t border-border mt-2">
                  <Button
                    variant="primary"
                    className="w-full"
                    onClick={handleGenerateSynopsis}
                    disabled={synopsisLoading || !canGenerateSynopsis}
                  >
                    {synopsisLoading ? (
                      <>
                        <motion.span
                          animate={{ rotate: 360 }}
                          transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                          className="inline-block mr-2"
                        >
                          ⏳
                        </motion.span>
                        Generating...
                      </>
                    ) : synopsis ? (
                      'View Synopsis'
                    ) : (
                      'Generate Magazine Synopsis'
                    )}
                  </Button>
                  {synopsis && !showSynopsis && (
                    <Button
                      variant="ghost"
                      className="w-full mt-1"
                      onClick={() => setShowSynopsis(true)}
                    >
                      View Synopsis
                    </Button>
                  )}
                  {synopsisError && (
                    <p className="text-xs text-error mt-1">{synopsisError}</p>
                  )}
                </div>
              </div>
            </motion.div>
          </div>

          {/* Main Report Content */}
          <div className="lg:col-span-3">
            <motion.div variants={cardVariants}>
              <Card className="p-8">
                <article className="prose prose-invert prose-lg max-w-none
                  prose-headings:text-text-primary
                  prose-p:text-text-secondary
                  prose-strong:text-text-primary
                  prose-li:text-text-secondary
                  prose-a:text-accent hover:prose-a:underline
                  prose-code:text-accent prose-code:bg-surface-2 prose-code:px-1 prose-code:rounded
                  prose-hr:border-border
                ">
                  <ReactMarkdown>{reportContent}</ReactMarkdown>
                </article>
              </Card>
            </motion.div>
          </div>
        </div>

        {/* Navigation */}
        <motion.div
          variants={cardVariants}
          className="flex justify-between items-center mt-8"
        >
          <Button
            variant="ghost"
            onClick={() => navigate(`/game/${scenarioId}/resolution`)}
          >
            Back to Resolution
          </Button>
          <Button
            size="lg"
            onClick={() => navigate(`/game/${scenarioId}/debrief`)}
          >
            Continue to Debrief
          </Button>
        </motion.div>
      </PageContainer>

      {/* Synopsis Modal */}
      <AnimatePresence>
        {showSynopsis && synopsis && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/70 backdrop-blur-sm z-40"
              onClick={() => setShowSynopsis(false)}
            />

            {/* Modal */}
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="fixed inset-4 md:inset-8 lg:inset-16 bg-surface-1 rounded-2xl z-50 overflow-hidden flex flex-col"
            >
              {/* Header */}
              <div className="flex items-center justify-between px-6 py-4 border-b border-border">
                <div>
                  <h2 className="text-xl font-bold text-text-primary">Magazine Synopsis</h2>
                  <p className="text-sm text-text-secondary">Plain-language summary of the analysis</p>
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => {
                      const blob = new Blob([synopsis], { type: 'text/markdown' });
                      const url = URL.createObjectURL(blob);
                      const a = document.createElement('a');
                      a.href = url;
                      a.download = `${scenarioId}-magazine-synopsis.md`;
                      a.click();
                      URL.revokeObjectURL(url);
                    }}
                  >
                    Download
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setShowSynopsis(false)}
                  >
                    Close
                  </Button>
                </div>
              </div>

              {/* Content */}
              <div className="flex-1 overflow-y-auto p-6">
                <article className="prose prose-invert prose-lg max-w-4xl mx-auto
                  prose-headings:text-text-primary
                  prose-p:text-text-secondary
                  prose-strong:text-text-primary
                  prose-li:text-text-secondary
                  prose-a:text-accent hover:prose-a:underline
                  prose-blockquote:border-accent prose-blockquote:text-text-secondary
                  prose-hr:border-border
                ">
                  <ReactMarkdown>{synopsis}</ReactMarkdown>
                </article>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
