
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

# Key Features

## Workforce Management

* Worker Registration
* Attendance Tracking
* Site-wise Worker Allocation
* Daily Workforce Monitoring
* Attendance History
* Payroll Calculation Support

---

## Site Management

* Multi-Site Support
* Site Creation and Configuration
* Project Budget Tracking
* Site Progress Updates
* Site-wise Reporting

---

## Inventory Management

* Material Master Management
* Material Procurement Tracking
* Material Consumption Tracking
* Inventory Transfer Between Sites
* Site-wise Inventory Visibility
* Low Stock Alerts
* Inventory Analytics

---

## Procurement Management

* Supplier Management
* Material Purchase Records
* Material Receipt Tracking
* Procurement Reports
* Supplier-wise Purchase History

---

## Expense & Budget Management

* Site Expenses Tracking
* Budget Monitoring
* Budget Utilization Analysis
* Cost Reporting
* Budget Alert Generation

---

## AI-Powered Operations

* Telegram-Based Data Entry
* Tool Calling Workflows
* Natural Language Data Extraction
* Automated Daily Reports
* Weekly Operational Summaries
* Management Insights
* Construction Knowledge Assistance

---

## Analytics Dashboard

* Workforce Analytics
* Inventory Analytics
* Site Performance Analytics
* Budget Analytics
* Operational Reports
* Executive Summary Dashboard

---

# System Architecture

```text
Telegram Operations Layer
        │
        ▼
AI Tool Calling Agent
        │
        ▼
FastAPI Backend Services
        │
        ▼
PostgreSQL Database
        │
        ▼
Web Dashboard
        │
        ▼
Management Intelligence Assistant
```

---

# Core Modules

## Human Resource Management

* Employee Management
* Attendance Tracking
* Site Assignment Tracking
* Payroll Support

---

## Inventory & Procurement Management

* Material Management
* Inventory Transactions
* Procurement Records
* Supplier Management
* Stock Monitoring

---

## Project Management

* Site Tracking
* Budget Monitoring
* Progress Updates
* Expense Management

---

## AI Management Assistant

* Natural Language Querying
* Site Analytics
* Inventory Insights
* Report Generation
* Construction Knowledge Assistance

---

# Technology Stack

### Backend

* FastAPI
* Python

### Database

* PostgreSQL

### AI Layer

* OpenRouter
* Qwen Models
* Tool Calling Agents

### Communication Layer

* Telegram Bot API
* Telegram Webhooks

### Frontend

* React / Next.js

### Deployment

* Docker
* Cloudflare Tunnel (Development)
* Cloud Hosting (Production)

---

# Future Enhancements

* Predictive Material Forecasting
* Budget Overrun Prediction
* Construction Cost Estimation
* Automated Procurement Recommendations
* Voice-Based Site Reporting
* OCR-Based Invoice Processing
* Multi-Role Access Control
* Advanced Project Analytics
* Construction Copilot Assistant

---

# Project Status

Current Phase:

* System Architecture Designed
* Database Schema Finalized
* Telegram Integration In Progress
* AI Tool Calling Workflow Development
* Dashboard Development Planned

---

## Author

Developed as an AI-powered Construction ERP and Resource Management Platform for construction contractors to digitize workforce operations, inventory management, procurement tracking, and project execution workflows.
