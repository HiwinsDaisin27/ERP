
# Construction ERP & Resource Management System

## Project Overview

The Construction ERP & Resource Management System is an AI-powered, site-centric enterprise management platform designed for construction contractors to efficiently manage workforce operations, inventory movement, procurement activities, project budgets, and site-level execution from a centralized system.

The platform combines Telegram-based operational workflows, PostgreSQL-backed data management, AI-assisted data extraction through tool-calling agents, and a web-based analytics dashboard to streamline daily construction operations. The system enables supervisors and managers to record attendance, assign workers, manage material transactions, monitor project progress, track budgets, and generate operational reports without relying on traditional paper-based processes.

The platform is specifically designed for small and medium-scale construction businesses that require a practical and scalable solution for managing multiple sites while maintaining complete visibility over labour, materials, expenses, and project performance.

---

## Objective

To develop a centralized Construction ERP platform that digitizes and automates construction site operations by integrating workforce management, inventory management, procurement tracking, project budgeting, operational reporting, and AI-powered decision support.

The system aims to:

* Digitize daily construction operations.
* Centralize workforce and inventory records.
* Track site-wise material consumption and procurement.
* Automate attendance and payroll-related workflows.
* Monitor project budgets and expenses.
* Generate daily, weekly, and monthly operational reports.
* Provide management with real-time visibility across all active sites.
* Enable natural language interaction through AI-powered assistants.
* Build a historical data repository for future analytics and forecasting.

---

## Problem Statement

Small and medium-scale construction contractors frequently manage labour attendance, worker allocation, material procurement, inventory tracking, and project progress through manual registers, spreadsheets, phone calls, and messaging applications.

This approach often leads to:

* Inaccurate attendance records.
* Poor visibility across multiple construction sites.
* Untracked material consumption.
* Inefficient inventory management.
* Budget overruns.
* Delayed reporting.
* Lack of historical operational data.
* Difficulty in generating actionable business insights.

The absence of a centralized management platform limits operational efficiency and makes data-driven decision-making difficult.

This project addresses these challenges by providing an integrated Construction ERP solution that centralizes operational data, automates business workflows, and enables intelligent reporting through AI-assisted systems.

---

## User & Module Identification

The Construction ERP & Management Intelligence Platform is designed to centralize construction operations through multiple interconnected modules. Site Supervisors use the Telegram interface for operational data entry, while Contractors, Project Managers, Accountants, and Administrators access the web platform for monitoring, reporting, payroll management, and business analytics. The system also includes an AI-powered Management Assistant that enables authorized users to retrieve operational insights and reports using natural language queries.

---

## Modules list

* Workforce Management Module
* Site Management Module
* Inventory & Procurement Management Module
* Budget & Expense Management Module
* Payroll & Accounting Module
* Dashboard & Analytics Module
* AI Management Assistant Module
* Authentication & Access Control Module
  
---

## System Use Case Overview

![Actor Use Case Diagram](<img width="680" height="780" alt="erp_usecase_actors" src="https://github.com/user-attachments/assets/a45402c0-ba43-4604-96f4-e0b479b4b3db" />

<svg width="680" viewBox="0 0 680 780" xmlns="http://www.w3.org/2000/svg" font-family="ui-sans-serif, system-ui, sans-serif">
  <title>Construction ERP Use Case Diagram – Actor Overview</title>
  <desc>Use case diagram showing three actors (Field Supervisor, Manager, Admin) and their primary use cases across Telegram and Web system boundaries.</desc>

  <!-- Background -->
  <rect width="680" height="780" fill="#ffffff"/>

  <!-- ─── System boundary: Telegram ─── -->
  <rect x="140" y="30" width="400" height="320" rx="14" fill="#f8fffe" stroke="#a0aab4" stroke-width="1.2" stroke-dasharray="6 4"/>
  <text x="340" y="22" text-anchor="middle" font-size="12" fill="#6b7a8d">Telegram Bot (Operational Input Layer)</text>

  <!-- ─── System boundary: Web Platform ─── -->
  <rect x="140" y="390" width="400" height="310" rx="14" fill="#f8f9ff" stroke="#a0aab4" stroke-width="1.2" stroke-dasharray="6 4"/>
  <text x="340" y="382" text-anchor="middle" font-size="12" fill="#6b7a8d">Web Platform (Management &amp; Intelligence Layer)</text>

  <!-- ═══ USE CASES – TELEGRAM (Teal) ═══ -->
  <rect x="162" y="52" width="148" height="40" rx="20" fill="#e1f5ee" stroke="#0f6e56" stroke-width="0.8"/>
  <text x="236" y="72" text-anchor="middle" dominant-baseline="central" font-size="13" font-weight="500" fill="#085041">Add worker / site</text>

  <rect x="334" y="52" width="148" height="40" rx="20" fill="#e1f5ee" stroke="#0f6e56" stroke-width="0.8"/>
  <text x="408" y="72" text-anchor="middle" dominant-baseline="central" font-size="13" font-weight="500" fill="#085041">Record attendance</text>

  <rect x="162" y="118" width="148" height="40" rx="20" fill="#e1f5ee" stroke="#0f6e56" stroke-width="0.8"/>
  <text x="236" y="138" text-anchor="middle" dominant-baseline="central" font-size="13" font-weight="500" fill="#085041">Material receipt</text>

  <rect x="334" y="118" width="148" height="40" rx="20" fill="#e1f5ee" stroke="#0f6e56" stroke-width="0.8"/>
  <text x="408" y="138" text-anchor="middle" dominant-baseline="central" font-size="13" font-weight="500" fill="#085041">Material consumption</text>

  <rect x="162" y="184" width="148" height="40" rx="20" fill="#e1f5ee" stroke="#0f6e56" stroke-width="0.8"/>
  <text x="236" y="204" text-anchor="middle" dominant-baseline="central" font-size="13" font-weight="500" fill="#085041">Add expense</text>

  <rect x="334" y="184" width="148" height="40" rx="20" fill="#e1f5ee" stroke="#0f6e56" stroke-width="0.8"/>
  <text x="408" y="204" text-anchor="middle" dominant-baseline="central" font-size="13" font-weight="500" fill="#085041">Update site progress</text>

  <!-- AI Insertion agent (Purple) -->
  <rect x="200" y="248" width="280" height="44" rx="22" fill="#eeedfe" stroke="#534ab7" stroke-width="0.8"/>
  <text x="340" y="264" text-anchor="middle" dominant-baseline="central" font-size="13" font-weight="500" fill="#3c3489">Natural language data entry</text>
  <text x="340" y="282" text-anchor="middle" dominant-baseline="central" font-size="11" fill="#534ab7">LLM insertion agent</text>

  <!-- ═══ USE CASES – WEB (Blue) ═══ -->
  <rect x="162" y="408" width="148" height="40" rx="20" fill="#e6f1fb" stroke="#185fa5" stroke-width="0.8"/>
  <text x="236" y="428" text-anchor="middle" dominant-baseline="central" font-size="13" font-weight="500" fill="#0c447c">View dashboard</text>

  <rect x="334" y="408" width="148" height="40" rx="20" fill="#e6f1fb" stroke="#185fa5" stroke-width="0.8"/>
  <text x="408" y="428" text-anchor="middle" dominant-baseline="central" font-size="13" font-weight="500" fill="#0c447c">Monitor sites &amp; workforce</text>

  <rect x="162" y="468" width="148" height="40" rx="20" fill="#e6f1fb" stroke="#185fa5" stroke-width="0.8"/>
  <text x="236" y="488" text-anchor="middle" dominant-baseline="central" font-size="13" font-weight="500" fill="#0c447c">Inventory visibility</text>

  <rect x="334" y="468" width="148" height="40" rx="20" fill="#e6f1fb" stroke="#185fa5" stroke-width="0.8"/>
  <text x="408" y="488" text-anchor="middle" dominant-baseline="central" font-size="13" font-weight="500" fill="#0c447c">Budget utilization</text>

  <!-- AI Web assistant (Purple) -->
  <rect x="200" y="528" width="280" height="44" rx="22" fill="#eeedfe" stroke="#534ab7" stroke-width="0.8"/>
  <text x="340" y="544" text-anchor="middle" dominant-baseline="central" font-size="13" font-weight="500" fill="#3c3489">Ask intelligence assistant</text>
  <text x="340" y="562" text-anchor="middle" dominant-baseline="central" font-size="11" fill="#534ab7">Natural language analytics</text>

  <!-- Admin use cases (Coral) -->
  <rect x="162" y="592" width="148" height="40" rx="20" fill="#faece7" stroke="#993c1d" stroke-width="0.8"/>
  <text x="236" y="612" text-anchor="middle" dominant-baseline="central" font-size="13" font-weight="500" fill="#712b13">Manage payroll</text>

  <rect x="334" y="592" width="148" height="40" rx="20" fill="#faece7" stroke="#993c1d" stroke-width="0.8"/>
  <text x="408" y="612" text-anchor="middle" dominant-baseline="central" font-size="13" font-weight="500" fill="#712b13">Configure wages &amp; budgets</text>

  <rect x="248" y="650" width="184" height="40" rx="20" fill="#faece7" stroke="#993c1d" stroke-width="0.8"/>
  <text x="340" y="670" text-anchor="middle" dominant-baseline="central" font-size="13" font-weight="500" fill="#712b13">View financial reports</text>

  <!-- ═══ ACTORS ═══ -->
  <!-- Field Supervisor -->
  <circle cx="62" cy="116" r="16" fill="none" stroke="#6b7a8d" stroke-width="1.4"/>
  <text x="62" y="112" text-anchor="middle" font-size="14">👷</text>
  <line x1="62" y1="132" x2="62" y2="170" stroke="#6b7a8d" stroke-width="1.4"/>
  <line x1="42" y1="148" x2="82" y2="148" stroke="#6b7a8d" stroke-width="1.4"/>
  <line x1="62" y1="170" x2="44" y2="194" stroke="#6b7a8d" stroke-width="1.4"/>
  <line x1="62" y1="170" x2="80" y2="194" stroke="#6b7a8d" stroke-width="1.4"/>
  <text x="62" y="210" text-anchor="middle" font-size="11" fill="#6b7a8d">Field</text>
  <text x="62" y="224" text-anchor="middle" font-size="11" fill="#6b7a8d">supervisor</text>

  <!-- Manager -->
  <circle cx="618" cy="470" r="16" fill="none" stroke="#6b7a8d" stroke-width="1.4"/>
  <text x="618" y="466" text-anchor="middle" font-size="14">📊</text>
  <line x1="618" y1="486" x2="618" y2="524" stroke="#6b7a8d" stroke-width="1.4"/>
  <line x1="598" y1="502" x2="638" y2="502" stroke="#6b7a8d" stroke-width="1.4"/>
  <line x1="618" y1="524" x2="600" y2="548" stroke="#6b7a8d" stroke-width="1.4"/>
  <line x1="618" y1="524" x2="636" y2="548" stroke="#6b7a8d" stroke-width="1.4"/>
  <text x="618" y="564" text-anchor="middle" font-size="11" fill="#6b7a8d">Manager</text>

  <!-- Admin -->
  <circle cx="618" cy="616" r="16" fill="none" stroke="#6b7a8d" stroke-width="1.4"/>
  <text x="618" y="612" text-anchor="middle" font-size="14">🔐</text>
  <line x1="618" y1="632" x2="618" y2="670" stroke="#6b7a8d" stroke-width="1.4"/>
  <line x1="598" y1="648" x2="638" y2="648" stroke="#6b7a8d" stroke-width="1.4"/>
  <line x1="618" y1="670" x2="600" y2="694" stroke="#6b7a8d" stroke-width="1.4"/>
  <line x1="618" y1="670" x2="636" y2="694" stroke="#6b7a8d" stroke-width="1.4"/>
  <text x="618" y="710" text-anchor="middle" font-size="11" fill="#6b7a8d">Admin</text>

  <!-- Association lines: Supervisor → Telegram -->
  <line x1="78" y1="116" x2="162" y2="72" stroke="#c0c8d0" stroke-width="0.8"/>
  <line x1="78" y1="130" x2="162" y2="138" stroke="#c0c8d0" stroke-width="0.8"/>
  <line x1="78" y1="140" x2="162" y2="204" stroke="#c0c8d0" stroke-width="0.8"/>
  <line x1="78" y1="144" x2="334" y2="72" stroke="#c0c8d0" stroke-width="0.8"/>
  <line x1="78" y1="148" x2="334" y2="138" stroke="#c0c8d0" stroke-width="0.8"/>
  <line x1="78" y1="150" x2="334" y2="204" stroke="#c0c8d0" stroke-width="0.8"/>

  <!-- Association lines: Manager → Web -->
  <line x1="602" y1="462" x2="482" y2="428" stroke="#c0c8d0" stroke-width="0.8"/>
  <line x1="602" y1="468" x2="482" y2="488" stroke="#c0c8d0" stroke-width="0.8"/>
  <line x1="602" y1="474" x2="480" y2="550" stroke="#c0c8d0" stroke-width="0.8"/>
  <line x1="602" y1="460" x2="310" y2="428" stroke="#c0c8d0" stroke-width="0.8"/>
  <line x1="602" y1="466" x2="310" y2="488" stroke="#c0c8d0" stroke-width="0.8"/>

  <!-- Association lines: Admin → Coral -->
  <line x1="602" y1="616" x2="482" y2="612" stroke="#c0c8d0" stroke-width="0.8"/>
  <line x1="602" y1="618" x2="310" y2="612" stroke="#c0c8d0" stroke-width="0.8"/>
  <line x1="602" y1="622" x2="432" y2="670" stroke="#c0c8d0" stroke-width="0.8"/>

  <!-- Legend -->
  <rect x="60" y="740" width="12" height="12" rx="3" fill="#e1f5ee" stroke="#0f6e56" stroke-width="0.8"/>
  <text x="76" y="750" font-size="11" fill="#6b7a8d">Operational (Telegram)</text>
  <rect x="210" y="740" width="12" height="12" rx="3" fill="#e6f1fb" stroke="#185fa5" stroke-width="0.8"/>
  <text x="226" y="750" font-size="11" fill="#6b7a8d">Management (Web)</text>
  <rect x="352" y="740" width="12" height="12" rx="3" fill="#faece7" stroke="#993c1d" stroke-width="0.8"/>
  <text x="368" y="750" font-size="11" fill="#6b7a8d">Admin only</text>
  <rect x="452" y="740" width="12" height="12" rx="3" fill="#eeedfe" stroke="#534ab7" stroke-width="0.8"/>
  <text x="468" y="750" font-size="11" fill="#6b7a8d">AI layer</text>
</svg>
)
## Site-Centric Module Breakdown

![Module Breakdown](<img width="680" height="820" alt="erp_usecase_modules" src="https://github.com/user-attachments/assets/e4ad10c8-27c3-4c6b-afe4-ee95d8b5bc37" />
<svg width="680" viewBox="0 0 680 820" xmlns="http://www.w3.org/2000/svg" font-family="ui-sans-serif, system-ui, sans-serif">
  <title>Construction ERP – Site-Centric Module Breakdown</title>
  <desc>Structural use case breakdown showing the central Site entity connected to all functional modules: Worker, Attendance, Inventory, Expense, Progress, Payroll, Reports, and AI Assistant.</desc>

  <!-- Background -->
  <rect width="680" height="820" fill="#ffffff"/>

  <!-- Section labels -->
  <text x="340" y="16" text-anchor="middle" font-size="11" fill="#6b7a8d">Input modules (via Telegram)</text>
  <text x="340" y="596" text-anchor="middle" font-size="11" fill="#6b7a8d">Output &amp; intelligence modules (via Web)</text>

  <!-- ════ TOP ROW – Teal (Operational) ════ -->
  <!-- Worker Management -->
  <rect x="60" y="28" width="168" height="76" rx="10" fill="#e1f5ee" stroke="#0f6e56" stroke-width="0.8"/>
  <text x="144" y="56" text-anchor="middle" dominant-baseline="central" font-size="13" font-weight="500" fill="#085041">Worker management</text>
  <text x="144" y="74" text-anchor="middle" dominant-baseline="central" font-size="11" fill="#0f6e56">Register, assign to site</text>
  <text x="144" y="90" text-anchor="middle" dominant-baseline="central" font-size="11" fill="#0f6e56">Track roles &amp; skills</text>

  <!-- Attendance -->
  <rect x="256" y="28" width="168" height="76" rx="10" fill="#e1f5ee" stroke="#0f6e56" stroke-width="0.8"/>
  <text x="340" y="56" text-anchor="middle" dominant-baseline="central" font-size="13" font-weight="500" fill="#085041">Attendance tracking</text>
  <text x="340" y="74" text-anchor="middle" dominant-baseline="central" font-size="11" fill="#0f6e56">Daily check-in per site</text>
  <text x="340" y="90" text-anchor="middle" dominant-baseline="central" font-size="11" fill="#0f6e56">Labour hours summary</text>

  <!-- Inventory -->
  <rect x="452" y="28" width="168" height="76" rx="10" fill="#e1f5ee" stroke="#0f6e56" stroke-width="0.8"/>
  <text x="536" y="56" text-anchor="middle" dominant-baseline="central" font-size="13" font-weight="500" fill="#085041">Inventory &amp; materials</text>
  <text x="536" y="74" text-anchor="middle" dominant-baseline="central" font-size="11" fill="#0f6e56">Receipts, consumption</text>
  <text x="536" y="90" text-anchor="middle" dominant-baseline="central" font-size="11" fill="#0f6e56">Stock per site</text>

  <!-- ════ LEFT – Expense Tracking ════ -->
  <rect x="30" y="318" width="168" height="76" rx="10" fill="#e1f5ee" stroke="#0f6e56" stroke-width="0.8"/>
  <text x="114" y="344" text-anchor="middle" dominant-baseline="central" font-size="13" font-weight="500" fill="#085041">Expense tracking</text>
  <text x="114" y="362" text-anchor="middle" dominant-baseline="central" font-size="11" fill="#0f6e56">Site-level costs</text>
  <text x="114" y="378" text-anchor="middle" dominant-baseline="central" font-size="11" fill="#0f6e56">Budget vs actual</text>

  <!-- ════ RIGHT – Site Progress ════ -->
  <rect x="482" y="318" width="168" height="76" rx="10" fill="#e1f5ee" stroke="#0f6e56" stroke-width="0.8"/>
  <text x="566" y="344" text-anchor="middle" dominant-baseline="central" font-size="13" font-weight="500" fill="#085041">Site progress</text>
  <text x="566" y="362" text-anchor="middle" dominant-baseline="central" font-size="11" fill="#0f6e56">Milestone updates</text>
  <text x="566" y="378" text-anchor="middle" dominant-baseline="central" font-size="11" fill="#0f6e56">Daily reports</text>

  <!-- ════ CENTRAL SITE ENTITY – Amber ════ -->
  <rect x="256" y="348" width="168" height="60" rx="12" fill="#faeeda" stroke="#ba7517" stroke-width="1.2"/>
  <text x="340" y="370" text-anchor="middle" dominant-baseline="central" font-size="14" font-weight="500" fill="#633806">Site</text>
  <text x="340" y="390" text-anchor="middle" dominant-baseline="central" font-size="11" fill="#ba7517">Central business entity</text>

  <!-- ════ BOTTOM ROW ════ -->
  <!-- Payroll – Coral (Admin) -->
  <rect x="60" y="610" width="168" height="76" rx="10" fill="#faece7" stroke="#993c1d" stroke-width="0.8"/>
  <text x="144" y="636" text-anchor="middle" dominant-baseline="central" font-size="13" font-weight="500" fill="#712b13">Payroll &amp; wages</text>
  <text x="144" y="654" text-anchor="middle" dominant-baseline="central" font-size="11" fill="#993c1d">Generate payroll</text>
  <text x="144" y="670" text-anchor="middle" dominant-baseline="central" font-size="11" fill="#993c1d">Wage config (admin)</text>

  <!-- Reports & BI – Blue -->
  <rect x="256" y="610" width="168" height="76" rx="10" fill="#e6f1fb" stroke="#185fa5" stroke-width="0.8"/>
  <text x="340" y="636" text-anchor="middle" dominant-baseline="central" font-size="13" font-weight="500" fill="#0c447c">Reports &amp; BI</text>
  <text x="340" y="654" text-anchor="middle" dominant-baseline="central" font-size="11" fill="#185fa5">Trend analysis</text>
  <text x="340" y="670" text-anchor="middle" dominant-baseline="central" font-size="11" fill="#185fa5">Historical insights</text>

  <!-- AI Assistant – Purple -->
  <rect x="452" y="610" width="168" height="76" rx="10" fill="#eeedfe" stroke="#534ab7" stroke-width="0.8"/>
  <text x="536" y="636" text-anchor="middle" dominant-baseline="central" font-size="13" font-weight="500" fill="#3c3489">AI assistant</text>
  <text x="536" y="654" text-anchor="middle" dominant-baseline="central" font-size="11" fill="#534ab7">Natural language queries</text>
  <text x="536" y="670" text-anchor="middle" dominant-baseline="central" font-size="11" fill="#534ab7">Forecasting support</text>

  <!-- ════ INPUT CHANNEL PILLS ════ -->
  <rect x="100" y="478" width="110" height="28" rx="14" fill="#f1efe8" stroke="#888780" stroke-width="0.7"/>
  <text x="155" y="492" text-anchor="middle" dominant-baseline="central" font-size="11" fill="#5f5e5a">via Telegram bot</text>

  <rect x="470" y="478" width="110" height="28" rx="14" fill="#f1efe8" stroke="#888780" stroke-width="0.7"/>
  <text x="525" y="492" text-anchor="middle" dominant-baseline="central" font-size="11" fill="#5f5e5a">via Web dashboard</text>

  <!-- ════ CONNECTORS – Top row → Site ════ -->
  <!-- Worker → Site -->
  <path d="M144 104 L144 310 L256 378" fill="none" stroke="#b4b2a9" stroke-width="0.8" marker-end="url(#arr)"/>
  <!-- Attendance → Site -->
  <line x1="340" y1="104" x2="340" y2="348" stroke="#b4b2a9" stroke-width="0.8" marker-end="url(#arr)"/>
  <!-- Inventory → Site -->
  <path d="M536 104 L536 310 L424 378" fill="none" stroke="#b4b2a9" stroke-width="0.8" marker-end="url(#arr)"/>

  <!-- Expense → Site -->
  <line x1="198" y1="356" x2="256" y2="370" stroke="#b4b2a9" stroke-width="0.8" marker-end="url(#arr)"/>
  <!-- Site Progress → Site -->
  <line x1="482" y1="360" x2="424" y2="372" stroke="#b4b2a9" stroke-width="0.8" marker-end="url(#arr)"/>

  <!-- Site → Payroll -->
  <path d="M276 408 L144 520 L144 610" fill="none" stroke="#b4b2a9" stroke-width="0.8" marker-end="url(#arr)"/>
  <!-- Site → Reports -->
  <line x1="340" y1="408" x2="340" y2="610" stroke="#b4b2a9" stroke-width="0.8" marker-end="url(#arr)"/>
  <!-- Site → AI Assistant -->
  <path d="M404 408 L536 520 L536 610" fill="none" stroke="#b4b2a9" stroke-width="0.8" marker-end="url(#arr)"/>

  <!-- Input channel dashed lines -->
  <path d="M155 478 L280 420" fill="none" stroke="#c8c6be" stroke-width="0.7" stroke-dasharray="4 3" marker-end="url(#arr-d)"/>
  <path d="M525 478 L400 420" fill="none" stroke="#c8c6be" stroke-width="0.7" stroke-dasharray="4 3" marker-end="url(#arr-d)"/>

  <!-- Edge labels -->
  <text x="186" y="250" text-anchor="middle" font-size="10" fill="#888780">allocation</text>
  <text x="340" y="236" text-anchor="middle" font-size="10" fill="#888780">records</text>
  <text x="494" y="250" text-anchor="middle" font-size="10" fill="#888780">stock</text>
  <text x="222" y="356" text-anchor="middle" font-size="10" fill="#888780">costs</text>
  <text x="458" y="356" text-anchor="middle" font-size="10" fill="#888780">updates</text>

  <!-- ════ LEGEND ════ -->
  <rect x="60" y="740" width="12" height="12" rx="3" fill="#e1f5ee" stroke="#0f6e56" stroke-width="0.7"/>
  <text x="76" y="750" font-size="11" fill="#6b7a8d">Operational (Telegram)</text>
  <rect x="230" y="740" width="12" height="12" rx="3" fill="#faece7" stroke="#993c1d" stroke-width="0.7"/>
  <text x="246" y="750" font-size="11" fill="#6b7a8d">Admin module</text>
  <rect x="360" y="740" width="12" height="12" rx="3" fill="#e6f1fb" stroke="#185fa5" stroke-width="0.7"/>
  <text x="376" y="750" font-size="11" fill="#6b7a8d">Reporting</text>
  <rect x="456" y="740" width="12" height="12" rx="3" fill="#eeedfe" stroke="#534ab7" stroke-width="0.7"/>
  <text x="472" y="750" font-size="11" fill="#6b7a8d">AI layer</text>
  <rect x="548" y="740" width="12" height="12" rx="3" fill="#faeeda" stroke="#ba7517" stroke-width="0.7"/>
  <text x="564" y="750" font-size="11" fill="#6b7a8d">Core entity</text>

  <!-- ════ ARROWHEAD MARKERS ════ -->
  <defs>
    <marker id="arr" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M2 1L8 5L2 9" fill="none" stroke="#b4b2a9" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
    </marker>
    <marker id="arr-d" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M2 1L8 5L2 9" fill="none" stroke="#c8c6be" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
    </marker>
  </defs>
</svg>
)
