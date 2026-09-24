# OpenIntel — Product Definition

## Product vision

OpenIntel is an **easy-to-use OSINT investigation application**.

The user should interact with OpenIntel as a unified application and should not need to understand the underlying OSINT engines.

OpenIntel internally orchestrates:

* Sherlock
* Maigret
* theHarvester
* SpiderFoot
* Photon
* Recon-ng

These tools are implementation details of the platform.

## Product principle

> Complexity belongs inside OpenIntel, not in the user's workflow.

The application should provide:

```text
Simple input
→ Intelligent investigation
→ Organized evidence
→ Clear relationships
→ Actionable report
```

## User workflow

The primary workflow should be:

```text
Create Investigation
→ Enter target
→ Select investigation type
→ Start
→ Monitor progress
→ Review findings
→ Explore relationships
→ Export report
```

## Target types

Initial target types:

* Username
* Email
* Domain
* URL
* IP
* Organization

## User should not need to

* know command-line syntax
* select individual OSINT engines
* configure complicated flags
* understand internal adapters
* understand database structure
* manually merge duplicate results
* manually correlate results from different tools

## Progressive disclosure

Expose advanced controls only when useful.

Default:

```text
Target
Investigation type
Start
```

Advanced:

```text
Sources
Depth
Concurrency
Timeouts
Scope
Rate limits
```

## Product priorities

1. Ease of use
2. Reliability
3. Clear evidence
4. Investigation reproducibility
5. Performance
6. Extensibility
7. Advanced customization

## Core product screens

### Dashboard

Show:

```text
Recent investigations
Active investigations
Investigation status
Entity counts
Evidence counts
```

### New Investigation

Simple form for starting an investigation.

### Investigation View

Show:

```text
Overview
Entities
Evidence
Relationships
Sources
Timeline
Activity
```

### Entity View

Show everything discovered about a single entity.

### Graph View

Visualize relationships between entities.

### Reports

Allow users to export investigation results.

## Important product rule

The application must remain usable by someone who has never used Sherlock, Maigret, SpiderFoot, Photon, Recon-ng or theHarvester.