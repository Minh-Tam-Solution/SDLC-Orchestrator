/**
 * SDLC Orchestrator SDK Cookbook - TypeScript Recipes.
 *
 * 5 production-ready recipes demonstrating common SDK usage patterns.
 * Each recipe is self-contained with error handling and inline comments.
 *
 * Recipes:
 *   6.  Next.js API Route Gate Check - Protect routes with gates
 *   7.  React Project Overview Hook - TanStack Query dashboard
 *   8.  Slack Notification on Gate Failure - Alert team on failures
 *   9.  Express Evidence Webhook - Re-evaluate gates on evidence accept
 *   10. Multi-Project Compliance Scanner - Scan all projects
 *
 * Prerequisites:
 *   npm install @sdlc-orchestrator/client
 *   export SDLC_BASE_URL="http://localhost:8000"
 *   export SDLC_API_KEY="sdlc_live_your_key_here"
 *
 * Reference: docs/03-integrate/03-Integration-Guides/SDK-Cookbook.md
 * Sprint 170 - Developer Experience
 */

import { SdlcClient, SdlcApiError, NotFoundError } from "@sdlc-orchestrator/client";
import type { ProjectSummary, GateStatus } from "@sdlc-orchestrator/client";

// ---------------------------------------------------------------------------
// Recipe 6: Gate Guard (standalone script)
// ---------------------------------------------------------------------------

async function recipeGateGuard(projectId: string, gateId: string): Promise<number> {
  const client = new SdlcClient();

  try {
    const result = await client.gates.evaluate({
      gateId,
      projectId,
      context: { triggered_by: "ci_pipeline" },
    });

    if (result.passed) {
      console.log(`PASS  Gate ${gateId} (score: ${result.score}/100)`);
      return 0;
    }

    console.log(`FAIL  Gate ${gateId} (score: ${result.score}/100)`);
    for (const v of result.violations) {
      console.log(`  - [${v.severity}] ${v.message}`);
      if (v.suggestion) {
        console.log(`    Fix: ${v.suggestion}`);
      }
    }
    return 1;
  } catch (e) {
    if (e instanceof NotFoundError) {
      console.error(`ERROR: Project ${projectId} or gate ${gateId} not found`);
    } else if (e instanceof SdlcApiError) {
      console.error(`ERROR: API call failed [${e.statusCode}]: ${e.message}`);
    } else {
      throw e;
    }
    return 1;
  }
}

// ---------------------------------------------------------------------------
// Recipe 8: Slack Notification on Gate Failure
// ---------------------------------------------------------------------------

async function recipeSlackNotify(
  projectId: string,
  gateId: string,
  webhookUrl: string,
): Promise<void> {
  const client = new SdlcClient();

  const result = await client.gates.evaluate({
    gateId,
    projectId,
    context: { source: "scheduled_check" },
  });

  if (result.passed) {
    console.log(`Gate ${gateId} passed (score: ${result.score}). No notification.`);
    return;
  }

  const blocks = [
    {
      type: "header",
      text: { type: "plain_text", text: `Gate ${gateId} FAILED` },
    },
    {
      type: "section",
      text: {
        type: "mrkdwn",
        text: [
          `*Project*: ${projectId}`,
          `*Score*: ${result.score}/100`,
          `*Violations*: ${result.violations.length}`,
        ].join("\n"),
      },
    },
  ];

  if (result.violations.length > 0) {
    const text = result.violations
      .slice(0, 5)
      .map((v) => `- [${v.severity}] ${v.message}`)
      .join("\n");
    blocks.push({
      type: "section",
      text: { type: "mrkdwn", text: `*Violations:*\n${text}` },
    });
  }

  const response = await fetch(webhookUrl, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ blocks }),
  });

  console.log(response.ok ? "Slack notification sent." : `Slack failed: ${response.status}`);
}

// ---------------------------------------------------------------------------
// Recipe 10: Multi-Project Compliance Scanner
// ---------------------------------------------------------------------------

interface ProjectCompliance {
  name: string;
  tier: string;
  totalGates: number;
  passedGates: number;
  failedGates: number;
  topViolations: Array<{ gate: string; severity: string; message: string }>;
}

async function recipeComplianceScan(): Promise<void> {
  const client = new SdlcClient();

  console.log("Scanning all projects for compliance...\n");

  const response = await client.projects.list({ status: "active", limit: 100 });
  const results: ProjectCompliance[] = await Promise.all(
    response.items.map(async (project: ProjectSummary): Promise<ProjectCompliance> => {
      let gates: GateStatus[] = [];
      try {
        gates = await client.gates.listGates(project.id);
      } catch {
        return {
          name: project.name,
          tier: project.tier,
          totalGates: 0,
          passedGates: 0,
          failedGates: 0,
          topViolations: [],
        };
      }

      const passed = gates.filter((g) => g.status === "passed").length;
      const failed = gates.filter((g) => g.status === "failed").length;

      const topViolations: ProjectCompliance["topViolations"] = [];
      for (const gate of gates) {
        if (gate.last_evaluation && !gate.last_evaluation.passed) {
          for (const v of gate.last_evaluation.violations.slice(0, 3)) {
            topViolations.push({
              gate: gate.gate_id,
              severity: v.severity,
              message: v.message,
            });
          }
        }
      }

      return {
        name: project.name,
        tier: project.tier,
        totalGates: gates.length,
        passedGates: passed,
        failedGates: failed,
        topViolations: topViolations.slice(0, 5),
      };
    }),
  );

  results.sort((a, b) => b.failedGates - a.failedGates);

  const atRisk = results.filter((r) => r.failedGates > 0);
  const compliant = results.filter((r) => r.failedGates === 0);

  console.log(`Total projects: ${results.length}`);
  console.log(`Fully compliant: ${compliant.length}`);
  console.log(`At risk: ${atRisk.length}\n`);

  if (atRisk.length > 0) {
    console.log("--- At-Risk Projects ---\n");
    for (const r of atRisk) {
      console.log(`${r.name} [${r.tier}] - ${r.failedGates} failed gate(s)`);
      for (const v of r.topViolations) {
        console.log(`  [${v.gate}] [${v.severity}] ${v.message}`);
      }
      console.log();
    }
  }

  // Write JSON report
  const report = {
    generated_at: new Date().toISOString(),
    total_projects: results.length,
    compliant_count: compliant.length,
    at_risk_count: atRisk.length,
    projects: results,
  };

  const fs = await import("node:fs/promises");
  await fs.writeFile("compliance-scan.json", JSON.stringify(report, null, 2));
  console.log("Full report written to compliance-scan.json");
}

// ---------------------------------------------------------------------------
// CLI Entry Point
// ---------------------------------------------------------------------------

async function main(): Promise<void> {
  const [cmd, ...args] = process.argv.slice(2);

  if (!cmd) {
    console.log("SDLC SDK Cookbook - TypeScript Recipes");
    console.log();
    console.log("Usage:");
    console.log("  npx tsx cookbook.ts gate-guard <projectId> <gateId>");
    console.log("  npx tsx cookbook.ts slack-notify <projectId> <gateId> <webhookUrl>");
    console.log("  npx tsx cookbook.ts compliance-scan");
    process.exit(0);
  }

  switch (cmd) {
    case "gate-guard":
      if (args.length !== 2) {
        console.error("Usage: gate-guard <projectId> <gateId>");
        process.exit(2);
      }
      process.exit(await recipeGateGuard(args[0], args[1]));
      break;

    case "slack-notify":
      if (args.length !== 3) {
        console.error("Usage: slack-notify <projectId> <gateId> <webhookUrl>");
        process.exit(2);
      }
      await recipeSlackNotify(args[0], args[1], args[2]);
      break;

    case "compliance-scan":
      await recipeComplianceScan();
      break;

    default:
      console.error(`Unknown command: ${cmd}`);
      process.exit(2);
  }
}

main().catch((e) => {
  console.error(
    "Fatal:",
    e instanceof SdlcApiError ? `[${e.statusCode}] ${e.message}` : e,
  );
  process.exit(1);
});
