#!/usr/bin/env Rscript
# BFIH Bayesian Calculation Verification Script
# Reads analysis JSON and recomputes posteriors to verify calculations

library(jsonlite)
library(magrittr)
library(tidyverse)

# ============================================================================
# FUNCTIONS
# ============================================================================

compute_likelihood_negation <- function(priors, likelihoods){
  map2_dbl(
    .x = priors,
    .y = seq_along(priors),
    .f = \(p,i){
      sum(likelihoods[-i]*priors[-i]/(1-p))
    }
  )
}

compute_posteriors <- function(priors, joint_likelihoods) {
  # Compute posteriors via Bayes' theorem with normalization
  # P(H|E) = P(E|H) * P(H) / sum(P(E|Hi) * P(Hi))

  numerators <- joint_likelihoods * priors
  normalizing_constant <- sum(numerators)
  posteriors <- numerators / normalizing_constant
  
  return(posteriors)
}

compute_lr_woe <- function(prior, posterior) {
  # Compute Likelihood Ratio and Weight of Evidence
  # LR = Odds(H|E) / Odds(H)
  # WoE = 10 * log10(LR) in decibans

  prior_odds <- prior / (1 - prior)
  posterior_odds <- posterior / (1 - posterior)
  lr <- posterior_odds / prior_odds
  woe <- 10 * log10(lr)

  return(list(lr = lr, woe = woe))
}

# ============================================================================
# MAIN ANALYSIS
# ============================================================================

verify_analysis <- function(json_file) {
  cat("=================================================================\n")
  cat("BFIH Bayesian Calculation Verification\n")
  cat("=================================================================\n")
  cat("File:", json_file, "\n\n")

  # Read JSON (simplifyVector=FALSE keeps nested structure)
  data <- fromJSON(json_file, simplifyVector = TRUE, simplifyDataFrame = FALSE)

  # Extract components
  proposition <- data$proposition
  stored_posteriors <- data$posteriors
  scenario_config <- data$scenario_config

  priors_by_paradigm <- scenario_config$priors_by_paradigm
  evidence <- scenario_config$evidence
  clusters <- evidence$clusters
  hypotheses <- scenario_config$hypotheses
  paradigms <- scenario_config$paradigms

  cat("Proposition:", proposition, "\n\n")

  # Extract IDs - handle both data frame and list formats
  if (is.data.frame(hypotheses)) {
    h_ids <- hypotheses$id
  } else {
    h_ids <- sapply(hypotheses, function(h) h$id)
  }

  if (is.data.frame(paradigms)) {
    p_ids <- paradigms$id
  } else {
    p_ids <- sapply(paradigms, function(p) p$id)
  }

  cat("Hypotheses:", paste(h_ids, collapse=", "), "\n")
  cat("Paradigms:", paste(p_ids, collapse=", "), "\n")
  cat("Evidence Clusters:", length(clusters), "\n\n")

  # ========================================================================
  # VERIFY CALCULATIONS FOR EACH PARADIGM
  # ========================================================================

  results <- list()

  for (paradigm_id in p_ids) {
    cat("=================================================================\n")
    cat("PARADIGM:", paradigm_id, "\n")
    cat("=================================================================\n")

    # Get priors for this paradigm
    priors <- unlist(priors_by_paradigm[[paradigm_id]])
    priors <- priors[h_ids]  # Ensure correct order
    names(priors) <- h_ids

    cat("\nPriors:\n")
    print(round(priors, 4))
    cat("Sum of priors:", sum(priors), "\n")

    # Compute joint likelihoods P(E|H) = product of cluster likelihoods
    joint_likelihoods <- setNames(rep(1, length(h_ids)), h_ids)

    cat("\nCluster Likelihoods:\n")
    n_clusters <- if (is.data.frame(clusters)) nrow(clusters) else length(clusters)

    in_clusters <- list(n_clusters)
      
    for (i in seq_len(n_clusters)) {
      # Handle both data frame and list formats
      if (is.data.frame(clusters)) {
        cluster_name <- clusters$cluster_name[i]
        likelihoods_by_paradigm <- clusters$likelihoods_by_paradigm[[i]]
      } else {
        cluster <- clusters[[i]]
        cluster_name <- cluster$cluster_name
        likelihoods_by_paradigm <- cluster$likelihoods_by_paradigm
      }

      likelihoods_paradigm <- likelihoods_by_paradigm[[paradigm_id]]
      lklhd <- map_dbl(likelihoods_paradigm,\(lik_data){
        prob <- if (is.list(lik_data)) lik_data$probability else lik_data
        return(prob)
      })
      lklhd_not <- compute_likelihood_negation(priors,lklhd)

      cat("\n  Cluster", i, "(", cluster_name, "):\n")
      #print(list(cluster=cluster_name,priors=priors,likelihoods=lklhd,lklhd_not=lklhd_not))

      c_id <- sprintf("C_%d",i)
      in_clusters[[c_id]] <- matrix(
        0,nrow=length(h_ids),ncol=4,
        dimnames = list(h_ids,c("P(E|H)", "P(E|~H)", "LR", "WoE (dB)")))
      cat(sprintf("%-6s %12s %12s %12s %12s\n", "H", "P(E|H)", "P(E|~H)", "LR", "WoE (dB)"))
      cat(paste(rep("-", 56), collapse=""), "\n")
      for (h_id in h_ids) {
        if (!is.null(likelihoods_paradigm[[h_id]])) {
          # Handle nested structure
          lik_data <- likelihoods_paradigm[[h_id]]
          prob <- if (is.list(lik_data)) lik_data$probability else lik_data
          joint_likelihoods[h_id] <- joint_likelihoods[h_id] * prob
          prob_not <- lklhd_not[[h_id]]
          cat(
            sprintf("%-6s %12.4f %12.4f %12.4f %12.2f\n",
                    h_id, prob, prob_not, prob/prob_not, 10*log10(prob/prob_not))
          )
          in_clusters[[c_id]][h_id,] <- c(  prob, prob_not, prob/prob_not, 10*log10(prob/prob_not))
        }
      }
    }

    cat("\nJoint Likelihoods P(E|H) [product across clusters]:\n")
    print(format(joint_likelihoods, scientific = TRUE, digits = 4))
    
    # Compute joint_likelihoods under negation
    joint_pe_noth <- compute_likelihood_negation(priors, joint_likelihoods)

    # Compute posteriors
    computed_posteriors <- compute_posteriors(priors, joint_likelihoods)

    cat("\nComputed Posteriors:\n")
    print(round(computed_posteriors, 6))
    cat("Sum of posteriors:", sum(computed_posteriors), "\n")

    # Get stored posteriors for comparison
    stored <- unlist(stored_posteriors[[paradigm_id]])
    stored <- stored[h_ids]

    cat("\nStored Posteriors:\n")
    print(round(stored, 6))

    # Compute differences
    diff <- computed_posteriors - stored
    cat("\nDifference (Computed - Stored):\n")
    print(round(diff, 8))

    max_diff <- max(abs(diff))
    cat("\nMax absolute difference:", format(max_diff, scientific = TRUE), "\n")

    if (max_diff < 1e-6) {
      cat("✓ VERIFIED: Calculations match within tolerance\n")
    } else if (max_diff < 1e-4) {
      cat("~ CLOSE: Minor numerical differences (likely rounding)\n")
    } else {
      cat("✗ MISMATCH: Significant differences detected\n")
    }

    # Compute LR and WoE for each hypothesis
    cat("\nLikelihood Ratios and Weight of Evidence:\n")
    cat(sprintf("%-6s %12s %12s %12s %12s\n", "H", "Prior", "Posterior", "LR", "WoE (dB)"))
    cat(paste(rep("-", 56), collapse=""), "\n")

    all_lr <- seq_along(h_ids) |> set_names(h_ids)
    all_woe <- seq_along(h_ids) |> set_names(h_ids)
    for (h_id in h_ids) {
      metrics <- compute_lr_woe(priors[h_id], computed_posteriors[h_id])
      all_lr[[h_id]] <- metrics$lr
      all_woe[[h_id]] <- metrics$woe
      cat(sprintf("%-6s %12.4f %12.4f %12.4f %12.2f\n",
                  h_id, priors[h_id], computed_posteriors[h_id],
                  metrics$lr, metrics$woe))
    }

    results[[paradigm_id]] <- list(
      priors = priors,
      joint_likelihoods = joint_likelihoods,
      joint_lklhd_neg = joint_pe_noth,
      joint_lr = all_lr,
      joint_woe = all_woe,
      computed_posteriors = computed_posteriors,
      stored_posteriors = stored,
      max_diff = max_diff,
      in_clusters = in_clusters
    )

    cat("\n")
  }

  # ========================================================================
  # SUMMARY
  # ========================================================================

  cat("=================================================================\n")
  cat("SUMMARY\n")
  cat("=================================================================\n")

  all_verified <- TRUE
  for (p_id in p_ids) {
    status <- if (results[[p_id]]$max_diff < 1e-6) "✓" else if (results[[p_id]]$max_diff < 1e-4) "~" else "✗"
    cat(sprintf("%s %s: max diff = %s\n", status, p_id,
                format(results[[p_id]]$max_diff, scientific = TRUE)))
    if (results[[p_id]]$max_diff >= 1e-4) all_verified <- FALSE
  }

  cat("\n")
  if (all_verified) {
    cat("All paradigm calculations VERIFIED\n")
  } else {
    cat("Some calculations have discrepancies - review above\n")
  }

  invisible(results)
}

# ============================================================================
# RUN
# ============================================================================

# Get command line argument or use default
args <- commandArgs(trailingOnly = TRUE)
if (length(args) > 0) {
  json_file <- args[1]
} else {
  # Find most recent report JSON
  files <- list.files(pattern = "bfih_report_auto_.*\\.json$")
  if (length(files) > 0) {
    # Sort by modification time, most recent first
    file_info <- file.info(files)
    json_file <- rownames(file_info)[which.max(file_info$mtime)]
    cat("Using most recent file:", json_file, "\n\n")
  } else {
    stop("No bfih_report_auto_*.json files found. Provide path as argument.")
  }
}

results <- verify_analysis(json_file)
